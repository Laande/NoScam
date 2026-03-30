from typing import List, Tuple, Dict, Any
import discord
from discord import ui


class EmbedPaginator:
    def __init__(self, embeds: List[discord.Embed], timeout: float = 300.0):
        self.embeds = embeds
        self.current_page = 0
        self.timeout = timeout

    def get_current_embed(self) -> discord.Embed:
        return self.embeds[self.current_page]

    def get_view(self) -> ui.View:
        return PaginatorView(self)

    def has_previous(self) -> bool:
        return self.current_page > 0

    def has_next(self) -> bool:
        return self.current_page < len(self.embeds) - 1

    def previous_page(self):
        if self.has_previous():
            self.current_page -= 1

    def next_page(self):
        if self.has_next():
            self.current_page += 1


class PaginatorView(ui.View):
    def __init__(self, paginator: EmbedPaginator):
        super().__init__(timeout=paginator.timeout)
        self.paginator = paginator

    @ui.button(label="◀ Previous", style=discord.ButtonStyle.primary, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: ui.Button):
        self.paginator.previous_page()
        await self._update_embed(interaction)

    @ui.button(label="Next ▶", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        self.paginator.next_page()
        await self._update_embed(interaction)

    async def _update_embed(self, interaction: discord.Interaction):
        embed = self.paginator.get_current_embed()

        self.previous_button.disabled = not self.paginator.has_previous()
        self.next_button.disabled = not self.paginator.has_next()

        await interaction.response.edit_message(embed=embed, view=self)


def create_hash_embeds(
    title: str,
    items: List[Dict[str, Any]],
    global_hash: Dict[str, Dict[str, Any]] = None,
    items_per_page: int = 10,
    description_func=None,
    color: discord.Color = discord.Color.blue()
) -> List[discord.Embed]:
    if not items:
        embed = discord.Embed(
            title=title,
            description="None",
            color=color
        )
        return [embed]

    embeds = []
    total_pages = (len(items) + items_per_page - 1) // items_per_page

    for page in range(total_pages):
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, len(items))
        page_items = items[start_idx:end_idx]

        embed = discord.Embed(
            title=f"{title} ({len(items)})",
            color=color
        )

        descriptions = []
        for i, item in enumerate(page_items, start_idx + 1):
            if description_func:
                desc = description_func(item, global_hash)
            else:
                desc = str(item)
            descriptions.append(f"{i}. {desc}")

        embed.description = "\n".join(descriptions)

        if total_pages > 1:
            embed.set_footer(text=f"Page {page + 1}/{total_pages}")

        embeds.append(embed)

    return embeds
