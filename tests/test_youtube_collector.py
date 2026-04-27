import json
import pytest
from unittest.mock import MagicMock, patch
from collectors.youtube_collector import YouTubeCollector


@pytest.fixture
def mock_youtube_service():
    service = MagicMock()
    service.channels().list().execute.return_value = {
        "items": [{
            "id": "UC123",
            "snippet": {"title": "GrowKwik", "description": "D2C growth channel"},
            "statistics": {"subscriberCount": "50000", "viewCount": "2000000"}
        }]
    }
    service.search().list().execute.return_value = {
        "items": [{"id": {"videoId": "vid001"}}, {"id": {"videoId": "vid002"}}],
        "nextPageToken": None
    }
    service.videos().list().execute.return_value = {
        "items": [{
            "id": "vid001",
            "snippet": {
                "title": "GoKwik Install Guide",
                "description": "How to install GoKwik on Shopify",
                "publishedAt": "2024-03-01T10:00:00Z",
                "tags": ["gokwik", "shopify"]
            },
            "statistics": {"viewCount": "10000", "likeCount": "500", "commentCount": "80"}
        }]
    }
    service.commentThreads().list().execute.return_value = {
        "items": [{
            "snippet": {
                "topLevelComment": {
                    "snippet": {
                        "authorDisplayName": "d2c_founder",
                        "textDisplay": "How do I get started?",
                        "likeCount": 2
                    }
                }
            }
        }],
        "nextPageToken": None
    }
    return service


def test_fetch_channel_meta(mock_youtube_service, tmp_path):
    collector = YouTubeCollector(service=mock_youtube_service, output_dir=str(tmp_path))
    meta = collector.fetch_channel_meta("UC123")
    assert meta["id"] == "UC123"
    assert meta["statistics"]["subscriberCount"] == "50000"


def test_fetch_video_ids(mock_youtube_service, tmp_path):
    collector = YouTubeCollector(service=mock_youtube_service, output_dir=str(tmp_path))
    ids = collector.fetch_all_video_ids("UC123")
    assert "vid001" in ids


def test_fetch_comments(mock_youtube_service, tmp_path):
    collector = YouTubeCollector(service=mock_youtube_service, output_dir=str(tmp_path))
    comments = collector.fetch_comments("vid001", max_comments=100)
    assert len(comments) == 1
    assert comments[0]["author"] == "d2c_founder"
    assert comments[0]["text"] == "How do I get started?"
