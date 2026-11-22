"""Check saved credentials against YouTube without exposing credentials."""
import json
from daily import CHANNELS, youtube

def main():
    for key, config in CHANNELS.items():
        yt, channel = youtube(key)
        scopes = channel.pop('_scopes', [])
        print(f"OK channel {key}: {channel['snippet']['title']} ({channel['id']})")
        can_comment = any(s.endswith('/youtube.force-ssl') or s.endswith('/youtube') for s in scopes)
        print(f"Comment permission {key}: {'available' if can_comment else 'not present'}")
    print('Preflight succeeded. This verifies token refresh and channel identity, not uploads.')

if __name__ == '__main__':
    main()
