import discord
from discord import app_commands
import aiohttp
import json
import io
from src.core.image_hash import calculate_image_hash
from src.config import MAX_HASHES_DISPLAY, GITHUB_IMAGES_BASE_URL


def setup_hash_commands(tree, bot, db):
    async def hash_autocomplete(
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        guild_id = str(interaction.guild.id)
        server_hashes = await db.get_server_hashes(guild_id)

        matches = [
            h for h in server_hashes
            if current.lower() in h['hash'].lower()
        ][:25]

        return [
            app_commands.Choice(
                name=f"{h['hash'][:50]} - {h.get('description', 'No description')[:30]}",
                value=h['hash']
            )
            for h in matches
        ]

    async def false_positive_autocomplete(
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        guild_id = str(interaction.guild.id)

        namespace = interaction.namespace
        action = namespace.action if hasattr(namespace, 'action') else None

        if action == "add":
            server_hashes = await db.get_server_hashes(guild_id)
            matches = [
                h for h in server_hashes
                if current.lower() in h['hash'].lower()
            ][:25]

            return [
                app_commands.Choice(
                    name=f"{h['hash'][:50]} - {h.get('description', 'No description')[:30]}",
                    value=h['hash']
                )
                for h in matches
            ]
        elif action == "remove":
            false_positives = await db.get_false_positives(guild_id)
            matches = [
                fp for fp in false_positives
                if current.lower() in fp['hash'].lower()
            ][:25]

            return [
                app_commands.Choice(name=fp['hash'][:100], value=fp['hash'])
                for fp in matches
            ]
        else:
            return []

    @tree.command(name="add_hash", description="Add a scam image hash for this server")
    @app_commands.describe(
        image_url="Image URL",
        description="Optional description"
    )
    @app_commands.default_permissions(administrator=True)
    async def add_hash(interaction: discord.Interaction, image_url: str, description: str = None):
        await interaction.response.defer(ephemeral=True)

        try:
            async with bot.session.get(image_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ Unable to download image.")
                    return

                image_bytes = await resp.read()
                image_hash = calculate_image_hash(image_bytes)

                guild_id = str(interaction.guild.id)
                success = await db.add_server_hash(guild_id, image_hash, description)

                if success:
                    msg = f"✅ Hash added to this server's database!\nHash: `{image_hash}`"
                    if description:
                        msg += f"\nDescription: {description}"
                    await interaction.followup.send(msg)
                else:
                    await interaction.followup.send("❌ This hash already exists for this server.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")
    
    @tree.command(name="get_hash", description="Calculate the hash of an image")
    @app_commands.describe(image_url="Image URL to calculate hash from")
    @app_commands.default_permissions(administrator=True)
    async def get_hash(interaction: discord.Interaction, image_url: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with bot.session.get(image_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ Unable to download image.")
                    return
                
                image_bytes = await resp.read()
                image_hash = calculate_image_hash(image_bytes)
                
                embed = discord.Embed(
                    title="🔍 Image Hash",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name=f"`{image_hash}`",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")

    @tree.command(name="list_hashes", description="List all hashes and false positives for this server")
    @app_commands.default_permissions(administrator=True)
    async def list_hashes(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        server_hashes = await db.get_server_hashes(guild_id)
        false_positives = await db.get_false_positives(guild_id)
        
        global_hashes = db.get_global_hashes()
        global_hash_dict = {h['hash']: h for h in global_hashes}

        fp_hashes = {fp['hash'] for fp in false_positives}
        active_hashes = [
            h for h in server_hashes if h['hash'] not in fp_hashes]

        if not active_hashes and not false_positives:
            await interaction.followup.send("❌ No hashes or false positives registered for this server.")
            return

        embed = discord.Embed(
            title=f"📋 Hash Management - {interaction.guild.name}",
            color=discord.Color.blue()
        )

        if active_hashes:
            hash_list = []
            for i, item in enumerate(active_hashes[:MAX_HASHES_DISPLAY], 1):
                desc = item.get('description', 'No description')
                hash_value = item['hash']
                
                if hash_value in global_hash_dict and GITHUB_IMAGES_BASE_URL:
                    global_item = global_hash_dict[hash_value]
                    image_path = global_item.get('image_path', '')
                    if image_path:
                        image_url = GITHUB_IMAGES_BASE_URL + image_path
                        hash_list.append(f"[`{hash_value}`]({image_url}) 🌐\n└ {desc}")
                    else:
                        hash_list.append(f"`{hash_value}` 🌐\n└ {desc}")
                else:
                    hash_list.append(f"`{hash_value}`\n└ {desc}")

            embed.add_field(
                name=f"🚨 Active Scam Hashes ({len(active_hashes)})",
                value="\n\n".join(hash_list) if hash_list else "None",
                inline=False
            )

            if len(active_hashes) > MAX_HASHES_DISPLAY:
                embed.add_field(
                    name="",
                    value=f"_Showing {MAX_HASHES_DISPLAY}/{len(active_hashes)} active hashes_",
                    inline=False
                )

        if false_positives:
            fp_list = []
            for i, item in enumerate(false_positives[:MAX_HASHES_DISPLAY], 1):
                hash_value = item['hash']
                
                if hash_value in global_hash_dict and GITHUB_IMAGES_BASE_URL:
                    global_item = global_hash_dict[hash_value]
                    image_path = global_item.get('image_path', '')
                    if image_path:
                        image_url = GITHUB_IMAGES_BASE_URL + image_path
                        fp_list.append(f"[`{hash_value}`]({image_url}) 🌐")
                    else:
                        fp_list.append(f"`{hash_value}` 🌐")
                else:
                    fp_list.append(f"`{hash_value}`")

            embed.add_field(
                name=f"✅ False Positives ({len(false_positives)})",
                value="\n".join(fp_list) if fp_list else "None",
                inline=False
            )

            if len(false_positives) > MAX_HASHES_DISPLAY:
                embed.add_field(
                    name="",
                    value=f"_Showing {MAX_HASHES_DISPLAY}/{len(false_positives)} false positives_",
                    inline=False
                )
        
        embed.set_footer(text="🌐 = Global hash (click to view image)")

        await interaction.followup.send(embed=embed)

    @tree.command(name="remove_hash", description="Remove a hash from this server")
    @app_commands.describe(hash_value="The hash to remove")
    @app_commands.autocomplete(hash_value=hash_autocomplete)
    @app_commands.default_permissions(administrator=True)
    async def remove_hash(interaction: discord.Interaction, hash_value: str):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        success = await db.delete_server_hash(guild_id, hash_value)

        if success:
            await interaction.followup.send(f"✅ Hash `{hash_value}` removed.")
        else:
            await interaction.followup.send("❌ Hash not found.")

    @tree.command(name="export_hashes", description="Export server hashes to JSON")
    @app_commands.default_permissions(administrator=True)
    async def export_hashes(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild_id = str(interaction.guild.id)
        data = await db.export_hashes(guild_id)

        json_data = json.dumps(data, indent=2)
        file = discord.File(
            fp=io.BytesIO(json_data.encode()),
            filename=f"hashes_{guild_id}.json"
        )

        await interaction.followup.send(
            "✅ Hashes exported successfully!",
            file=file,
            ephemeral=True
        )

    @tree.command(name="import_hashes", description="Import hashes from JSON file")
    @app_commands.describe(file="JSON file containing hashes")
    @app_commands.default_permissions(administrator=True)
    async def import_hashes(interaction: discord.Interaction, file: discord.Attachment):
        await interaction.response.defer(ephemeral=True)

        if not file.filename.endswith('.json'):
            await interaction.followup.send("❌ File must be a JSON file.")
            return

        try:
            content = await file.read()
            data = json.loads(content.decode())

            guild_id = str(interaction.guild.id)
            result = await db.import_hashes(guild_id, data)

            await interaction.followup.send(
                f"✅ Import complete!\n"
                f"Added: {result['added']}\n"
                f"Skipped (duplicates): {result['skipped']}"
            )
        except json.JSONDecodeError:
            await interaction.followup.send("❌ Invalid JSON file.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")

    @tree.command(name="false_positive", description="Manage false positives")
    @app_commands.describe(
        action="Add or remove a false positive",
        hash_value="The hash to add/remove"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Add", value="add"),
        app_commands.Choice(name="Remove", value="remove")
    ])
    @app_commands.autocomplete(hash_value=false_positive_autocomplete)
    @app_commands.default_permissions(administrator=True)
    async def false_positive(interaction: discord.Interaction, action: app_commands.Choice[str], hash_value: str):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)

        if action.value == "add":
            success = await db.add_false_positive(guild_id, hash_value, str(interaction.user.id))
            if success:
                await interaction.followup.send(f"✅ Hash `{hash_value}` marked as false positive.")
            else:
                await interaction.followup.send("❌ This hash is already marked as a false positive.")
        else:
            success = await db.remove_false_positive(guild_id, hash_value)
            if success:
                await interaction.followup.send(f"✅ Hash `{hash_value}` removed from false positives.")
            else:
                await interaction.followup.send("❌ Hash not found in false positives.")
