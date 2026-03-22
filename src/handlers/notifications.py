import discord
from src.config import DISCORD_SUPPORT_URL, SUPPORT_SERVER_URL
from src.handlers.views import ActionButtons

async def send_user_warning(message, action, guild_name):
    try:
        warning_embed = discord.Embed(
            title="⚠️ Scam Image Detected",
            description="Your message contained an image flagged as a potential scam.",
            color=discord.Color.red()
        )
        warning_embed.add_field(
            name="Server",
            value=f"{guild_name}",
            inline=False
        )
        warning_embed.add_field(
            name="Action Taken",
            value=f"Your message has been {'deleted' if action != 'none' else 'reported to moderators'}.",
            inline=False
        )
        if action in ['mute', 'kick', 'ban']:
            warning_embed.add_field(
                name="Additional Action",
                value=f"You have been {action}ed from the server.",
                inline=False
            )
        
        warning_embed.add_field(
            name="⚠️ Account Compromised?",
            value=(
                f"If you didn't send this image, your account may be compromised.\n"
                f"[Click here to secure your account]({DISCORD_SUPPORT_URL})"
            ),
            inline=False
        )
        
        await message.author.send(embed=warning_embed)
    except discord.Forbidden:
        pass

async def send_scam_report(bot, db, message, match, distance, image_file, message_content, message_jump_url):
    guild_id = str(message.guild.id)
    server_config = await db.get_server_config(guild_id)
    
    if not server_config or not server_config['report_channel_id']:
        return
    
    report_channel = bot.get_channel(int(server_config['report_channel_id']))
    if not report_channel:
        return
    
    is_fp = await db.is_false_positive(guild_id, match['hash'])
    
    embed = discord.Embed(
        title="🚨 Scam Image Detected",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )
    
    embed.add_field(name="User", value=f"{message.author.mention} ({message.author.id})", inline=False)
    embed.add_field(name="Channel", value=message.channel.mention, inline=True)
    embed.add_field(name="Hash Distance", value=f"{distance}", inline=True)
    
    reputation = await db.get_user_reputation(guild_id, str(message.author.id))
    if reputation:
        embed.add_field(
            name="User Reputation",
            value=f"⚠️ {reputation['detection_count']} previous detections",
            inline=True
        )
    
    if message_content:
        content_display = message_content[:1024]
        embed.add_field(name="Message Content", value=content_display, inline=False)
    
    embed.add_field(name="Description", value=match.get('description', 'N/A'), inline=False)
    embed.add_field(name="Message Link", value=f"[Go to message]({message_jump_url})", inline=False)
    embed.set_image(url=f"attachment://{image_file.filename}")
    embed.set_footer(text=f"Hash: {match['hash']}")
    
    view = ActionButtons(message.author.id, message.guild.id, match['hash'], bot, db, is_false_positive=is_fp)
    await report_channel.send(embed=embed, file=image_file, view=view)
