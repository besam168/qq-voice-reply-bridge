from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from pathlib import Path


FALLBACK_FFMPEG_CANDIDATES = [
    Path(r"C:\Users\winsam\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"),
    Path(r"C:\Users\winsam\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"),
]


def resolve_ffmpeg() -> str | None:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    for candidate in FALLBACK_FFMPEG_CANDIDATES:
        if candidate.exists():
            return str(candidate)

    for env_path in os.environ.get("PATH", "").split(os.pathsep):
        if not env_path:
            continue
        candidate = Path(env_path) / "ffmpeg.exe"
        if candidate.exists():
            return str(candidate)

    return None


async def synthesize_to_file(*, text: str, output_path: Path, voice: str, rate: str = "+0%") -> Path:
    try:
        import edge_tts  # type: ignore
    except ImportError as exc:
        raise RuntimeError("edge-tts is not installed. Run: pip install -r requirements.txt") from exc

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    target_ext = output_path.suffix.lower()
    if target_ext != ".wav":
        raise ValueError("Only .wav output is supported")

    temp_mp3_path = output_path.with_suffix(".edge-temp.mp3")

    communicator = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicator.save(str(temp_mp3_path))

    ffmpeg_path = resolve_ffmpeg()
    if not ffmpeg_path:
        try:
            temp_mp3_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise RuntimeError("ffmpeg not found in PATH. Install ffmpeg and verify with: ffmpeg -version")

    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(temp_mp3_path),
        "-acodec",
        "pcm_s16le",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        raise RuntimeError(
            "ffmpeg failed to convert edge-tts mp3 to wav. "
            f"stderr: {stderr or 'No stderr output'}; stdout: {stdout or 'No stdout output'}"
        )

    try:
        temp_mp3_path.unlink(missing_ok=True)
    except Exception:
        pass

    return output_path


def synthesize_sync(*, text: str, output_path: Path, voice: str, rate: str = "+0%") -> Path:
    return asyncio.run(synthesize_to_file(text=text, output_path=output_path, voice=voice, rate=rate))

