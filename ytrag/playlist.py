import logging
from pathlib import Path
from typing import Optional
import yt_dlp

from ytrag.config import settings
from ytrag.models import Video

logger = logging.getLogger("ytrag.playlist")


def list_playlist(playlist_url: str) -> list[Video]:
    """Extract all available videos and their metadata from a YouTube playlist URL.
    
    Uses flat extraction so full video pages are not fetched during listing.
    """
    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
    }

    videos: list[Video] = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        if not info:
            logger.warning(f"Could not extract playlist information from: {playlist_url}")
            return []

        playlist_id = info.get("id")
        entries = info.get("entries") or []

        for entry in entries:
            if not entry:
                continue

            video_id = entry.get("id")
            title = entry.get("title")
            duration = entry.get("duration")

            # Skip entries without valid ID or title (e.g. deleted/private videos)
            if not video_id or not title:
                continue
            if title in ["[Deleted video]", "[Private video]"]:
                logger.info(f"Skipping unavailable video: {video_id} ({title})")
                continue

            videos.append(
                Video(
                    video_id=video_id,
                    title=title,
                    duration=int(duration) if duration is not None else 0,
                    playlist_id=playlist_id,
                )
            )

    logger.info(f"Extracted {len(videos)} valid videos from playlist.")
    return videos


def extract_single_video(video_url_or_id: str) -> Video:
    """Extract metadata for a single video by URL or ID."""
    url = (
        video_url_or_id
        if video_url_or_id.startswith("http")
        else f"https://www.youtube.com/watch?v={video_url_or_id}"
    )
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError(f"Could not fetch metadata for video: {video_url_or_id}")
        return Video(
            video_id=info["id"],
            title=info.get("title", f"Video {info['id']}"),
            duration=int(info.get("duration", 0)),
        )


def download_audio(video: Video, force: bool = False) -> Path:
    """Download audio stream for a given video into the configured audio directory.
    
    Downloads native audio (preferring m4a) to avoid requiring external FFmpeg transcoding.
    Skips downloading if audio file already exists and force is False.
    """
    audio_dir = settings.audio_dir
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Check existing audio files for this video_id
    existing_files = list(audio_dir.glob(f"{video.video_id}.*"))
    if existing_files and not force:
        # Return first existing audio file if valid size
        target = existing_files[0]
        if target.stat().st_size > 0:
            logger.info(f"Using cached audio: {target.name}")
            return target

    # yt-dlp template targeting video_id.%(ext)s
    outtmpl = str(audio_dir / f"{video.video_id}.%(ext)s")

    ydl_opts = {
        # Prefer native m4a audio stream directly from YouTube
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "fragment_retries": 3,
        "ignoreerrors": False,
    }

    url = f"https://www.youtube.com/watch?v={video.video_id}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Find the downloaded file
    matching_files = list(audio_dir.glob(f"{video.video_id}.*"))
    if not matching_files:
        raise FileNotFoundError(f"Audio download failed for video {video.video_id} ({video.title})")

    downloaded = matching_files[0]
    logger.info(f"Downloaded audio to {downloaded}")
    return downloaded
