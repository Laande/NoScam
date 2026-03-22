import discord
from datetime import timedelta
from src.config import MUTE_DURATION_HOURS

async def perform_auto_action(member, guild, action):
    try:
        if action == 'mute':
            await member.timeout(discord.utils.utcnow() + timedelta(hours=MUTE_DURATION_HOURS))
        elif action == 'kick':
            await member.kick(reason="Scam image detected (automatic action)")
        elif action == 'ban':
            await member.ban(reason="Scam image detected (automatic action)")
    except Exception as e:
        print(f"Error performing automatic action: {e}")