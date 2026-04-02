import re
from pathlib import Path
from typing import List

from config import SUPPORTED_IMAGE_EXTS
from services.utils import slug_token


def find_matching_images(item_number: str, images_dir: Path) -> List[str]:
    key = slug_token(item_number)
    matches: list[Path] = []

    for path in images_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_IMAGE_EXTS:
            continue
        stem = slug_token(path.stem)
        if stem == key:
            matches.append(path)
            continue
        if stem.startswith(key):
            tail = stem[len(key):]
            if tail == "" or tail.isdigit():
                matches.append(path)

    def sort_key(p: Path):
        nums = re.findall(r"(\d+)", p.stem)
        return (p.stem.lower(), int(nums[-1]) if nums else 0)

    return [str(p.resolve()) for p in sorted(matches, key=sort_key)]
