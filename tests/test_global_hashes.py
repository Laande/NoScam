import os
import json


def test_global_hashes_file_exists():
    assert os.path.exists('global_hashes.json')


def test_global_hashes_schema_and_files():
    with open('global_hashes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert 'hashes' in data
    assert isinstance(data['hashes'], list)

    hashes = []
    for item in data['hashes']:
        assert isinstance(item, dict)
        assert 'hash' in item
        assert 'image_path' in item

        h = item['hash']
        p = item['image_path']

        assert isinstance(h, str) and len(h) > 0
        assert isinstance(p, str) and len(p) > 0

        hashes.append(h)

        image_file = os.path.join('global_images', p)
        assert os.path.exists(image_file), f'Missing image: {image_file}'

    assert len(set(hashes)) == len(hashes), 'Duplicate hashes found in global_hashes.json'
