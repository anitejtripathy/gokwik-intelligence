#!/usr/bin/env python3
"""
run.py — Full pipeline orchestrator for GoKwik Social Intelligence

Usage:
  python run.py

Reads from .env:
  YOUTUBE_API_KEY, ANTHROPIC_API_KEY,
  GROWKWIK_YOUTUBE_CHANNEL_ID, GROWKWIK_INSTAGRAM_USERNAME, VARUN_MAYA_VIDEO_ID
Usage:
  python run.py              # full pipeline
  python run.py --analyze    # skip collection, run Stage 2+3 on existing raw data
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from collectors.youtube_collector import YouTubeCollector
from collectors.instagram_collector import InstagramCollector
from collectors.normalizer import save_normalized, load_normalized
from collectors.schema import normalize_youtube_video
from agents.agency_model_agent import AgencyModelAgent
from agents.content_theme_agent import ContentThemeAgent
from agents.audience_intelligence_agent import AudienceIntelligenceAgent
from agents.gokwik_benefits_agent import GoKwikBenefitsAgent
from agents.engagement_agent import EngagementAgent
from report_generator import ReportGenerator
from site_generator import SiteGenerator

AGENT_OUTPUT_DIR = Path("data/normalized")
AGENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_json(data: dict, filename: str):
    path = AGENT_OUTPUT_DIR / filename
    path.write_text(json.dumps(data, indent=2))
    print(f"[run] Saved {filename}")


def stage1_collect():
    print("\n=== STAGE 1: DATA COLLECTION ===")
    yt_collector = YouTubeCollector(
        api_key=os.environ["YOUTUBE_API_KEY"],
        output_dir="data/raw/youtube"
    )
    ig_collector = InstagramCollector(
        username=os.environ["GROWKWIK_INSTAGRAM_USERNAME"],
        output_dir="data/raw/instagram"
    )

    print("[Stage 1] Collecting GrowKwik YouTube (Varun Maya agency)...")
    growkwik_items = yt_collector.collect_all(os.environ["GROWKWIK_YOUTUBE_CHANNEL_ID"], channel_label="growkwik")

    print("[Stage 1] Collecting GoKwik YouTube (brand channel)...")
    gokwik_items = yt_collector.collect_all(os.environ["GOKWIK_YOUTUBE_CHANNEL_ID"], channel_label="gokwik")

    yt_items = growkwik_items + gokwik_items

    print("[Stage 1] Collecting Instagram...")
    ig_items = ig_collector.collect_all()

    all_items = yt_items + ig_items
    save_normalized(all_items, str(AGENT_OUTPUT_DIR / "content_items.json"))
    print(f"[Stage 1] Total items collected: {len(all_items)}")
    return all_items


def stage2_analyze(content_items):
    print("\n=== STAGE 2: CLAUDE AGENT ANALYSIS ===")
    raw_items = [item.to_dict() for item in content_items]

    # Serial: Agency Model Agent first
    print("[Stage 2] Running AgencyModelAgent (serial)...")
    varun_maya_id = os.environ.get("VARUN_MAYA_VIDEO_ID", "")
    varun_transcript = ""
    if varun_maya_id:
        t_path = Path(f"data/raw/youtube/transcripts/{varun_maya_id}.txt")
        if t_path.exists():
            varun_transcript = t_path.read_text()
        else:
            print(f"[Stage 2] Varun Maya transcript not found at {t_path}, proceeding without it")

    all_transcripts = [
        item.get("transcript", "") or ""
        for item in raw_items
        if item.get("platform") == "youtube" and item.get("transcript")
    ]

    agency_agent = AgencyModelAgent()
    agency_context = agency_agent.run(
        transcripts=all_transcripts,
        varun_maya_transcript=varun_transcript
    )
    save_json(agency_context, "agency_context.json")

    # Parallel batch 1: content-theme + audience-intelligence
    print("[Stage 2] Running ContentThemeAgent + AudienceIntelligenceAgent (parallel)...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        theme_future = executor.submit(
            ContentThemeAgent().run,
            content_items=raw_items,
            agency_context=agency_context
        )
        audience_future = executor.submit(
            AudienceIntelligenceAgent().run,
            content_items=raw_items
        )
    content_themes = theme_future.result()
    audience_profile = audience_future.result()
    save_json(content_themes, "content_themes.json")
    save_json(audience_profile, "audience_profile.json")

    # Parallel batch 2: gokwik-benefits + engagement
    print("[Stage 2] Running GoKwikBenefitsAgent + EngagementAgent (parallel)...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        benefits_future = executor.submit(
            GoKwikBenefitsAgent().run,
            agency_context=agency_context,
            content_themes=content_themes,
            audience_profile=audience_profile
        )
        engagement_future = executor.submit(
            EngagementAgent().run,
            content_items=raw_items,
            content_themes=content_themes
        )
    gokwik_value_map = benefits_future.result()
    engagement_stats = engagement_future.result()
    save_json(gokwik_value_map, "gokwik_value_map.json")
    save_json(engagement_stats, "engagement_stats.json")

    return agency_context, content_themes, audience_profile, gokwik_value_map, engagement_stats


def stage3_report(agency_context, content_themes, audience_profile, gokwik_value_map, engagement_stats):
    print("\n=== STAGE 3: REPORT + SITE GENERATION ===")
    gen = ReportGenerator(output_dir="output")
    gen.generate_brief(
        agency_context=agency_context,
        content_themes=content_themes,
        audience_profile=audience_profile,
        gokwik_value_map=gokwik_value_map,
        engagement_stats=engagement_stats
    )
    gen.generate_data_tables(
        agency_context=agency_context,
        content_themes=content_themes,
        audience_profile=audience_profile,
        gokwik_value_map=gokwik_value_map,
        engagement_stats=engagement_stats
    )
    SiteGenerator(
        agent_output_dir=str(AGENT_OUTPUT_DIR),
        site_data_dir="site/data"
    ).generate()
    print("\n[run] Pipeline complete!")
    print("  Brief:       output/brief.md")
    print("  Data tables: output/data-tables.md")
    print("  Site:        site/index.html (open locally or deploy to GitHub Pages)")


def load_from_raw() -> list:
    """Build content items from existing raw video JSON files, skipping API calls."""
    print("\n=== STAGE 1: LOADING FROM EXISTING RAW DATA ===")
    all_items = []
    raw_dir = Path("data/raw/youtube")
    comments_dir = raw_dir / "comments"
    transcripts_dir = raw_dir / "transcripts"

    for channel_label in ["growkwik", "gokwik"]:
        videos_path = raw_dir / f"{channel_label}_videos.json"
        if not videos_path.exists():
            print(f"[load] No raw data for {channel_label}, skipping")
            continue
        videos = json.loads(videos_path.read_text())
        print(f"[load] {channel_label}: {len(videos)} videos")
        for video in videos:
            vid_id = video.get("id", "")
            comments_path = comments_dir / f"{vid_id}.json"
            transcript_path = transcripts_dir / f"{vid_id}.txt"
            comments = json.loads(comments_path.read_text()) if comments_path.exists() else []
            transcript = transcript_path.read_text() if transcript_path.exists() else None
            item = normalize_youtube_video(video, comments, transcript, source_channel=channel_label)
            all_items.append(item)

    save_normalized(all_items, str(AGENT_OUTPUT_DIR / "content_items.json"))
    print(f"[load] Total items: {len(all_items)}")
    return all_items


if __name__ == "__main__":
    if "--analyze" in sys.argv:
        items = load_from_raw()
    else:
        items = stage1_collect()
    agency_context, content_themes, audience_profile, gokwik_value_map, engagement_stats = stage2_analyze(items)
    stage3_report(agency_context, content_themes, audience_profile, gokwik_value_map, engagement_stats)
