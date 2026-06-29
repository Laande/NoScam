import pytest

from src.utils.img_urls import extract_image_urls_from_message


class DummyAttachment:
    def __init__(self, url, content_type):
        self.url = url
        self.content_type = content_type


class DummyImage:
    def __init__(self, url):
        self.url = url


class DummyEmbed:
    def __init__(self, embed_type=None, url=None, image=None, thumbnail=None):
        self.type = embed_type
        self.url = url
        self.image = image
        self.thumbnail = thumbnail


class DummyMessage:
    def __init__(self, attachments=None, embeds=None, content=None):
        self.attachments = attachments or []
        self.embeds = embeds or []
        self.content = content or ''


def test_extract_image_urls_from_message_with_image_attachments():
    message = DummyMessage(attachments=[
        DummyAttachment('https://example.com/photo1.png', 'image/png'),
        DummyAttachment('https://example.com/file.txt', 'text/plain'),
        DummyAttachment('https://example.com/photo2.jpg', 'image/jpeg')
    ])

    result = extract_image_urls_from_message(message)

    assert result == [
        'https://example.com/photo1.png',
        'https://example.com/photo2.jpg'
    ]


def test_extract_image_urls_from_message_with_embeds():
    message = DummyMessage(embeds=[
        DummyEmbed(embed_type='image', url='https://example.com/embed-image.png'),
        DummyEmbed(image=DummyImage('https://example.com/embed-image-obj.png')),
        DummyEmbed(thumbnail=DummyImage('https://example.com/embed-thumb.png')),
        DummyEmbed(embed_type='rich', url='https://example.com/not-image.png'),
    ])

    result = extract_image_urls_from_message(message)

    assert result == [
        'https://example.com/embed-image.png',
        'https://example.com/embed-image-obj.png',
        'https://example.com/embed-thumb.png'
    ]


def test_extract_image_urls_from_message_with_urls_in_content():
    message = DummyMessage(
        content='Check these images https://cdn.discordapp.com/attachments/123/456/image1.jpg?ex=1&is=2 and https://cdn.discordapp.com/attachments/123/456/image2.png?ex=3&is=4 and this text https://example.com/page.html'
    )

    result = extract_image_urls_from_message(message)

    assert result == [
        'https://cdn.discordapp.com/attachments/123/456/image1.jpg?ex=1&is=2',
        'https://cdn.discordapp.com/attachments/123/456/image2.png?ex=3&is=4'
    ]


def test_extract_image_urls_from_message_ignores_non_discord_content_urls():
    message = DummyMessage(
        content='https://example.com/image.png'
    )

    result = extract_image_urls_from_message(message)

    assert result == []


def test_extract_image_urls_from_message_returns_empty_when_no_images():
    message = DummyMessage(
        attachments=[DummyAttachment('https://example.com/file.pdf', 'application/pdf')],
        embeds=[DummyEmbed(embed_type='rich', url='https://example.com/page.html')]
    )

    result = extract_image_urls_from_message(message)

    assert result == []
