import discord
from discord import app_commands
from src.config import SUPPORT_SERVER_URL

def setup_help_commands(tree, bot, db):
    @tree.command(name="help", description="Show all available commands and information")
    async def help_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛡️ Scam Detector Bot - Help",
            description="Automatic scam image detection and moderation bot",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 Hash Management",
            value=(
                "`/get_hash` - Calculate the hash of an image\n"
                "`/add_hash` - Add a scam image hash to your server\n"
                "`/list_hashes` - View all hashes and false positives\n"
                "`/remove_hash` - Remove a hash from your server\n"
                "`/false_positive` - Mark/unmark a hash as false positive\n"
                "`/export_hashes` - Export your hashes to JSON\n"
                "`/import_hashes` - Import hashes from JSON file"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Configuration",
            value=(
                "`/set_report_channel` - Set the channel for scam reports\n"
                "`/set_action` - Configure automatic moderation action\n"
                "`/set_threshold` - Adjust detection sensitivity (0-20)\n"
                "`/toggle_global_hashes` - Enable/disable global hash database\n"
                "`/scam_stats` - View detection statistics\n"
                "`/user_reputation` - Check a user's detection history"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Available Actions",
            value=(
                "• **None** - Report only, no automatic action\n"
                "• **Delete** - Delete the message (default)\n"
                "• **Mute** - Delete message + mute user for 1 hour\n"
                "• **Kick** - Delete message + kick user\n"
                "• **Ban** - Delete message + ban user"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"Need help? Join our support server: {SUPPORT_SERVER_URL}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
