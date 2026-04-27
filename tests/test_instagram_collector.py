import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from collectors.instagram_collector import InstagramCollector


def test_classify_post_type():
    collector = InstagramCollector(username="growkwik", output_dir="/tmp/ig_test")
    assert collector._classify_post_type(is_video=True, media_count=1) == "reel"
    assert collector._classify_post_type(is_video=False, media_count=1) == "image"
    assert collector._classify_post_type(is_video=False, media_count=3) == "carousel"


def test_extract_hashtags():
    collector = InstagramCollector(username="growkwik", output_dir="/tmp/ig_test")
    caption = "Check this out #D2C #ecommerce #gokwik great content"
    tags = collector._extract_hashtags(caption)
    assert "D2C" in tags
    assert "ecommerce" in tags
    assert "gokwik" in tags


def test_build_post_dict():
    collector = InstagramCollector(username="growkwik", output_dir="/tmp/ig_test")
    mock_post = MagicMock()
    mock_post.shortcode = "ABC123"
    mock_post.caption = "Great content #d2c"
    mock_post.is_video = True
    mock_post.video_view_count = 5000
    mock_post.likes = 300
    mock_post.comments = 25
    mock_post.date_utc.isoformat.return_value = "2024-03-01T10:00:00"
    mock_post.url = "https://instagram.com/p/ABC123/"
    type(mock_post).mediacount = PropertyMock(return_value=1)

    result = collector._build_post_dict(mock_post)
    assert result["shortcode"] == "ABC123"
    assert result["typename"] == "GraphVideo"
    assert result["views"] == 5000
    assert "d2c" in result["hashtags"]
