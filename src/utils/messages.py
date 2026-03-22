import discord
from src.config import SUPPORT_SERVER_URL

def get_welcome_embed(guild_name: str) -> discord.Embed:
    embed = discord.Embed(
        title="🛡️ Scam Detector Bot",
        description="Thank you for adding me to your server!",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="Setup Complete",
        value="This channel has been automatically configured for scam reports.",
        inline=False
    )
    
    embed.add_field(
        name="Next Steps",
        value=(
            "Use `/help` to see all available commands and detailed information.\n\n"
            "`/add_hash` - Add a scam image hash\n"
            "`/set_action` - Configure automatic moderation\n"
            "`/set_threshold` - Adjust detection sensitivity (default: 5)\n"
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Need help? Use /help or join: {SUPPORT_SERVER_URL}")
    
    return embed

def get_setup_required_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🛡️ Scam Detector Bot - Setup Required",
        description="I don't have permission to create channels in your server.",
        color=discord.Color.orange()
    )
    
    embed.add_field(
        name="Manual Setup Required",
        value=(
            "1. Create a text channel for scam reports\n"
            "2. Give me permission to send messages in that channel\n"
            "3. Use `/set_report_channel` to configure the bot\n"
            "4. Use `/help` for more information"
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Need help? Join: {SUPPORT_SERVER_URL}")
    
    return embed
