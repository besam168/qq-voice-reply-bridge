from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from providers.tts_edge import synthesize_sync as edge_synthesize_sync


def configure_utf8_console() -> None:
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def emit_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8-sig"))


def normalize_text(text: str, config: Dict[str, Any]) -> str:
    normalized = str(text).strip()
    if not normalized:
        raise ValueError("Input text is empty after trimming")

    max_text_length = int((config.get("tts") or {}).get("max_text_length", 4000))
    if max_text_length > 0 and len(normalized) > max_text_length:
        raise ValueError(f"Input text is too long ({len(normalized)} > {max_text_length})")
    return normalized


def resolve_repo_path(value: str | None, *, base_dir: Path, default: str) -> Path:
    raw = str(value or default).strip()
    path = Path(raw)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def resolve_output_dir(config: Dict[str, Any], config_path: Path) -> Path:
    output_dir = resolve_repo_path(
        (config.get("tts") or {}).get("output_dir"),
        base_dir=config_path.parent,
        default="./output",
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def resolve_output_extension(config: Dict[str, Any]) -> str:
    extension = str((config.get("tts") or {}).get("output_ext", "wav")).strip().lower().lstrip(".")
    if not extension:
        extension = "wav"
    if extension != "wav":
        raise ValueError("Only wav output is supported by this QQ voice reply bridge")
    return extension


def synthesize_audio(*, text: str, config: Dict[str, Any], config_path: Path) -> Path:
    tts = config.get("tts") or {}
    provider_name = str(tts.get("provider", "edge")).strip().lower()
    if provider_name != "edge":
        raise ValueError("Only tts.provider='edge' is supported")

    output_dir = resolve_output_dir(config, config_path)
    extension = resolve_output_extension(config)
    filename = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid4().hex[:8] + "." + extension
    audio_path = output_dir / filename

    edge_synthesize_sync(
        text=text,
        output_path=audio_path,
        voice=str(tts.get("voice", "zh-CN-XiaoxiaoNeural")),
        rate=str(tts.get("rate", "+0%")),
    )
    return audio_path.resolve()


def play_audio(*, audio_path: Path, config: Dict[str, Any], config_path: Path) -> Dict[str, Any]:
    playback = config.get("playback") or {}
    player_script = resolve_repo_path(
        playback.get("player_script"),
        base_dir=config_path.parent,
        default="./scripts/play-local-audio.ps1",
    )
    if not player_script.exists():
        raise FileNotFoundError(f"Playback script not found: {player_script}")

    timeout_seconds = int(playback.get("timeout_seconds", 20))
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(player_script),
        "-AudioPath",
        str(audio_path),
        "-TimeoutSeconds",
        str(timeout_seconds),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        raise RuntimeError(
            "Local playback failed. "
            f"stderr: {stderr or 'No stderr output'}; stdout: {stdout or 'No stdout output'}"
        )

    lines = [line.strip() for line in (completed.stdout or "").splitlines() if line.strip()]
    return {"ok": True, "output": lines}


def speak(*, text: str, config: Dict[str, Any], config_path: Path, no_play: bool = False) -> Dict[str, Any]:
    normalized_text = normalize_text(text, config)
    audio_path = synthesize_audio(text=normalized_text, config=config, config_path=config_path)

    playback_cfg = config.get("playback") or {}
    playback_enabled = bool(playback_cfg.get("enabled", True)) and not no_play
    playback_result: Dict[str, Any] | None = None
    if playback_enabled:
        playback_result = play_audio(audio_path=audio_path, config=config, config_path=config_path)

    return {
        "ok": True,
        "text": normalized_text,
        "audio_path": str(audio_path),
        "played": playback_enabled,
        "playback_result": playback_result,
    }


def main() -> None:
    configure_utf8_console()
    parser = argparse.ArgumentParser(description="Generate a QQ-sendable WAV voice reply from text.")
    parser.add_argument("text", help="Text to speak")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[1] / "config.json"),
        help="Path to config JSON file",
    )
    parser.add_argument("--no-play", action="store_true", help="Generate audio without local speaker playback")
    args = parser.parse_args()

    try:
        config_path = Path(args.config).resolve()
        config = load_config(config_path)
        result = speak(text=args.text, config=config, config_path=config_path, no_play=args.no_play)
        emit_json(result)
    except Exception as exc:
        emit_json({"ok": False, "error": str(exc)})
        raise SystemExit(1)


if __name__ == "__main__":
    main()
