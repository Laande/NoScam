import discord
from datetime import timedelta

class ActionButtons(discord.ui.View):
    def __init__(self, user_id, guild_id, hash_value, bot_instance, db_instance, is_false_positive=False):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.guild_id = guild_id
        self.hash_value = hash_value
        self.bot = bot_instance
        self.db = db_instance
        self.is_false_positive = is_false_positive
        
        if is_false_positive:
            self.remove_item(self.false_positive_button)
        else:
            self.remove_item(self.mark_as_scam_button)
    
    @discord.ui.button(label="Mute", style=discord.ButtonStyle.secondary, emoji="🔇", row=0)
    async def mute_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(self.user_id)
        
        if member:
            try:
                await member.timeout(discord.utils.utcnow() + timedelta(hours=1))
                await interaction.response.send_message(f"✅ {member.mention} has been muted for 1 hour.")
            except Exception as e:
                await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Member not found.", ephemeral=True)
    
    @discord.ui.button(label="Kick", style=discord.ButtonStyle.danger, emoji="👢", row=0)
    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(self.user_id)
        
        if member:
            try:
                await member.kick(reason="Scam image detected")
                await interaction.response.send_message(f"✅ {member.name} has been kicked.")
            except Exception as e:
                await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Member not found.", ephemeral=True)
    
    @discord.ui.button(label="Ban", style=discord.ButtonStyle.danger, emoji="🔨", row=0)
    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(self.user_id)
        
        if member:
            try:
                await member.ban(reason="Scam image detected")
                await interaction.response.send_message(f"✅ {member.name} has been banned.")
            except Exception as e:
                await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Member not found.", ephemeral=True)
    
    @discord.ui.button(label="False Positive", style=discord.ButtonStyle.success, emoji="✅", row=1)
    async def false_positive_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = await self.db.add_false_positive(
            str(self.guild_id),
            self.hash_value,
            str(interaction.user.id)
        )
        
        if success:
            await interaction.response.send_message(f"✅ Hash marked as false positive. It will no longer trigger detections on this server.")
            
            new_view = ActionButtons(
                self.user_id, 
                self.guild_id, 
                self.hash_value, 
                self.bot, 
                self.db, 
                is_false_positive=True
            )
            await interaction.message.edit(view=new_view)
        else:
            await interaction.response.send_message("❌ This hash is already marked as a false positive.", ephemeral=True)
    
    @discord.ui.button(label="Mark as Scam", style=discord.ButtonStyle.danger, emoji="⚠️", row=1)
    async def mark_as_scam_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = await self.db.remove_false_positive(
            str(self.guild_id),
            self.hash_value
        )
        
        if success:
            await interaction.response.send_message(f"✅ Hash removed from false positives. It will now trigger detections again.")
            
            new_view = ActionButtons(
                self.user_id, 
                self.guild_id, 
                self.hash_value, 
                self.bot, 
                self.db, 
                is_false_positive=False
            )
            await interaction.message.edit(view=new_view)
        else:
            await interaction.response.send_message("❌ This hash is not in the false positives list.", ephemeral=True)
