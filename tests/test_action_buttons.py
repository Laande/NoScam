import asyncio

from src.handlers.views import ActionButtons


class Dummy:
    pass


def _build_view(**kwargs):
    async def _create():
        return ActionButtons(**kwargs)

    return asyncio.run(_create())


def test_action_buttons_uses_passed_member_when_available():
    member = Dummy()

    view = _build_view(
        user_id=123,
        guild_id=456,
        hash_value="abc",
        bot_instance=Dummy(),
        db_instance=Dummy(),
        member=member,
    )

    assert view.member is member


def test_action_buttons_falls_back_to_guild_member_cache():
    member = Dummy()

    class FakeGuild:
        def __init__(self, member):
            self.member = member

        def get_member(self, user_id):
            return self.member if user_id == 123 else None

    view = _build_view(
        user_id=123,
        guild_id=456,
        hash_value="abc",
        bot_instance=Dummy(),
        db_instance=Dummy(),
    )

    assert asyncio.run(view._resolve_member(FakeGuild(member))) is member
