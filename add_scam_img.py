import argparse
import io
import json
import os
import re
from pathlib import Path

from PIL import Image
import imagehash

from src.config import DEFAULT_WARNING_THRESHOLD
from src.core.image_hash import calculate_image_hash

GLOBAL_IMAGES_DIR = "global_images"
GLOBAL_HASHES_PATH = "global_hashes.json"
SUPPORTED_EXTENSIONS = [".jpg", ".jpeg"]
PLACEHOLDER_DESCRIPTION = "Placeholder description"


def load_global_hashes(json_path):
    if not os.path.exists(json_path):
        return {"hashes": []}

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_global_hashes(json_path, data):
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ensure_dir_exists(path):
    os.makedirs(path, exist_ok=True)


def convert_source_jpeg_to_jpg(file_path):
    source_path = Path(file_path)
    if source_path.suffix.lower() != ".jpeg":
        return file_path

    jpg_path = source_path.with_suffix(".jpg")
    try:
        with Image.open(source_path) as image:
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            image.save(jpg_path, format="JPEG")
    except Exception as e:
        raise ValueError(f"Failed to convert JPEG to JPG: {e}")

    source_path.unlink()
    return str(jpg_path)


def get_next_image_index(image_entries):
    max_index = 0
    for item in image_entries:
        image_path = item.get("image_path", "")
        match = re.match(r"^(\d+)\.jpg$", image_path)
        if match:
            try:
                max_index = max(max_index, int(match.group(1)))
            except ValueError:
                continue
    return max_index + 1


def is_image_file(path):
    return os.path.isfile(path) and Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def compare_to_existing_hashes(image_hash, hash_entries, warning_threshold):
    try:
        target = imagehash.hex_to_hash(image_hash)
    except (TypeError, ValueError):
        return False

    for entry in hash_entries:
        stored_hash = entry.get("hash")
        if not stored_hash:
            continue
        try:
            distance = target - imagehash.hex_to_hash(stored_hash)
        except (TypeError, ValueError):
            continue
        if distance <= warning_threshold:
            return True
    return False


def add_images_from_folder(source_dir, warning_threshold=DEFAULT_WARNING_THRESHOLD):
    source_dir = os.path.abspath(source_dir)
    ensure_dir_exists(source_dir)
    ensure_dir_exists(GLOBAL_IMAGES_DIR)

    hashes_data = load_global_hashes(GLOBAL_HASHES_PATH)
    hash_entries = hashes_data.get("hashes", [])
    next_index = get_next_image_index(hash_entries)

    added = []
    skipped = []

    for filename in sorted(os.listdir(source_dir)):
        source_path = os.path.join(source_dir, filename)
        if not is_image_file(source_path):
            continue

        if Path(source_path).suffix.lower() == ".jpeg":
            source_path = convert_source_jpeg_to_jpg(source_path)

        try:
            with open(source_path, "rb") as f:
                image_bytes = f.read()
        except OSError as e:
            skipped.append((filename, f"read error: {e}"))
            continue

        try:
            image_hash = calculate_image_hash(image_bytes)
        except ValueError as e:
            skipped.append((filename, f"hash error: {e}"))
            continue

        if compare_to_existing_hashes(image_hash, hash_entries, warning_threshold):
            skipped.append((filename, f"match within warning threshold ({warning_threshold})"))
            continue

        destination_filename = f"{next_index}.jpg"
        destination_path = os.path.join(GLOBAL_IMAGES_DIR, destination_filename)

        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")
                image.save(destination_path, format="JPEG")
        except Exception:
            try:
                Image.open(source_path).convert("RGB").save(destination_path, format="JPEG")
            except Exception as e:
                skipped.append((filename, f"save error: {e}"))
                continue

        hash_entries.append({
            "hash": image_hash,
            "description": PLACEHOLDER_DESCRIPTION,
            "image_path": destination_filename,
        })

        added.append((filename, destination_filename))
        next_index += 1

        try:
            os.remove(source_path)
        except OSError:
            pass

    hashes_data["hashes"] = hash_entries
    save_global_hashes(GLOBAL_HASHES_PATH, hashes_data)

    return added, skipped


def setup_argparser():
    parser = argparse.ArgumentParser(
        description="Import scam images from a source folder into global_images and update global_hashes.json.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python add_scam_img.py
  python add_scam_img.py --source-dir "dir name"
  python add_scam_img.py --warning-threshold 8
"""
    )
    parser.add_argument(
        "--source-dir",
        default="img_to_add",
        help="Source folder containing images to evaluate (default: 'img_to_add')",
    )
    parser.add_argument(
        "--warning-threshold",
        type=int,
        default=DEFAULT_WARNING_THRESHOLD,
        help="Warning threshold used to compare image hashes (default from config.py)",
    )
    return parser


def main(argv=None):
    parser = setup_argparser()
    args = parser.parse_args(argv)
    added, skipped = add_images_from_folder(args.source_dir, args.warning_threshold)

    for source_name, dest_name in added:
        print(f"Added {source_name} -> {dest_name}")
    for source_name, reason in skipped:
        print(f"Skipped {source_name}: {reason}")

    print(f"Added {len(added)} image(s), skipped {len(skipped)} image(s).")


if __name__ == "__main__":
    main()
