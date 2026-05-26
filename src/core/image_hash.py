import imagehash
from PIL import Image
import io
import warnings
from src.config import DEFAULT_THRESHOLD, DEFAULT_WARNING_THRESHOLD

def calculate_image_hash(image_bytes):
    try:
        # Suppress PIL warnings about truncated files
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            image = Image.open(io.BytesIO(image_bytes))
            return str(imagehash.average_hash(image))
    except Exception as e:
        raise ValueError(f"Failed to process image: {e}")

def find_best_hash(target_hash, hash_list, threshold=None, warning_threshold=None):
    if threshold is None:
        threshold = DEFAULT_THRESHOLD
    if warning_threshold is None:
        warning_threshold = DEFAULT_WARNING_THRESHOLD

    try:
        target = imagehash.hex_to_hash(target_hash)
    except (ValueError, TypeError) as e:
        print(f"Invalid target hash: {target_hash} - {e}")
        return None, None, None
    
    best_warning_item = None
    best_warning_distance = None

    for item in hash_list:
        try:
            stored_hash = imagehash.hex_to_hash(item['hash'])
            distance = target - stored_hash

            if distance <= threshold:
                return item, distance, 'detected'

            if distance <= warning_threshold:
                if best_warning_distance is None or distance < best_warning_distance:
                    best_warning_distance = distance
                    best_warning_item = item
        except (ValueError, TypeError) as e:
            print(f"Skipping invalid hash: {item.get('hash', 'unknown')} - {e}")
            continue

    if best_warning_item is not None:
        return best_warning_item, best_warning_distance, 'warning'

    return None, None, None
