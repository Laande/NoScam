import os
import pytest
from get_hash import parse_input, get_image_hash


def test_parse_input_single_number():
    assert parse_input('5') == [5]


def test_parse_input_range():
    assert parse_input('1-3') == [1, 2, 3]


def test_parse_input_multiple_ranges_and_values():
    assert parse_input('1,3,5-7') == [1, 3, 5, 6, 7]


def test_parse_input_invalid_number():
    with pytest.raises(ValueError):
        parse_input('abc')


def test_parse_input_empty():
    with pytest.raises(ValueError):
        parse_input('')


def test_get_image_hash_missing_file():
    assert get_image_hash('global_images/does_not_exist.jpg') is None


def test_get_image_hash_existing_file():
    path = 'global_images/1.jpg'
    if not os.path.exists(path):
        pytest.skip('Missing test image: global_images/1.jpg')

    value = get_image_hash(path)
    assert value is not None
    assert isinstance(value, str)
    assert len(value) > 0
