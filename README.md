# twitter-downloader

Download Twitter/X videos and embed AI-generated subtitles with Whisper.

## Prerequisites

- **System**: `ffmpeg` (install via your package manager: `brew install ffmpeg`, `apt install ffmpeg`, etc.)
- **Python**: 3.11+ with `uv` or `pip`

## Setup

1. Get an Apify API token from [https://apify.com](https://apify.com)
2. Create `~/.config/twitter-downloader/.env`:
   ```
   token=<YOUR_APIFY_TOKEN>
   ```

## Usage

```bash
download-tweet "https://x.com/..." -o output.mp4
```

The tool downloads the video, transcribes audio with Whisper's `base.en` model, generates subtitles, and muxes them into the output file as an embedded subtitle track.

## Notes

- **Language**: English only (uses `base.en` Whisper model)
- **Subtitles**: Embedded as a `mov_text` subtitle stream (not burned in; can be toggled on/off)
- **Installation as command**: `uv tool install .` or `pip install git+https://github.com/MarkSverdlov/twitter-downloader.git`
