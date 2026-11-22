"""Retrieve one CC-declared source excerpt for visual review, without publishing."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from daily import OUTPUT, command, duration, write_json, youtube


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--video-id', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', args.video_id):
        raise SystemExit('Invalid video identifier')
    service, _ = youtube('vicecity')
    videos = service.videos().list(part='snippet,status', id=args.video_id).execute().get('items', [])
    if not videos or videos[0].get('status', {}).get('license') != 'creativeCommon':
        raise SystemExit('This source is not currently declared Creative Commons. No media requested.')
    video = videos[0]
    folder = OUTPUT / 'gameplay-preview'
    folder.mkdir(parents=True, exist_ok=True)
    source = folder / 'source.mp4'
    command_line = [sys.executable, '-m', 'yt_dlp', '--js-runtimes', 'node',
        '--no-playlist', '--no-progress', '--retries', '0', '--extractor-retries', '0',
        '--socket-timeout', '20', '--download-sections', '*00:01:00-00:01:20',
        '-f', 'bv*[height<=720]+ba/b[height<=720]', '--merge-output-format', 'mp4',
        '-o', str(folder / 'source.%(ext)s'), f'https://www.youtube.com/watch?v={args.video_id}']
    process = subprocess.Popen(command_line, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        # Media URLs contain temporary access signatures. Keep them out of logs.
        print(re.sub(r'https?://\S+', '[media URL]', line.rstrip()), flush=True)
    if process.wait() != 0:
        raise SystemExit('Source retrieval failed. No preview created or upload attempted.')
    if not source.is_file() or duration(source) < 5:
        raise SystemExit('Source excerpt is missing or too short')
    preview = folder / 'vertical-review.mp4'
    command(['ffmpeg', '-y', '-loglevel', 'error', '-i', source,
        '-vf', 'scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1',
        '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-movflags', '+faststart', preview])
    write_json(folder / 'source-record.json', {
        'video_id': args.video_id, 'title': video['snippet']['title'],
        'creator': video['snippet']['channelTitle'], 'declared_license': 'creativeCommon',
        'source_start_seconds': 60, 'source_end_seconds': 80,
        'purpose': 'Visual review of gameplay and facecam only. Source audio removed.',
        'approved_for_publication': False,
    })
    print('PREVIEW_OK: 20-second source excerpt and vertical crop are ready for review. No YouTube upload.')


if __name__ == '__main__':
    main()
