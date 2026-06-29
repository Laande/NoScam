import re
import discord


def extract_image_urls_from_message(message: discord.Message) -> list:
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

    content = getattr(message, 'content', '')
    if content:
        maybe_urls = re.findall(r'https?://[^\s)\]>]+', content)
        for url in maybe_urls:
            cleaned_url = url.rstrip('.,;:')
            if 'cdn.discordapp.com' in cleaned_url.lower():
                image_urls.append(cleaned_url)

    return image_urls