# QQ Voice Reply Bridge

An OpenClaw skill for generating QQ voice-reply audio files on Windows.

## What this skill does

`qq-voice-reply-bridge` is a small reply-side bridge for direct voice conversations:

- accepts reply text from an agent or workflow
- generates a QQ-sendable `.wav` file using Edge TTS
- optionally plays the generated audio through the local Windows speaker
- returns the absolute audio path for QQBot to send with `<qqmedia>`

This skill does **not** send QQ messages by itself. It only prepares the WAV file that OpenClaw/QQBot can send back to the user.

## Capabilities

- Edge TTS text-to-speech
- WAV output (`pcm_s16le`, mono, `16000 Hz`)
- optional local playback
- JSON result containing the absolute audio path
- QQBot voice reply integration via `<qqmedia>`

## Trigger examples

Use this skill when the user asks for a spoken or voice reply, for example:

- 给我回语音
- 直接语音对话
- 把这句话说出来发给我
- 生成 QQ 语音回复
- 用语音回复我

## Expected OpenClaw flow

1. User sends a QQ voice or text message.
2. ASR converts incoming voice to text if needed.
3. The agent decides the reply content.
4. This skill generates a local WAV file.
5. QQBot sends the file as a voice message:

```xml
<qqmedia file="C:\\absolute\\path\\to\\output.wav" />
```

## Inputs

- `Text`: required text to speak.
- `Config`: optional path to `config.json`.
- `NoPlay`: optional flag to disable local speaker playback.

## Output

The PowerShell/Python entrypoints return UTF-8 JSON. On success:

```json
{
  "ok": true,
  "text": "老板你好。",
  "audio_path": "C:\\...\\output\\xxx.wav",
  "played": true
}
```

On failure:

```json
{
  "ok": false,
  "error": "..."
}
```
