import json
from pathlib import Path
from collectors.schema import ContentItem


def save_normalized(items: list[ContentItem], path: str = "data/normalized/content_items.json"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    data = [item.to_dict() for item in items]
    Path(path).write_text(json.dumps(data, indent=2))
    print(f"[Normalizer] Saved {len(data)} items to {path}")


def load_normalized(path: str = "data/normalized/content_items.json") -> list[dict]:
    p = Path(path)
    if not p.exists():
        print(f"[Normalizer] Warning: {path} not found — returning empty list")
        return []
    return json.loads(p.read_text())
