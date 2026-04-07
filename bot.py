import discord
from discord import app_commands
import aiohttp
import os
import asyncio
from dotenv import load_dotenv

from src.core.database import Database
from src.handlers.detection import check_images_for_scam, process_detection_queue, detection_queue
from src.handlers.notifications import send_user_warning, send_scam_report
from src.handlers.moderation import perform_auto_action
from src.commands.hash_commands import setup_hash_commands
from src.commands.config_commands import setup_config_commands
from src.commands.help_commands import setup_help_commands
from src.utils.messages import get_welcome_embed, get_setup_required_embed
from src.config import DEFAULT_ACTION

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.session = None
        self.db = Database()
        self.queue_processor_task = None
        self.server_config_cache = {}
        self.cache_ttl = 300
    
    def invalidate_config_cache(self, guild_id: str):
        if guild_id in self.server_config_cache:
            del self.server_config_cache[guild_id]
    
    async def setup_hook(self):
        await self.db.init_database()
        self.session = aiohttp.ClientSession()
        self.queue_processor_task = asyncio.create_task(process_detection_queue(self.db))
        
        setup_hash_commands(self.tree, self, self.db)
        setup_config_commands(self.tree, self, self.db)
        setup_help_commands(self.tree, self, self.db)
        
    async def close(self):
        if self.session:
            await self.session.close()
        if self.queue_processor_task:
            self.queue_processor_task.cancel()
        await super().close()

bot = Bot()

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Bot connected as {bot.user}')
    activity = discord.Activity(type=discord.ActivityType.watching, name="👀")
    await bot.change_presence(activity=activity)

@bot.event
async def on_guild_join(guild):
    try:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                embed_links=True,
                attach_files=True,
                read_message_history=True
            )
        }
        
        for role in guild.roles:
            if role.permissions.moderate_members or role.permissions.manage_messages:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=False,
                    read_message_history=True
                )
        
        channel = await guild.create_text_channel(
            name='scam-reports',
            topic='Automatic scam image detection reports',
            reason='Scam Detector Bot setup',
            overwrites=overwrites
        )
        
        guild_id = str(guild.id)
        await bot.db.set_report_channel(guild_id, str(channel.id))
        
        embed = get_welcome_embed(guild.name)
        await channel.send(embed=embed)
        
    except discord.Forbidden:
        try:
            owner = guild.owner
            if owner:
                embed = get_setup_required_embed()
                await owner.send(embed=embed)
        except Exception as e:
            print(f'Could not send setup message to owner: {e}')
    except Exception as e:
        print(f'Error creating channel in {guild.name}: {e}')

async def get_cached_config(guild_id: str):
    current_time = asyncio.get_event_loop().time()
    
    if guild_id in bot.server_config_cache:
        cached_data, timestamp = bot.server_config_cache[guild_id]
        if current_time - timestamp < bot.cache_ttl:
            return cached_data
    
    config = await bot.db.get_server_config(guild_id)
    bot.server_config_cache[guild_id] = (config, current_time)
    return config

@bot.event
async def on_message(message):
    if not message.guild:
        return
    
    if not message.attachments and not message.embeds:
        return
    
    guild_id = str(message.guild.id)
    
    if message.author.bot:
        server_config = await get_cached_config(guild_id)
        scan_bots = server_config.get('scan_bot_messages', 0) == 1 if server_config else False
        if not scan_bots:
            return
    
    image_urls = []
    
    if message.attachments:
        image_urls.extend([
            att.url for att in message.attachments
            if att.content_type and att.content_type.startswith('image/')
        ])
    
    if message.embeds:
        for embed in message.embeds:
            if embed.type == 'image' and embed.url:
                image_urls.append(embed.url)
            if embed.image and embed.image.url:
                image_urls.append(embed.image.url)
            if embed.thumbnail and embed.thumbnail.url:
                image_urls.append(embed.thumbnail.url)
    
    if not image_urls:
        return
    
    result = await check_images_for_scam(message, image_urls, bot.session, bot.db)
    
    if result['detected']:
        user_id = str(message.author.id)
        server_config = await get_cached_config(guild_id)
        action = server_config['default_action'] if server_config and server_config['default_action'] else DEFAULT_ACTION
        
        if action != 'none':
            try:
                await message.delete()
            except Exception:
                pass
        
        asyncio.create_task(perform_auto_action(message.author, message.guild, action))
        asyncio.create_task(send_user_warning(message, action, message.guild.name))
        
        asyncio.create_task(send_scam_report(
            bot,
            bot.db,
            message,
            result['match'],
            result['distance'],
            result['image_file'],
            result['message_content'],
            result['message_jump_url']
        ))
        
        await detection_queue.put({
            'guild_id': guild_id,
            'user_id': user_id,
            'hash': result['match']['hash']
        })
        

if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("ERROR: DISCORD_TOKEN environment variable not set")
        exit(1)
    bot.run(token)
