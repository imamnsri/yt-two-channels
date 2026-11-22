"""Check each actual Google token independently, without logging secret values."""
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError
from daily import CHANNELS, youtube


def main():
    failed=[]
    for key in CHANNELS:
        try:
            service,channel=youtube(key)
            scopes=channel.pop('_scopes',[])
            print(f"OK channel {key}: {channel['snippet']['title']} ({channel['id']})")
            can_comment=any(s.endswith('/youtube.force-ssl') or s.endswith('/youtube') for s in scopes)
            print(f"Comment permission {key}: {'available' if can_comment else 'not present'}")
        except RefreshError:
            print(f'FAIL {key}: Google token expired/revoked or cannot refresh. Reauthorize this channel locally.')
            failed.append(key)
        except HttpError as error:
            print(f'FAIL {key}: YouTube API HTTP {error.resp.status}. Check API enablement and permissions.')
            failed.append(key)
        except Exception as error:
            print(f'FAIL {key}: {str(error) if isinstance(error,RuntimeError) else type(error).__name__}')
            failed.append(key)
    if failed:
        raise SystemExit(1)
    print('Preflight succeeded: token refresh and channel identities verified. Uploads still need testing.')

if __name__=='__main__':
    main()
