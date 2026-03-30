from src.core.image_hash import calculate_image_hash
import os
import argparse


def parse_input(input_str):
    numbers = []
    parts = input_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            range_parts = part.split('-')
            if len(range_parts) != 2:
                raise ValueError(f"Invalid range format: {part}")
            try:
                start = int(range_parts[0])
                end = int(range_parts[1])
                if start > end:
                    raise ValueError(f"Invalid range: start > end in {part}")
                numbers.extend(range(start, end + 1))
            except ValueError as e:
                raise ValueError(f"Invalid number in range {part}: {e}")
        else:
            try:
                numbers.append(int(part))
            except ValueError:
                raise ValueError(f"Invalid number: {part}")
    
    if not numbers:
        raise ValueError("No valid numbers found in input")
    
    return sorted(set(numbers))


def get_image_hash(image_path):
    if not os.path.isfile(image_path):
        print(f"File not found: {image_path}")
        return None
    
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
            return calculate_image_hash(image_bytes)
    except Exception as e:
        print(f"Error processing image: {e}")
        return None


def setup_argparser():
    parser = argparse.ArgumentParser(
        description="Calculate image hash for a given image or range of images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python get_hash.py 1                        # Single image: global_images/1.jpg
  python get_hash.py 1-5                      # Range: global_images/1.jpg to 5.jpg
  python get_hash.py 1,3,5-8                  # Multiple: 1.jpg, 3.jpg, 5.jpg to 8.jpg
  python get_hash.py 1-10 -d images/ -e .png  # Custom directory and extension
        """
    )
    parser.add_argument("input", help="Image number(s) or range(s) (e.g., 1 or 1-5 or 1,3,5-8)")
    parser.add_argument("-d", "--dir", default="global_images", help="Directory containing images (default: global_images)")
    parser.add_argument("-e", "--ext", default=".jpg", help="Image file extension (default: .jpg)")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = setup_argparser()
    
    try:
        numbers = parse_input(args.input)
    except ValueError as e:
        print(f"Error parsing input: {e}")
        exit(1)
    
    for num in numbers:
        image_path = os.path.join(args.dir, f"{num}{args.ext}")
        hash_value = get_image_hash(image_path)
        if hash_value:
            print(f"Image: {image_path}, Hash: {hash_value}")