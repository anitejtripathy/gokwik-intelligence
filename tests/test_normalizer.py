import json
from pathlib import Path
from collectors.normalizer import save_normalized, load_normalized
from collectors.schema import ContentItem, Engagement, Comment


def _make_item(id: str, platform: str) -> ContentItem:
    return ContentItem(
        id=id, platform=platform, type="video", title="T",
        text="desc", transcript="spoken",
        engagement=Engagement(views=100, likes=10, comments=5, engagement_rate=0.15),
        published_at="2024-01-01T00:00:00Z",
        comments=[Comment(author="u", text="c", likes=1)],
        tags=["a"], url="https://example.com"
    )


def test_save_and_load_normalized(tmp_path):
    items = [_make_item("yt1", "youtube"), _make_item("ig1", "instagram")]
    out_path = tmp_path / "content_items.json"
    save_normalized(items, str(out_path))
    loaded = load_normalized(str(out_path))
    assert len(loaded) == 2
    assert loaded[0]["id"] == "yt1"
    assert loaded[1]["platform"] == "instagram"
