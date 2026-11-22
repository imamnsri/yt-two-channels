"""Run on YOUR PC. OAuth tokens go directly to GitHub secrets, never to chat."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'config/channels.json').read_text())
REPO='imamnsri/yt-two-channels'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--channel',choices=['all',*CONFIG],default='all')
    parser.add_argument('--client-file',type=Path,default=ROOT/'client_secret.json')
    args=parser.parse_args()
    if not args.client_file.is_file():
        raise SystemExit('Put your downloaded Desktop OAuth client_secret.json in the project root, or supply --client-file PATH. Never upload it to chat or Git.')
    if not shutil.which('gh'):
        raise SystemExit('Install GitHub CLI on this PC first: https://cli.github.com/')
    subprocess.run(['gh','auth','status'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print('Before continuing: your OAuth app must be In production, and YouTube Data API v3 must be enabled.')
    for key in CONFIG if args.channel=='all' else [args.channel]:
        config=CONFIG[key]
        scopes=['https://www.googleapis.com/auth/youtube.upload','https://www.googleapis.com/auth/youtube.readonly']
        if key=='vicecity':
            scopes.append('https://www.googleapis.com/auth/youtube.force-ssl')
        print(f"\nChoose YOUR channel: {config.get('authorization_name', config['name'])}")
        if key=='vicecity':
            print('This consent includes permission to add our first comments to our GTA videos.')
        input('Press Enter to open Google sign-in on this PC...')
        flow=InstalledAppFlow.from_client_secrets_file(str(args.client_file),scopes=scopes)
        credentials=flow.run_local_server(host='localhost',port=0,open_browser=True,
            authorization_prompt_message='Opening Google sign-in...',
            access_type='offline',prompt='consent select_account')
        service=build('youtube','v3',credentials=credentials,cache_discovery=False)
        items=service.channels().list(part='snippet',mine=True).execute().get('items',[])
        if len(items)!=1:
            raise SystemExit('Expected exactly one YouTube channel; nothing saved.')
        channel=items[0]
        print(f"Selected channel: {channel['snippet']['title']} ({channel['id']})")
        expected=config.get('channel_id')
        if (expected and channel['id']!=expected) or (not expected and channel['snippet']['title'].casefold()!=config.get('authorization_name', config['name']).casefold()):
            raise SystemExit('Wrong channel selected. Nothing saved; run again and choose the correct channel.')
        if not credentials.refresh_token:
            raise SystemExit('No refresh token returned. Nothing saved. Check existing app access in your Google account before retrying.')
        if input(f"Type YES to update {config['token_secret']} for this channel: ").strip().upper()!='YES':
            print('Skipped; nothing saved.')
            continue
        data={'client_id':credentials.client_id,'client_secret':credentials.client_secret,
              'refresh_token':credentials.refresh_token,'token_uri':'https://oauth2.googleapis.com/token','scopes':scopes}
        serialized=json.dumps(data)
        # gh receives values only on stdin, not as command-line args or visible terminal text.
        subprocess.run(['gh','secret','set',config['token_secret'],'--repo',REPO],input=serialized,text=True,check=True)
        print(f"Updated {config['token_secret']} securely. No token printed or saved to a project file.")
    print('\nFinished. Tell your assistant the update is done; do not send any credentials.')

if __name__=='__main__':
    main()
