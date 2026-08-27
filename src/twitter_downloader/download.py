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


class UnfoundException(Exception):
    pass


def get_download_url(twitter_url: str) -> str:
    response = httpx.get(twitter_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    try:
        div = soup.find("div", {"itemprop": "video"})
        if not div:
            raise UnfoundException
        meta = div.find("meta", {"itemprop": "contentUrl"})
        if not meta:
            raise UnfoundException
        download_url = meta.get("content")
        if not download_url:
            raise UnfoundException
        return download_url  # ty: ignore[invalid-return-type]
    except UnfoundException:
        print("No video found!")
        sys.exit(1)


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
        srt_writer = get_writer("srt", temp)
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
