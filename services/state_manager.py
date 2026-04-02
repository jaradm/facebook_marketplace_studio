import json
from pathlib import Path
from typing import Any, Dict, List

from config import STATE_FILE
from models import ProductListing


def save_state(payload: Dict[str, Any]) -> None:
    Path(STATE_FILE).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_state() -> Dict[str, Any] | None:
    state_path = Path(STATE_FILE)
    if not state_path.exists():
        return None
    return json.loads(state_path.read_text(encoding="utf-8"))


def products_from_state(items: List[dict]) -> List[ProductListing]:
    return [ProductListing(**item) for item in items]
