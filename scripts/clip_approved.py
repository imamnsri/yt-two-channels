"""Render a Short from an explicitly licensed, direct MP4 source; never rip YouTube."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
import requests
from daily import ROOT, command


def validate(source):
    if source.get('rights_confirmed') is not True or not source.get('rights_note'):
        raise ValueError('Clip requires documented owner permission or an applicable licence')
    url=source.get('media_url','')
    host=urlparse(url).hostname or ''
    if urlparse(url).scheme!='https' or host in ('youtube.com','www.youtube.com','youtu.be') or host.endswith('.googlevideo.com'):
        raise ValueError('Provide a licensed original MP4 file, not a YouTube download URL')
    start=float(source.get('start_seconds',0))
    end=float(source.get('end_seconds',0))
    if start<0 or not 10<=end-start<=60:
        raise ValueError('Provide a 10-60 second highlight with a non-negative start')
    return url,start,end


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--index',type=int,required=True)
    args=parser.parse_args()
    sources=json.loads((ROOT/'config/approved_clips.json').read_text())
    if not 0<=args.index<len(sources):
        raise SystemExit('No approved clip at this index. Supply rights and direct original media first.')
    url,start,end=validate(sources[args.index])
    folder=ROOT/'output'/'approved-clips'
    folder.mkdir(parents=True,exist_ok=True)
    original=folder/'source.mp4'
    try:
        with requests.get(url,stream=True,timeout=120) as response:
            response.raise_for_status()
            # Never pass an arbitrary remote URL directly to ffmpeg.
            with original.open('wb') as file:
                for chunk in response.iter_content(1024*1024):
                    file.write(chunk)
                    if file.tell()>500*1024*1024:
                        raise RuntimeError('Source exceeds 500 MB; provide a smaller export')
        target=folder/f'clip-{args.index}.mp4'
        command(['ffmpeg','-y','-loglevel','error','-ss',start,'-i',original,'-t',end-start,
                 '-vf','scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1',
                 '-c:v','libx264','-preset','veryfast','-crf','23','-c:a','aac','-movflags','+faststart',target])
        print(f'Approved clip rendered for review: {target.name}. Not uploaded.')
    finally:
        original.unlink(missing_ok=True)

if __name__=='__main__':
    main()
