import discord
import io
import asyncio
from src.core.image_hash import calculate_image_hash, find_similar_hash
from src.config import DEFAULT_THRESHOLD

detection_queue = asyncio.Queue()

async def process_detection_queue(db):
    while True:
        try:
            detection_data = await detection_queue.get()
            guild_id = detection_data['guild_id']
            user_id = detection_data['user_id']
            hash_value = detection_data['hash']
            
            await db.increment_detection(guild_id, user_id, hash_value)
            detection_queue.task_done()
        except Exception as e:
            print(f"Error processing detection queue: {e}")

async def check_images_for_scam(message, attachments, session, db):
    try:
        guild_id = str(message.guild.id)
        server_config = await db.get_server_config(guild_id)
        threshold = server_config['hash_threshold'] if server_config else DEFAULT_THRESHOLD
        all_hashes = await db.get_all_hashes(guild_id)
        
        scam_detected = False
        match_info = None
        best_distance = float('inf')
        flagged_attachment = None
        
        for attachment in attachments:
            async with session.get(attachment.url) as resp:
                if resp.status != 200:
                    continue
                
                image_bytes = await resp.read()
                image_hash = calculate_image_hash(image_bytes)
                match, distance = find_similar_hash(image_hash, all_hashes, threshold)
                
                if match:
                    scam_detected = True
                    if distance < best_distance:
                        best_distance = distance
                        match_info = match
                        flagged_attachment = attachment
        
        if scam_detected:
            async with session.get(flagged_attachment.url) as img_resp:
                if img_resp.status == 200:
                    img_data = await img_resp.read()
                    image_file = discord.File(io.BytesIO(img_data), filename=flagged_attachment.filename)
            
            return {
                'detected': True,
                'match': match_info,
                'distance': best_distance,
                'image_file': image_file,
                'message_content': message.content,
                'message_jump_url': message.jump_url
            }
        
        return {'detected': False}
                
    except Exception as e:
        print(f"Error while verifying images: {e}")
        return {'detected': False}