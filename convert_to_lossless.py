#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import tempfile
import subprocess
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# Archive.org のディレクトリ URL
BASE_URL = "https://archive.org/download/nerdcorejcore2/XROGER/[XRSP-01]%20ファック!マルチね☆彡REMIXES/"

def get_mp3_urls(base_url):
    resp = requests.get(base_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return [
        urljoin(base_url, a["href"])
        for a in soup.find_all("a", href=True)
        if a["href"].lower().endswith(".mp3")
    ]

def process_file(url, work_dir, out_dir):
    fname_mp3 = os.path.basename(url)
    base = os.path.splitext(fname_mp3)[0]
    local_mp3 = os.path.join(work_dir, fname_mp3)
    local_wav = os.path.join(work_dir, base + ".wav")

    # ダウンロード
    print(f"Downloading {fname_mp3}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_mp3, "wb") as f:
            for chunk in r.iter_content(1024*1024):
                f.write(chunk)

    # WAV に変換（PCM 16bit/44.1kHz, ステレオ）
    print(f"Converting to WAV: {base}.wav ...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", local_mp3,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        local_wav
    ], check=True)

    os.remove(local_mp3)

    # 出力ディレクトリへ移動
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, os.path.basename(local_wav))
    os.replace(local_wav, dest)
    return dest

def main():
    parser = argparse.ArgumentParser(description="Archive.org の MP3 を WAV(ロスレス)に変換")
    parser.add_argument(
        "-o", "--output-dir",
        default="processed",
        help="変換後ファイルの出力先フォルダ名 (デフォルト: processed)"
    )
    args = parser.parse_args()

    work = tempfile.TemporaryDirectory()
    urls = get_mp3_urls(BASE_URL)
    if not urls:
        print("MP3 が見つかりませんでした。", file=sys.stderr)
        sys.exit(1)

    converted = []
    for url in urls:
        try:
            wav_path = process_file(url, work.name, args.output_dir)
            converted.append(wav_path)
        except Exception as e:
            print(f"Error processing {url}: {e}", file=sys.stderr)

    if converted:
        print(f"Converted {len(converted)} files to '{args.output_dir}'.")
    else:
        print("変換ファイルがありませんでした。", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
