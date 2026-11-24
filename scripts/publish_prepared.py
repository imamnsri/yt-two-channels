"""Upload checked original media at the configured Eastern release time."""
import datetime as dt
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import requests
from googleapiclient.http import MediaFileUpload
from daily import ROOT, HISTORY, CHANNELS, EASTERN, youtube, existing_upload, write_json, persist

def sources(entry):
    urls = entry.get('source_urls', [entry.get('source_url')])
    if not isinstance(urls, list) or not 1 <= len(urls) <= 10:
        raise ValueError('Expected one to ten video sources')
    for url in urls:
        source = urlparse(url or '')
        if source.scheme != 'https' or source.hostname != 'gcdn.picsart.com':
            raise ValueError('Source must be a Picsart HTTPS asset')
    return urls

def probe_video(path):
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
    if not {'audio', 'video'} <= {s['codec_type'] for s in probe['streams']}:
        raise RuntimeError('Video must have audio and picture')
    return float(probe['format']['duration'])

def assemble(parts, video):
    if len(parts) == 1:
        parts[0].replace(video)
        return
    inputs, filters, streams = [], [], []
    for i, part in enumerate(parts):
        length = probe_video(part)
        inputs += ['-i', str(part)]
        filters += [f'[{i}:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,setpts=PTS-STARTPTS[v{i}]', f'[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,asetpts=PTS-STARTPTS,afade=t=in:d=0.08,afade=t=out:st={max(0,length-0.08)}:d=0.08[a{i}]']
        streams += [f'[v{i}][a{i}]']
    filters.append(''.join(streams) + f'concat=n={len(parts)}:v=1:a=1[v][a]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(filters), '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(video)], check=True)

def validate(entry):
    if entry['channel'] != 'kidz' or not entry.get('quality_checked'):
        raise ValueError('Only checked kids media is supported')
    sources(entry)
    when = dt.datetime.fromisoformat(entry['publish_at'].replace('Z', '+00:00'))
    local = when.astimezone(EASTERN)
    expected = CHANNELS['kidz']['weekend_time'] if local.weekday() >= 5 else CHANNELS['kidz']['slots'][0][1]
    if local.strftime('%H:%M') != expected or local.second:
        raise ValueError('Release differs from configured Eastern schedule')
    if not entry['id'].replace('-', '').isalnum():
        raise ValueError('Invalid release ID')
    return when

def publish(entry):
    when = validate(entry)
    receipt_path = HISTORY / ('prepared-' + entry['id'] + '.json')
    if receipt_path.exists():
        print('SKIP prepared: receipt exists', flush=True)
        return
    service, channel = youtube(entry['channel'])
    marker = 'Prepared release: ' + entry['id']
    recovered = existing_upload(service, channel, marker)
    if recovered:
        write_json(receipt_path, {'video_id': recovered, 'recovered': True, 'publish_at': entry['publish_at']})
        persist()
        print('RECOVERED https://youtu.be/' + recovered, flush=True)
        return
    if when <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5):
        raise RuntimeError('Publishing slot missed; refusing to silently change date')
    with tempfile.TemporaryDirectory() as directory:
        video = Path(directory) / 'video.mp4'
        parts = []
        for i, url in enumerate(sources(entry)):
            part = Path(directory) / f'part-{i}.mp4'
            with requests.get(url, stream=True, timeout=90, allow_redirects=False) as response:
                if response.status_code != 200:
                    raise RuntimeError('Prepared media HTTP ' + str(response.status_code))
                with part.open('wb') as output:
                    for chunk in response.iter_content(1024*1024):
                        output.write(chunk)
                        if output.tell() > 100*1024*1024:
                            raise RuntimeError('Video exceeds 100 MB')
            probe_video(part)
            parts.append(part)
        assemble(parts, video)
        length = probe_video(video)
        if abs(length-entry['duration_seconds']) > 1:
            raise RuntimeError('Video duration differs from checked asset')
        body = {'snippet': {'title': entry['title'], 'description': entry['description'] + '\n\n' + marker, 'categoryId': CHANNELS['kidz']['category'], 'defaultLanguage': 'en', 'defaultAudioLanguage': 'en-US'}, 'status': {'privacyStatus': 'private', 'publishAt': entry['publish_at'], 'selfDeclaredMadeForKids': True}}
        result = service.videos().insert(part='snippet,status', body=body, media_body=MediaFileUpload(str(video), chunksize=8*1024*1024, resumable=True)).execute()
        receipt = {'video_id': result['id'], 'title': entry['title'], 'publish_at': entry['publish_at'], 'source_sha256': hashlib.sha256(video.read_bytes()).hexdigest(), 'duration_seconds': length, 'mode': 'live', 'made_for_kids': True, 'kind': entry.get('kind', 'original animated song'), 'source_count': len(parts)}
        write_json(receipt_path, receipt)
        persist()
        confirmed = service.videos().list(part='status', id=result['id']).execute()['items'][0]['status']
        receipt['youtube_status'] = confirmed
        write_json(receipt_path, receipt)
        persist()
        print('OK kidz prepared: https://youtu.be/' + result['id'], flush=True)
        print('YOUTUBE_STATUS ' + json.dumps(confirmed), flush=True)

if __name__ == '__main__':
    try:
        for entry in json.loads((ROOT/'config/prepared_releases.json').read_text()):
            publish(entry)
    except Exception as error:
        print('FAIL prepared: ' + (str(error) if type(error) in (ValueError, RuntimeError) else type(error).__name__), flush=True)
        raise SystemExit(1)
