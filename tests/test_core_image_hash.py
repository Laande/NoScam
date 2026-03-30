import os
import pytest
from src.core.image_hash import calculate_image_hash, find_similar_hash


def test_calculate_image_hash_from_file_bytes():
    image_path = 'global_images/1.jpg'
    if not os.path.exists(image_path):
        pytest.skip('Missing test image: global_images/1.jpg')

    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    result = calculate_image_hash(image_bytes)
    assert isinstance(result, str)
    assert len(result) > 0


def test_calculate_image_hash_corrupted_bytes_raises_value_error():
    with pytest.raises(ValueError):
        calculate_image_hash(b'not-an-image')


def test_find_similar_hash_finds_exact_match():
    sample_list = [{'hash': 'e1e140407f303e20', 'description': 'test'}]
    item, distance = find_similar_hash('e1e140407f303e20', sample_list, threshold=0)
    assert item is not None
    assert distance == 0


def test_find_similar_hash_no_match():
    sample_list = [{'hash': 'e1e140407f303e20', 'description': 'test'}]
    item, distance = find_similar_hash('ffffffffffffffff', sample_list, threshold=0)
    assert item is None
    assert distance is None


def test_find_similar_hash_with_threshold():
    sample_list = [
        {'hash': 'e1e140407f303e22', 'description': 'exact'},
        {'hash': 'e1e140407f303e21', 'description': 'close'}
    ]

    item, distance = find_similar_hash('e1e140407f303e22', sample_list, threshold=2)
    assert item is not None
    assert distance is not None
    assert distance <= 2
    assert item['description'] in {'exact', 'close'}
