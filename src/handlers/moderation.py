import discord
from datetime import timedelta
from src.config import (
    MUTE_DURATION_HOURS,
    PERMISSION_WARNING_COOLDOWN_MINUTES,
    ACTION_PERMISSION_NAMES,
    SUPPORT_SERVER_URL,
)
from src.handlers.views import PermissionWarningView

_permission_warning_last_sent = {}


async def send_missing_permission_warning(
    bot, db, guild, permission_name, summary, why_extra=None, fix_extra=None
):
    if bot is None or db is None or guild is None:
        return False

    guild_id = str(guild.id)
    now = discord.utils.utcnow()
    last_sent = _permission_warning_last_sent.get(guild_id)

    if last_sent is not None and now - last_sent < timedelta(minutes=PERMISSION_WARNING_COOLDOWN_MINUTES):
        return False

    server_config = await db.get_server_config(guild_id)
    if not server_config or not server_config.get('report_channel_id'):
        return False

    if server_config.get('permission_warning_muted', 0) == 1:
        return False

    channel = bot.get_channel(int(server_config['report_channel_id']))
    if not channel:
        return False

    embed = discord.Embed(
        title="⚠️ Part of my scam protection is disabled",
        description=(
            f"I detected a scam image, but Discord refused to let me {summary}.\n"
            f"Until this is fixed, scammers get reported here but not stopped."
        ),
        color=discord.Color.red(),
        timestamp=now
    )

    why = (
        f"Either my role doesn't have the **{permission_name}** permission{why_extra or ''}."
    )

    embed.add_field(name="Why", value=why, inline=False)

    fixes = [
        "• Server Settings → Roles",
        f"• Open my role and enable **{permission_name}**",
    ]
    if fix_extra:
        fixes.append(fix_extra)
    fixes.append("• Optional: `/set_action none` to turn automatic actions off entirely")

    embed.add_field(name="How to fix", value="\n".join(fixes), inline=False)
    embed.set_footer(text=f"Need help? {SUPPORT_SERVER_URL}")

    try:
        await channel.send(embed=embed, view=PermissionWarningView(guild.id, db))
    except discord.Forbidden:
        return False

    _permission_warning_last_sent[guild_id] = now
    return True


async def send_delete_permission_warning(bot, db, guild):
    return await send_missing_permission_warning(
        bot, db, guild,
        permission_name=ACTION_PERMISSION_NAMES['delete'],
        summary="delete the scam message",
        why_extra=", or I don't have it allowed in this specific channel",
        fix_extra="• Check the channel overwrites too (right-click the channel → Permissions)",
    )


async def send_action_permission_warning(bot, db, guild, action, member):
    summary = f"run the automatic action (`{action}`)"
    if member is not None:
        summary += f" on {member.mention}"

    return await send_missing_permission_warning(
        bot, db, guild,
        permission_name=ACTION_PERMISSION_NAMES.get(action, 'Moderate Members'),
        summary=summary,
        why_extra=", or the member is higher than me in the role hierarchy",
        fix_extra="• Drag my role above the members and roles I need to punish",
    )


async def perform_auto_action(member, action, guild=None, bot=None, db=None):
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
    except discord.Forbidden as e:
        try:
            await send_action_permission_warning(bot, db, guild, action, target_member)
        except Exception as warning_error:
            pass
    except Exception as e:
        print(f"Error performing automatic action: {e}")