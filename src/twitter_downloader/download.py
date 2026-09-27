import re
import sys
import tempfile
from pathlib import Path
from typing import Annotated

import ffmpeg
import httpx
import typer
import whisper
from bs4 import BeautifulSoup
from whisper.utils import get_writer


def find_video_url(soup: BeautifulSoup) -> str | None:
    div = soup.find("div", {"itemprop": "video"})
    if div:
        meta = div.find("meta", {"itemprop": "contentUrl"})
        if meta:
            content = meta.get("content")
            if content:
                return str(content)

    best: tuple[int, str] | None = None
    for script in soup.find_all("script", attrs={"data-tsr-stream-part": True}):
        for block in re.findall(r"\{[^{}]*content_type:\"video/mp4\"[^{}]*\}", script.string or ""):
            bitrate_match = re.search(r"bitrate:(\d+)", block)
            url_match = re.search(r'url:"([^"]+)"', block)
            if url_match:
                bitrate = int(bitrate_match.group(1)) if bitrate_match else 0
                if best is None or bitrate > best[0]:
                    best = (bitrate, url_match.group(1))
    return best[1] if best else None


def get_download_url(twitter_url: str) -> str:
    response = httpx.get(twitter_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    url = find_video_url(soup)
    if not url:
        print("No video found!")
        sys.exit(1)
    return url


def get_video(download_url: str) -> bytes:
    response = httpx.get(download_url)
    response.raise_for_status()
    return response.content


app = typer.Typer()


@app.command()
def download_and_subtitle_tweet(
    twitter_url: str, output_path: Annotated[Path, typer.Option(..., "-o", "--output")]
):
    download_url = get_download_url(twitter_url)
    video = get_video(download_url)
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        with open(temp / "video.mp4", "wb") as file:
            file.write(video)
        model = whisper.load_model("base.en")
        result = model.transcribe(str(temp / "video.mp4"), word_timestamps=True)
        srt_writer = get_writer("srt", str(temp))
        srt_writer(result, str(temp / "video.mp4"))
        ffmpeg.output(
            ffmpeg.input(str(temp / "video.mp4")),
            ffmpeg.input(str(temp / "video.srt")),
            str(output_path),
            vcodec="copy",
            acodec="copy",
            scodec="mov_text",
        ).run()


if __name__ == "__main__":
    app()
