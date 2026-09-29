import asyncio
from datetime import timedelta

from src.config import PERMISSION_WARNING_COOLDOWN_MINUTES
from src.handlers import moderation
from src.handlers.views import PermissionWarningView


class FakeChannel:
    def __init__(self):
        self.sent = []

    async def send(self, *, embed, view=None):
        self.sent.append((embed, view))


class FakeBot:
    def __init__(self, channel):
        self.channel = channel

    def get_channel(self, channel_id):
        return self.channel if channel_id == 999 else None


class DummyInteraction:
    def __init__(self):
        self.response = DummyResponse()


class DummyResponse:
    def __init__(self):
        self.done = False

    async def edit_message(self, **kwargs):
        self.done = True

    async def wait_for_edit(self):
        return self


class FakeDB:
    def __init__(self, report_channel_id="999", muted=0):
        self.report_channel_id = report_channel_id
        self.muted = muted
        self.saved_mutes = []

    async def get_server_config(self, guild_id):
        return {
            "report_channel_id": self.report_channel_id,
            "permission_warning_muted": self.muted,
        }

    async def set_permission_warning_muted(self, guild_id, muted):
        self.muted = 1 if muted else 0
        self.saved_mutes.append((guild_id, self.muted))
        return True


def _send(bot, db, guild_id="1"):
    guild = type("Guild", (), {"id": int(guild_id)})()
    member = type("Member", (), {"mention": "<@1>"})()
    return asyncio.run(moderation.send_action_permission_warning(bot, db, guild, "ban", member))


def _send_delete(bot, db, guild_id="1"):
    guild = type("Guild", (), {"id": int(guild_id)})()
    return asyncio.run(moderation.send_delete_permission_warning(bot, db, guild))


def test_permission_warning_is_sent_to_report_channel():
    moderation._permission_warning_last_sent.clear()
    channel = FakeChannel()

    assert _send(FakeBot(channel), FakeDB()) is True
    assert len(channel.sent) == 1

    embed, view = channel.sent[0]
    assert isinstance(view, PermissionWarningView)
    assert "Ban Members" in embed.fields[0].value
    assert view.children


def test_delete_permission_warning_names_manage_messages():
    moderation._permission_warning_last_sent.clear()
    channel = FakeChannel()

    assert _send_delete(FakeBot(channel), FakeDB()) is True

    embed, _ = channel.sent[0]
    assert "delete the scam message" in embed.description
    assert "Manage Messages" in embed.fields[0].value
    assert "role hierarchy" not in embed.fields[0].value
    assert "channel overwrites" in embed.fields[1].value


def test_permission_warning_mentions_role_hierarchy_for_punishments():
    moderation._permission_warning_last_sent.clear()
    channel = FakeChannel()

    assert _send(FakeBot(channel), FakeDB()) is True

    embed, _ = channel.sent[0]
    assert "role hierarchy" in embed.fields[0].value
    assert "above the members and roles" in embed.fields[1].value


def test_delete_and_action_warnings_share_the_same_cooldown():
    moderation._permission_warning_last_sent.clear()
    channel = FakeChannel()
    bot = FakeBot(channel)

    assert _send_delete(bot, FakeDB()) is True
    assert _send(bot, FakeDB()) is False
    assert len(channel.sent) == 1


def test_permission_warning_respects_cooldown():
    moderation._permission_warning_last_sent.clear()
    channel = FakeChannel()
    bot = FakeBot(channel)

    assert _send(bot, FakeDB()) is True
    assert _send(bot, FakeDB()) is False
    assert len(channel.sent) == 1

    cooldown = timedelta(minutes=PERMISSION_WARNING_COOLDOWN_MINUTES)
    moderation._permission_warning_last_sent["1"] -= cooldown + timedelta(minutes=1)

    assert _send(bot, FakeDB()) is True
    assert len(channel.sent) == 2


def test_permission_warning_is_per_guild():
    moderation._permission_warning_last_sent.clear()
    channel = FakeChannel()

    assert _send(FakeBot(channel), FakeDB(), guild_id="1") is True
    assert _send(FakeBot(channel), FakeDB(), guild_id="2") is True
    assert len(channel.sent) == 2


def test_permission_warning_skipped_without_report_channel():
    moderation._permission_warning_last_sent.clear()
    channel = FakeChannel()

    assert _send(FakeBot(channel), FakeDB(report_channel_id=None)) is False
    assert channel.sent == []


def test_permission_warning_not_sent_when_muted():
    moderation._permission_warning_last_sent.clear()
    channel = FakeChannel()

    assert _send(FakeBot(channel), FakeDB(muted=1)) is False
    assert channel.sent == []


def test_mute_button_disables_future_warnings():
    moderation._permission_warning_last_sent.clear()
    channel = FakeChannel()
    db = FakeDB()

    assert _send(FakeBot(channel), db) is True

    view = channel.sent[0][1]
    interaction = DummyInteraction()

    asyncio.run(view.mute_button.callback(interaction))
    asyncio.run(interaction.response.wait_for_edit())

    assert db.saved_mutes == [("1", 1)]
    assert view.is_finished() is False
    assert all(item.disabled for item in view.children)

    assert _send(FakeBot(channel), db) is False
    assert len(channel.sent) == 1
