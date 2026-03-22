import discord
from discord import app_commands
from src.config import TOP_HASHES_LIMIT, SUPPORT_SERVER_URL

def setup_config_commands(tree, bot, db):
    @tree.command(name="set_report_channel", description="Set the channel for reports")
    @app_commands.describe(channel="The channel where reports will be sent")
    @app_commands.default_permissions(administrator=True)
    async def set_report_channel(interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        await db.set_report_channel(guild_id, str(channel.id))
        await interaction.followup.send(f"✅ Report channel set to: {channel.mention}")
    
    @tree.command(name="set_action", description="Set the automatic action on detection")
    @app_commands.describe(action="Action to perform automatically")
    @app_commands.choices(action=[
        app_commands.Choice(name="No action (report only)", value="none"),
        app_commands.Choice(name="Delete message only (default)", value="delete"),
        app_commands.Choice(name="Delete + Mute (1h)", value="mute"),
        app_commands.Choice(name="Delete + Kick", value="kick"),
        app_commands.Choice(name="Delete + Ban", value="ban")
    ])
    @app_commands.default_permissions(administrator=True)
    async def set_action(interaction: discord.Interaction, action: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        await db.set_default_action(guild_id, action.value)
        await interaction.followup.send(f"✅ Automatic action set to: **{action.name}**")
    
    @tree.command(name="set_threshold", description="Set the tolerance threshold for hash comparison")
    @app_commands.describe(threshold="Threshold (0-20, recommended: 5)")
    @app_commands.default_permissions(administrator=True)
    async def set_threshold(interaction: discord.Interaction, threshold: int):
        await interaction.response.defer(ephemeral=True)
        if threshold < 0 or threshold > 20:
            await interaction.followup.send("❌ Threshold must be between 0 and 20.")
            return
        
        guild_id = str(interaction.guild.id)
        await db.set_hash_threshold(guild_id, threshold)
        await interaction.followup.send(f"✅ Threshold set to: **{threshold}**")
    
    @tree.command(name="toggle_global_hashes", description="Enable or disable global hash database")
    @app_commands.describe(enabled="Enable or disable global hashes")
    @app_commands.choices(enabled=[
        app_commands.Choice(name="Enabled", value="true"),
        app_commands.Choice(name="Disabled", value="false")
    ])
    @app_commands.default_permissions(administrator=True)
    async def toggle_global_hashes(interaction: discord.Interaction, enabled: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        use_global = enabled.value == "true"
        
        await db.set_use_global_hashes(guild_id, use_global)
        
        status = "enabled" if use_global else "disabled"
        await interaction.followup.send(
            f"✅ Global hash database **{status}** for this server.\n"
            f"{'The bot will now use both global and server-specific hashes.' if use_global else 'The bot will now only use server-specific hashes.'}"
        )
    
    @tree.command(name="hashes_stats", description="Show hashes detection statistics")
    @app_commands.default_permissions(administrator=True)
    async def scam_stats(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        stats = await db.get_stats(guild_id)
        server_config = await db.get_server_config(guild_id)
        detection_stats = await db.get_detection_stats(guild_id)
        
        embed = discord.Embed(
            title="📊 Hashes Statistics",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Global Hashes", value=f"{stats['global_count']}", inline=True)
        embed.add_field(name="Server Hashes", value=f"{stats['server_count']}", inline=True)
        embed.add_field(name="Total Hashes", value=f"{stats['total']}", inline=True)
        
        embed.add_field(name="Total Detections", value=f"{detection_stats['total_detections']}", inline=True)
        
        if server_config:
            embed.add_field(name="Current Threshold", value=f"{server_config['hash_threshold']}", inline=True)
            embed.add_field(name="Auto Action", value=f"{server_config['default_action']}", inline=True)
            
            global_status = "✅ Enabled" if server_config.get('use_global_hashes', 1) == 1 else "❌ Disabled"
            embed.add_field(name="Global Hashes", value=global_status, inline=True)
            
            if server_config['report_channel_id']:
                channel = bot.get_channel(int(server_config['report_channel_id']))
                if channel:
                    embed.add_field(name="Report Channel", value=channel.mention, inline=True)
        
        if detection_stats['top_hashes']:
            top_list = "\n".join([
                f"`{h['hash']}` - {h['count']} detections"
                for h in detection_stats['top_hashes'][:TOP_HASHES_LIMIT]
            ])
            embed.add_field(name="Top Detected Hashes", value=top_list, inline=False)
        
        embed.set_footer(text=f"Support: {SUPPORT_SERVER_URL}")
        
        await interaction.followup.send(embed=embed)
    
    @tree.command(name="user_reputation", description="Check a user's reputation")
    @app_commands.describe(user="The user to check")
    @app_commands.default_permissions(administrator=True)
    async def user_reputation(interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        
        reputation = await db.get_user_reputation(guild_id, user_id)
        
        if not reputation:
            await interaction.followup.send(f"✅ {user.mention} has no scam detections.")
            return
        
        embed = discord.Embed(
            title=f"User Reputation - {user.name}",
            color=discord.Color.orange() if reputation['detection_count'] >= 2 else discord.Color.blue()
        )
        
        embed.add_field(name="Detection Count", value=f"{reputation['detection_count']}", inline=True)
        embed.add_field(name="Last Detection", value=f"{reputation['last_detection']}", inline=True)
        
        if reputation['detection_count'] >= 3:
            embed.add_field(
                name="⚠️ Warning",
                value="This user has multiple scam detections!",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
