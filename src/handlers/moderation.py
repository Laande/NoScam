import discord
from datetime import timedelta
from src.config import MUTE_DURATION_HOURS

async def perform_auto_action(member, action):
    msg = "Scam image detected (automatic action)"
    try:
        if action == 'mute':
            await member.timeout(discord.utils.utcnow() + timedelta(hours=MUTE_DURATION_HOURS), reason=msg)
        elif action == 'kick':
            await member.kick(reason=msg)
        elif action == 'ban':
            await member.ban(reason=msg)
    except Exception as e:
        print(f"Error performing automatic action: {e}")