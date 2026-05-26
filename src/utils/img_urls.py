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
    
    return image_urls