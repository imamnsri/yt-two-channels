"""Find multi-channel GTA footage candidates using declared CC licensing.

This collects metadata for review. A CC label does not verify that the uploader
owns all underlying footage or music, or establish the absence of facecam.
"""
import datetime as dt
import re
from daily import OUTPUT, write_json, youtube

QUERIES = ['GTA 6 gameplay no commentary', 'GTA VI gameplay no facecam']
EXCLUDE = re.compile(r'\b(trailer|teaser|leak|concept|modded|gta\s*[5v]\b|fan.made)\b', re.I)


def summarize(video):
    snippet = video['snippet']
    published = dt.datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
    hours = max(1, (dt.datetime.now(dt.timezone.utc) - published).total_seconds() / 3600)
    views = int(video.get('statistics', {}).get('viewCount', 0))
    return {
        'video_id': video['id'],
        'url': f"https://www.youtube.com/watch?v={video['id']}",
        'title': snippet['title'],
        'creator': snippet['channelTitle'],
        'channel_id': snippet['channelId'],
        'license': video.get('status', {}).get('license', 'unknown'),
        'published_at': snippet['publishedAt'],
        'duration': video.get('contentDetails', {}).get('duration'),
        'views': views,
        'views_per_hour': round(views / hours, 2),
        'facecam_status': 'needs visual review',
        'game_version_status': 'needs gameplay verification',
        'footage_and_music_rights': 'uploader CC declaration; needs source verification',
        'approved_for_clipping': False,
        'attribution': f"Source: {snippet['title']} by {snippet['channelTitle']} — https://www.youtube.com/watch?v={video['id']}. Declared CC BY: https://creativecommons.org/licenses/by/3.0/ . Edits and commentary must be identified when reused.",
    }


def main():
    service, _ = youtube('vicecity')
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=45)).isoformat().replace('+00:00', 'Z')
    ids = set()
    for query in QUERIES:
        result = service.search().list(
            part='snippet', type='video', q=query, videoLicense='creativeCommon',
            order='viewCount', maxResults=15, publishedAfter=since,
            relevanceLanguage='en', regionCode='US', safeSearch='strict',
        ).execute()
        ids.update(item['id']['videoId'] for item in result.get('items', []))
    candidates = []
    if ids:
        details = service.videos().list(
            part='snippet,statistics,status,contentDetails', id=','.join(sorted(ids)),
        ).execute()
        for video in details.get('items', []):
            if video.get('status', {}).get('license') != 'creativeCommon':
                continue
            if EXCLUDE.search(video['snippet']['title']):
                continue
            candidates.append(summarize(video))
    candidates.sort(key=lambda item: item['views_per_hour'], reverse=True)
    reference = service.videos().list(
        part='snippet,status,statistics,contentDetails', id='7Lt-KTk0tKc',
    ).execute().get('items', [])
    report = {
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'candidates': candidates,
        'reference': [summarize(video) for video in reference],
        'note': 'Research only. No video downloads, clip approvals or uploads performed.',
    }
    write_json(OUTPUT / 'gta_footage_candidates.json', report)
    print(f"CC-declared candidates: {len(candidates)} from {len({v['channel_id'] for v in candidates})} channels")
    for candidate in candidates[:8]:
        print(f"{candidate['views']} views | {candidate['creator']} | {candidate['title']} | {candidate['url']}")
    for item in report['reference']:
        print(f"Reference declared licence: {item['license']} | {item['creator']} | {item['title']}")
    print('Facecam, gameplay version and source rights still require review.')


if __name__ == '__main__':
    main()
