import json
from PIL import Image

import add_scam_img
from src.core.image_hash import calculate_image_hash


def create_test_image(path, color=(255, 0, 0)):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (10, 10), color)
    image.save(path, format="JPEG")


def create_checker_test_image(path, color1=(255, 0, 0), color2=(0, 0, 255)):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (10, 10), color1)
    for x in range(10):
        for y in range(10):
            if (x + y) % 2 == 0:
                image.putpixel((x, y), color2)
    image.save(path, format="JPEG")


def test_add_scam_img(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    global_images_dir = repo_root / "global_images"
    global_images_dir.mkdir()

    global_hashes_path = repo_root / "global_hashes.json"
    existing_image = global_images_dir / "1.jpg"
    create_test_image(existing_image, color=(255, 0, 0))

    existing_hash = calculate_image_hash(existing_image.read_bytes())
    global_hashes_path.write_text(json.dumps({"hashes": [{
        "hash": existing_hash,
        "description": "Existing image",
        "image_path": "1.jpg"
    }]}, indent=2), encoding="utf-8")

    source_dir = repo_root / "add scam img"
    source_dir.mkdir()
    source_image = source_dir / "new_image.jpeg"
    create_checker_test_image(source_image, color1=(255, 0, 0), color2=(0, 0, 255))

    monkeypatch.setattr(add_scam_img, "GLOBAL_IMAGES_DIR", str(global_images_dir))
    monkeypatch.setattr(add_scam_img, "GLOBAL_HASHES_PATH", str(global_hashes_path))

    added, skipped = add_scam_img.add_images_from_folder(str(source_dir), warning_threshold=add_scam_img.DEFAULT_WARNING_THRESHOLD)

    assert added == [("new_image.jpeg", "2.jpg")]
    assert skipped == []

    updated_data = json.loads(global_hashes_path.read_text(encoding="utf-8"))
    assert len(updated_data["hashes"]) == 2
    assert updated_data["hashes"][-1]["image_path"] == "2.jpg"
    assert updated_data["hashes"][-1]["description"] == add_scam_img.PLACEHOLDER_DESCRIPTION
    assert (global_images_dir / "2.jpg").exists()
    assert not source_image.exists()


def test_removes_source_image(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    global_images_dir = repo_root / "global_images"
    global_images_dir.mkdir()

    global_hashes_path = repo_root / "global_hashes.json"
    existing_image = global_images_dir / "1.jpg"
    create_test_image(existing_image, color=(255, 0, 0))

    existing_hash = calculate_image_hash(existing_image.read_bytes())
    global_hashes_path.write_text(json.dumps({"hashes": [{
        "hash": existing_hash,
        "description": "Existing image",
        "image_path": "1.jpg"
    }]}, indent=2), encoding="utf-8")

    source_dir = repo_root / "add scam img"
    source_dir.mkdir()
    source_image = source_dir / "new_image.jpg"
    create_checker_test_image(source_image, color1=(255, 0, 0), color2=(0, 0, 255))

    monkeypatch.setattr(add_scam_img, "GLOBAL_IMAGES_DIR", str(global_images_dir))
    monkeypatch.setattr(add_scam_img, "GLOBAL_HASHES_PATH", str(global_hashes_path))

    added, skipped = add_scam_img.add_images_from_folder(str(source_dir), warning_threshold=add_scam_img.DEFAULT_WARNING_THRESHOLD)

    assert added == [("new_image.jpg", "2.jpg")]
    assert skipped == []
    assert not source_image.exists()
    assert (global_images_dir / "2.jpg").exists()
