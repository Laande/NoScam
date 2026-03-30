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


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_embed_paginator():
    import discord
    from src.utils.pagination import EmbedPaginator

    # Create test embeds
    embed1 = discord.Embed(title="Page 1", description="First page")
    embed2 = discord.Embed(title="Page 2", description="Second page")
    embed3 = discord.Embed(title="Page 3", description="Third page")

    embeds = [embed1, embed2, embed3]
    paginator = EmbedPaginator(embeds)

    # Test initial state
    assert paginator.current_page == 0
    assert paginator.get_current_embed() == embed1
    assert paginator.has_previous() is False
    assert paginator.has_next() is True

    # Test navigation
    paginator.next_page()
    assert paginator.current_page == 1
    assert paginator.get_current_embed() == embed2
    assert paginator.has_previous() is True
    assert paginator.has_next() is True

    paginator.next_page()
    assert paginator.current_page == 2
    assert paginator.get_current_embed() == embed3
    assert paginator.has_previous() is True
    assert paginator.has_next() is False

    # Test previous navigation
    paginator.previous_page()
    assert paginator.current_page == 1
    assert paginator.get_current_embed() == embed2

    # Test view creation
    assert hasattr(paginator, 'get_view')
    assert callable(paginator.get_view)


def test_create_hash_embeds():
    from src.utils.pagination import create_hash_embeds

    # Test with empty list
    embeds = create_hash_embeds("Test", [])
    assert len(embeds) == 1
    assert embeds[0].title == "Test"
    assert embeds[0].description == "None"

    # Test with items
    items = [
        {"hash": "hash1", "description": "desc1"},
        {"hash": "hash2", "description": "desc2"},
        {"hash": "hash3", "description": "desc3"},
    ]

    def format_func(item, global_hash):
        return f"{item['hash']}: {item['description']}"

    embeds = create_hash_embeds("Test Hashes", items, global_hash={}, items_per_page=2, description_func=format_func)

    assert len(embeds) == 2  # 3 items, 2 per page = 2 pages

    # Check first page
    assert "Test Hashes (3)" in embeds[0].title
    assert "1. hash1: desc1" in embeds[0].description
    assert "2. hash2: desc2" in embeds[0].description
    assert "Page 1/2" in embeds[0].footer.text

    # Check second page
    assert "3. hash3: desc3" in embeds[1].description
    assert "Page 2/2" in embeds[1].footer.text
