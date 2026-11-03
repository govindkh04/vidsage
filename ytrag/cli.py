import logging
import os
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ytrag.chunk import chunk_segments
from ytrag.config import settings
from ytrag.models import Video, format_timestamp
from ytrag.playlist import download_audio, extract_single_video, list_playlist
from ytrag.transcribe import (
    get_transcript_cache_path,
    load_cached_transcript,
    transcribe,
)

# Configure UTF-8 encoding on Windows to prevent charmap encoding errors
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Setup rich console
console = Console(legacy_windows=False)
app = typer.Typer(
    name="ytrag",
    help="VidSage - AI-Powered YouTube Lecture Search & Revision Assistant",
    add_completion=False,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
# Reduce noisy third-party logging in CLI
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)


@app.command()
def preflight():
    """Verify environment, dependencies, models, and external service credentials."""
    table = Table(title="VidSage Preflight Diagnostics", show_lines=True)
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Details")

    # 1. Python environment
    py_ver = sys.version.split()[0]
    if sys.version_info >= (3, 11) and sys.version_info < (3, 12):
        table.add_row("Python", "[green]OK[/green]", f"Version {py_ver}")
    else:
        table.add_row("Python", "[yellow]WARNING[/yellow]", f"Running on {py_ver} (Python 3.11 recommended)")

    # 2. Whisper & Device
    device = settings.resolved_device
    compute = settings.resolved_compute_type
    table.add_row(
        "Whisper Setup",
        "[green]READY[/green]",
        f"Model: {settings.whisper_model} | Device: {device.upper()} ({compute})",
    )

    # 3. Embedding Model
    table.add_row(
        "Embedding Model",
        "[green]CONFIGURED[/green]",
        f"{settings.embed_model}",
    )

    # 4. Qdrant Connection
    try:
        settings.validate_for_indexing()
        from ytrag.services.qdrant_service import QdrantService
        qs = QdrantService()
        stats = qs.stats()
        table.add_row(
            "Qdrant Cloud",
            "[green]CONNECTED[/green]",
            f"Collection: {stats['collection_name']} | Points: {stats['points_count']}",
        )
    except Exception as e:
        table.add_row("Qdrant Cloud", "[red]FAILED[/red]", str(e))

    # 5. Groq API
    try:
        import groq
        if not settings.groq_api_key:
            table.add_row("Groq API", "[yellow]MISSING KEY[/yellow]", "GROQ_API_KEY is not set in .env")
        else:
            client = groq.Groq(api_key=settings.groq_api_key)
            models = client.models.list()
            table.add_row("Groq API", "[green]CONNECTED[/green]", f"Available models: {len(models.data)}")
    except Exception as e:
        table.add_row("Groq API", "[red]FAILED[/red]", str(e))

    # 6. Local Storage
    table.add_row(
        "Local Storage",
        "[green]READY[/green]",
        f"Root: {settings.root_dir}\nTranscripts: {settings.transcripts_dir}\nAudio: {settings.audio_dir}",
    )

    console.print(table)


@app.command()
def ingest(
    playlist: Optional[str] = typer.Option(None, "--playlist", "-p", help="YouTube Playlist URL"),
    video: Optional[str] = typer.Option(None, "--video", "-v", help="Single YouTube Video URL or ID"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Maximum number of videos to ingest"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Whisper model to use (default: from config)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-download and re-transcription"),
    keep_audio: bool = typer.Option(False, "--keep-audio", help="Keep downloaded audio files after transcription"),
):
    """Ingest lecture videos into VidSage: audio download -> Whisper transcription -> chunking -> Qdrant indexing."""
    if not playlist and not video:
        console.print("[red]Error: Must provide either --playlist or --video URL.[/red]")
        raise typer.Exit(code=1)

    # 1. Fetch videos
    videos: list[Video] = []
    if playlist:
        with console.status(f"[bold cyan]Extracting playlist videos from: {playlist}..."):
            videos = list_playlist(playlist)
    elif video:
        with console.status(f"[bold cyan]Fetching metadata for video: {video}..."):
            videos = [extract_single_video(video)]

    if not videos:
        console.print("[yellow]No valid videos found to process.[/yellow]")
        raise typer.Exit(code=0)

    if limit is not None and limit > 0:
        videos = videos[:limit]

    console.print(Panel(f"Starting ingestion for [bold green]{len(videos)}[/bold green] video(s)"))

    # 2. Process each video
    from ytrag.index import upsert_chunks

    processed_count = 0
    failed_count = 0

    for idx, v in enumerate(videos, start=1):
        console.print(f"\n[bold blue]=== [{idx}/{len(videos)}] Processing: {v.title} ({v.video_id}) ===[/bold blue]")
        try:
            # Check if transcript already cached
            cached = load_cached_transcript(v.video_id)
            if cached and not force:
                console.print(f"[green][+] Cached transcript found ({len(cached)} segments). Skipping audio download.[/green]")
                segments = cached
            else:
                # Step A: Download audio
                with console.status("[yellow]Downloading audio stream...[/yellow]"):
                    audio_path = download_audio(v, force=force)
                console.print(f"[green][+] Audio ready: {audio_path.name} ({audio_path.stat().st_size // 1024} KB)[/green]")

                # Step B: Transcribe audio
                active_model = model or settings.whisper_model
                with console.status(f"[yellow]Transcribing lecture audio with Whisper ({active_model} on {settings.resolved_device}/{settings.resolved_compute_type})...[/yellow]"):
                    segments = transcribe(v, audio_path=audio_path, force=force, model_name=active_model)
                console.print(f"[green][+] Transcribed into {len(segments)} segments[/green]")

                # Step C: Clean temporary audio unless explicitly requested to keep
                if not keep_audio and audio_path.is_file():
                    audio_path.unlink(missing_ok=True)
                    console.print("[dim]Temporary audio file deleted.[/dim]")

            # Step D: Time-based chunking
            chunks = chunk_segments(v, segments)
            console.print(f"[green][+] Created {len(chunks)} timestamped chunks[/green]")

            # Step E: Embed and Upsert to Qdrant
            with console.status("[yellow]Generating dense embeddings and upserting into Qdrant...[/yellow]"):
                upserted = upsert_chunks(chunks)
            console.print(f"[bold green][+] Indexed {upserted} chunks into Qdrant collection '{settings.collection_name}'[/bold green]")
            processed_count += 1

        except Exception as e:
            console.print(f"[bold red][x] Failed processing video {v.video_id}: {e}[/bold red]")
            logging.exception(f"Failure on {v.video_id}")
            failed_count += 1
            # Continue to next video (Section 17 partial failure rule)
            continue

    console.print(
        Panel(
            f"Ingestion Finished!\n"
            f"Successfully processed: [green]{processed_count}[/green]\n"
            f"Failed: [red]{failed_count}[/red]",
            title="Summary",
        )
    )


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question in English or Hinglish (e.g. 'DSA Roadmap me kya bataya gaya hai?')"),
    top_k: Optional[int] = typer.Option(None, "--top-k", "-k", help="Number of retrieved lecture chunks"),
    threshold: Optional[float] = typer.Option(None, "--threshold", "-t", help="Relevance score threshold"),
):
    """Ask a question and receive a grounded answer with clickable lecture timestamps."""
    from ytrag.answer import answer as generate_answer

    console.print(f"\n[bold cyan]Question:[/bold cyan] {question}")

    with console.status("[yellow]Searching lectures & generating grounded answer with Groq...[/yellow]"):
        result = generate_answer(
            question=question,
            top_k=top_k,
            max_distance=threshold,
        )

    # 1. Grounding Status
    if result["grounded"]:
        status_badge = "[bold white on green] GROUNDED ANSWER [/bold white on green]"
    else:
        status_badge = "[bold white on yellow] REFUSAL / UNGROUNDED [/bold white on yellow]"

    console.print(f"\n{status_badge}\n")

    # 2. Answer Text
    console.print(
        Panel(
            result["answer"],
            title="[bold green]VidSage Response[/bold green]",
            border_style="green" if result["grounded"] else "yellow",
        )
    )

    # 3. Citations Table
    citations = result.get("citations", [])
    if citations:
        table = Table(title="Referenced Lecture Citations", show_lines=True)
        table.add_column("Citation", style="bold cyan", width=10)
        table.add_column("Lecture Title", style="cyan", width=30)
        table.add_column("Timestamp", style="green", width=12)
        table.add_column("Lecture Excerpt", style="white")
        table.add_column("Clickable Jump Link", style="bold blue")

        for c in citations:
            excerpt = (c["text"][:150] + "...") if len(c["text"]) > 150 else c["text"]
            table.add_row(
                c["citation_id"],
                c["title"],
                c["timestamp"],
                excerpt,
                c["url"],
            )

        console.print(table)
    else:
        if result["grounded"]:
            console.print("[dim]No specific citation referenced in the response.[/dim]")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (e.g. 'two pointer approach' or Hinglish question)"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of retrieved results"),
    video_id: Optional[str] = typer.Option(None, "--video-id", help="Filter by specific video ID"),
):
    """Retrieve relevant lecture segments from Qdrant without calling the LLM."""
    from ytrag.index import search as qdrant_search

    with console.status(f"[cyan]Searching Qdrant for: '{query}'...[/cyan]"):
        results = qdrant_search(query=query, top_k=top_k, video_id=video_id)

    if not results:
        console.print("[yellow]No relevant lecture chunks found.[/yellow]")
        return

    table = Table(title=f"Search Results for: \"{query}\"", show_lines=True)
    table.add_column("Score", style="magenta", width=8)
    table.add_column("Lecture", style="cyan", width=32)
    table.add_column("Timestamp", style="green", width=12)
    table.add_column("Transcript Excerpt", style="white")
    table.add_column("Action / URL", style="blue")

    for r in results:
        score = f"{r['score']:.3f}"
        title = r["video_title"]
        time_str = f"{format_timestamp(r['start_sec'])} - {format_timestamp(r['end_sec'])}"
        # Strip title prefix from display excerpt for readability
        lines = r["text"].split("\n\n", 1)
        excerpt = lines[1] if len(lines) > 1 else lines[0]
        excerpt_clean = (excerpt[:160] + "...") if len(excerpt) > 160 else excerpt
        url = r["source_url"]

        table.add_row(score, title, time_str, excerpt_clean, url)

    console.print(table)


@app.command()
def stats():
    """Display Qdrant collection indexing statistics."""
    from ytrag.index import stats as qdrant_stats

    try:
        s = qdrant_stats()
        table = Table(title="VidSage Index Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for k, v in s.items():
            table.add_row(str(k), str(v))

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error fetching stats: {e}[/red]")


@app.command(name="eval")
def run_eval(
    golden: Optional[Path] = typer.Option(None, "--golden", "-g", help="Path to golden.json evaluation dataset"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Top-K retrieval limit"),
):
    """Run automated RAG evaluation against the golden dataset (hit rate, refusal accuracy, timestamp error)."""
    from ytrag.evaluate import run_evaluation

    try:
        run_evaluation(golden_path=golden, top_k=top_k)
    except Exception as e:
        console.print(f"[bold red]Evaluation failed: {e}[/bold red]")


@app.command()
def clean_audio():
    """Delete all cached audio files while preserving transcripts."""
    audio_dir = settings.audio_dir
    files = list(audio_dir.glob("*"))
    deleted = 0
    for f in files:
        if f.is_file():
            f.unlink()
            deleted += 1
    console.print(f"[green]Cleaned {deleted} audio files from {audio_dir}. Transcripts remain intact.[/green]")


if __name__ == "__main__":
    app()
