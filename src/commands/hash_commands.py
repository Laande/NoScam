import discord
from discord import app_commands
import aiohttp
import json
import io
from src.core.image_hash import calculate_image_hash
from src.config import MAX_HASHES_DISPLAY, GITHUB_IMAGES_BASE_URL
from src.utils.pagination import EmbedPaginator, create_hash_embeds


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
        await interaction.response.defer()

        try:
            async with bot.session.get(image_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ Unable to download image.", ephemeral=True)
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
                    await interaction.followup.send("❌ This hash already exists for this server.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

    @tree.command(name="get_hash", description="Calculate the hash of an image")
    @app_commands.describe(image_url="Image URL to calculate hash from")
    @app_commands.default_permissions(moderate_members=True)
    async def get_hash(interaction: discord.Interaction, image_url: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with bot.session.get(image_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ Unable to download image.", ephemeral=True)
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
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

    def format_embed(item, global_hash_dict):
            desc = item.get('description', '')
            hash_value = item['hash']

            if hash_value in global_hash_dict and GITHUB_IMAGES_BASE_URL:
                global_item = global_hash_dict[hash_value]
                image_path = global_item.get('image_path', '')
                if image_path:
                    image_url = GITHUB_IMAGES_BASE_URL + image_path
                    return f"[`{hash_value}`]({image_url}) 🌐{f'\n└ {desc}' if desc else ''}"
                else:
                    return f"`{hash_value}` 🌐{f'\n└ {desc}' if desc else ''}"
            else:
                return f"`{hash_value}`{f'\n└ {desc}' if desc else ''}"

    @tree.command(name="list_hashes", description="List hashes for this server")
    @app_commands.describe(type="What to display (defaults to active hashes)")
    @app_commands.choices(type=[
        app_commands.Choice(name="Active Hashes Only", value="active"),
        app_commands.Choice(name="False Positives Only", value="false_positives")
    ])
    @app_commands.default_permissions(moderate_members=True)
    async def list_hashes(interaction: discord.Interaction, type: str = "active"):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        
        server_config = await db.get_server_config(guild_id)
        use_global = server_config.get('use_global_hashes', 1) == 1 if server_config else True
        
        all_hashes = await db.get_all_hashes(guild_id)
        false_positives = await db.get_false_positives(guild_id)
        
        global_hashes = db.get_global_hashes()
        global_hash_dict = {h['hash']: h for h in global_hashes}

        if not all_hashes and not false_positives:
            status = "enabled" if use_global else "disabled"
            await interaction.followup.send(f"❌ No hashes registered for this server.\n_Global hashes are {status}_")
            return

        embed = []
        if all_hashes and type == "active":
            embed = create_hash_embeds(
                title="🚨 Active Scam Hashes",
                items=all_hashes[:MAX_HASHES_DISPLAY],
                global_hash=global_hash_dict,
                items_per_page=8,
                description_func=format_embed,
                color=discord.Color.red()
            )

        elif false_positives and type == "false_positives":
            embed = create_hash_embeds(
                title="✅ False Positives",
                items=false_positives[:MAX_HASHES_DISPLAY],
                global_hash=global_hash_dict,
                items_per_page=8,
                description_func=format_embed,
                color=discord.Color.green()
            )

        else:
            embed = discord.Embed(
                description="No hashes to display.",
                color=discord.Color.blue()
                return await interaction.followup.send(embed=embed)
            )
        
        if len(embed) == 1:
            await interaction.followup.send(embed=embed[0])
        else:
            paginator = EmbedPaginator(embed)
            view = paginator.get_view()

            view.previous_button.disabled = not paginator.has_previous()
            view.next_button.disabled = not paginator.has_next()

            await interaction.followup.send(embed=paginator.get_current_embed(), view=view)

    @tree.command(name="remove_hash", description="Remove a hash from this server")
    @app_commands.describe(hash_value="The hash to remove")
    @app_commands.autocomplete(hash_value=hash_autocomplete)
    @app_commands.default_permissions(administrator=True)
    async def remove_hash(interaction: discord.Interaction, hash_value: str):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)
        success = await db.delete_server_hash(guild_id, hash_value)

        if success:
            await interaction.followup.send(f"✅ Hash `{hash_value}` removed.")
        else:
            await interaction.followup.send("❌ Hash not found.", ephemeral=True)

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
            await interaction.followup.send("❌ File must be a JSON file.", ephemeral=True)
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
            await interaction.followup.send("❌ Invalid JSON file.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

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
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)

        if action.value == "add":
            success = await db.add_false_positive(guild_id, hash_value, str(interaction.user.id))
            if success:
                await interaction.followup.send(f"✅ Hash `{hash_value}` marked as false positive.")
            else:
                await interaction.followup.send("❌ This hash is already marked as a false positive.", ephemeral=True)
        else:
            success = await db.remove_false_positive(guild_id, hash_value)
            if success:
                await interaction.followup.send(f"✅ Hash `{hash_value}` removed from false positives.")
            else:
                await interaction.followup.send("❌ Hash not found in false positives.", ephemeral=True)
