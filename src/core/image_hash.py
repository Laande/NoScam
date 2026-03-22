import imagehash
from PIL import Image
import io

def calculate_image_hash(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    return str(imagehash.average_hash(image))

def find_similar_hash(target_hash, hash_list, threshold=5):
    try:
        target = imagehash.hex_to_hash(target_hash)
    except (ValueError, TypeError) as e:
        print(f"Invalid target hash: {target_hash} - {e}")
        return None, None
    
    for item in hash_list:
        try:
            stored_hash = imagehash.hex_to_hash(item['hash'])
            distance = target - stored_hash
            
            if distance <= threshold:
                return item, distance
        except (ValueError, TypeError) as e:
            print(f"Skipping invalid hash: {item.get('hash', 'unknown')} - {e}")
            continue
    
    return None, None
