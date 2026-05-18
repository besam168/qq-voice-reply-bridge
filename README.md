# qq-voice-reply-bridge

A minimal Windows/OpenClaw bridge that turns reply text into a local `.wav` file suitable for QQ voice replies.

This repository does **not** directly send QQ messages. It only generates a QQ-sendable WAV file. In OpenClaw/QQBot, send the generated file with:

```xml
<qqmedia file="C:\\absolute\\path\\to\\output.wav" />
```

## 1. 项目介绍

`qq-voice-reply-bridge` is a small, public, reusable text-to-speech utility for the reply side of QQ voice conversations.

It is designed for this flow:

1. input reply text
2. generate a `.wav` voice file
3. optionally play the audio on the local Windows speaker
4. return the absolute path
5. let OpenClaw/QQBot send that path as a QQ voice message

## 2. 功能清单

- Edge TTS provider (`edge-tts`)
- WAV output for QQ voice sending
- ffmpeg conversion to `pcm_s16le`, mono, `16000 Hz`
- optional local Windows playback
- UTF-8 JSON output
- OpenClaw/QQBot integration notes

Non-goals:

- no real-time duplex voice call
- no microphone recording or ASR
- no Tmall Genie bridge
- no webhook/callback/HTTP bridge server
- no mock backend
- no cloud control panel
- no automatic OpenClaw/QQBot/ffmpeg installer

## 3. 仓库结构

```text
qq-voice-reply-bridge/
├─ SKILL.md
├─ README.md
├─ LICENSE
├─ requirements.txt
├─ config.example.json
├─ speak-local.ps1
└─ scripts/
   ├─ speak.py
   ├─ play-local-audio.ps1
   └─ providers/
      └─ tts_edge.py
```

Generated audio is written to `./output` by default.

## 4. 系统要求

- Windows 10/11
- PowerShell 5.1+ or PowerShell 7+
- Python 3.10+ recommended
- Internet access for Edge TTS
- `ffmpeg` available in `PATH`
- OpenClaw/QQBot only if you want to send the WAV back to QQ

## 5. 安装步骤

```powershell
git clone https://github.com/besam168/qq-voice-reply-bridge.git
cd qq-voice-reply-bridge
pip install -r requirements.txt
ffmpeg -version
copy config.example.json config.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\speak-local.ps1 -Text "你好，老板。" -NoPlay
```

## 6. ffmpeg 安装与 PATH 说明

Edge TTS generates compressed audio. When `output_ext` is `wav`, this bridge first creates a temporary MP3 and then uses `ffmpeg` to convert it to a QQ-friendly WAV:

- codec: `pcm_s16le`
- channel: mono
- sample rate: `16000 Hz`

Install ffmpeg by any standard Windows method, for example:

- `winget install Gyan.FFmpeg`
- download a Windows build from the official ffmpeg site or gyan.dev

After installing, open a new PowerShell window and check:

```powershell
ffmpeg -version
```

If this command fails, add the folder containing `ffmpeg.exe` to your Windows `PATH`.

## 7. Python 依赖安装

```powershell
pip install -r requirements.txt
```

Required packages:

- `edge-tts`
- `requests`

`requests` is included for compatibility and future lightweight integration use, but the core TTS path only requires `edge-tts` plus system `ffmpeg`.

## 8. 快速开始

Copy the example config:

```powershell
copy config.example.json config.json
```

Generate a WAV without playing it locally:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\speak-local.ps1 -Text "你好，老板。" -NoPlay
```

Expected JSON:

```json
{
  "ok": true,
  "text": "你好，老板。",
  "audio_path": "C:\\...\\qq-voice-reply-bridge\\output\\20260518-121100-xxxxxxxx.wav",
  "played": false
}
```

## 9. 本地播放测试

Run without `-NoPlay`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\speak-local.ps1 -Text "你好，老板。"
```

The script generates the WAV, plays it synchronously through Windows `SoundPlayer`, and returns JSON with `played: true` if playback succeeds.

## 10. OpenClaw 集成说明

This repository is not a message bot. It does not receive QQ events and does not send QQ messages.

Recommended OpenClaw QQBot flow:

1. User sends a QQ voice message.
2. OpenClaw/QQBot or another component runs ASR and gets text.
3. The agent decides the reply text.
4. Run this bridge to generate WAV:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File C:\path\to\qq-voice-reply-bridge\speak-local.ps1 -Text "回复内容" -NoPlay
   ```

5. Parse `audio_path` from the JSON response.
6. Send the path as a QQ voice/media message.

## 11. QQBot 回语音方式

Use the absolute path returned in `audio_path`:

```xml
<qqmedia file="C:\\absolute\\path\\to\\output.wav" />
```

Important notes:

- The `file` value should be an absolute local path accessible to the QQBot process.
- Keep the generated WAV reasonably small.
- Confirm your QQBot/OpenClaw runtime supports sending local media files with `<qqmedia>`.

## 12. 常见故障排查

### 1. `edge-tts is not installed`

Install Python dependencies:

```powershell
pip install -r requirements.txt
```

If you use a virtual environment, make sure `speak-local.ps1 -Python` points to that environment's Python executable.

### 2. `ffmpeg not found in PATH`

Install ffmpeg and verify:

```powershell
ffmpeg -version
```

If it still fails, add the directory containing `ffmpeg.exe` to Windows `PATH`, then restart PowerShell.

### 3. mp3 成功但 wav 转换失败

Check the error message returned by ffmpeg. Common causes:

- broken ffmpeg installation
- output directory is not writable
- antivirus or file lock blocked the output file
- non-ASCII path issues in older shells

Try a short ASCII-only output path, for example `C:\qq-voice-reply-bridge`.

### 4. 本地播放没声音

- Confirm the generated WAV exists.
- Open the WAV manually in Windows Media Player.
- Check Windows output device and volume mixer.
- Try `-NoPlay` to confirm generation succeeds independently from playback.

### 5. QQ 发不出去语音（路径、大小、媒体能力）

- Use the absolute path from `audio_path`, not a relative path.
- Make sure QQBot and this script run on the same machine or can access the same path.
- Check file size and QQBot media limits.
- Confirm your QQBot implementation supports `<qqmedia file="..." />` for local WAV files.
- Make sure the file still exists when QQBot sends it.

## 13. License

MIT License. See [LICENSE](LICENSE).

## Required local acceptance tests

Pure generation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\speak-local.ps1 -Text "测试语音" -NoPlay
```

Local playback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\speak-local.ps1 -Text "测试播放"
```

Chinese stability:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\speak-local.ps1 -Text "老板你好，今天开始语音对话测试。"
```

QQ reply demo in OpenClaw/QQBot:

```xml
<qqmedia file="C:\\absolute\\path\\to\\output.wav" />
```
