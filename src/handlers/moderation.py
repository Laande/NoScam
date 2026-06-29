import discord
from datetime import timedelta
from src.config import MUTE_DURATION_HOURS

async def perform_auto_action(member, action, guild=None):
    msg = "Scam image detected (automatic action)"

    target_member = member
    if guild is not None and target_member is not None:
        if not isinstance(target_member, discord.Member):
            user_id = target_member.id
            target_member = guild.get_member(user_id)
            if target_member is None:
                try:
                    target_member = await guild.fetch_member(user_id)
                except (discord.NotFound, discord.HTTPException):
                    target_member = None

    if target_member is None:
        print("Cannot perform automatic action: target member could not be resolved")
        return

    try:
        if action == 'mute':
            await target_member.timeout(discord.utils.utcnow() + timedelta(hours=MUTE_DURATION_HOURS), reason=msg)
        elif action == 'kick':
            await target_member.kick(reason=msg)
        elif action == 'ban':
            await target_member.ban(reason=msg)
    except Exception as e:
        print(f"Error performing automatic action: {e}")