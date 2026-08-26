import os
import sys
import tempfile
from pathlib import Path
from typing import Annotated

import ffmpeg
import httpx
import typer
import whisper
from apify_client import ApifyClient
from dotenv import load_dotenv
from whisper.utils import get_writer


def get_download_url(twitter_url: str) -> str:
    load_dotenv(Path("~/.config/twitter-downloader/.env").expanduser())
    token = os.environ["token"]

    client = ApifyClient(token)

    run_input = {
        "startUrls": [twitter_url],
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
        },
    }

    run = client.actor("zVDlrh34Zwp3735an").call(run_input=run_input)

    if not run:
        print("API client failed")
        sys.exit(1)

    dataset_id = run.default_dataset_id
    dataset_client = client.dataset(dataset_id)

    if len(dataset_client.list_items().items) == 0:
        print("No video found!")
        sys.exit(1)
    return dataset_client.list_items().items[0]["download_url"]


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
