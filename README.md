# Two-channel YouTube automation

Channels: **Vice City - Unlocked** and **Kidzz Rhythm**.

## Verified baseline and current implementation

The original Gemini, voice, and Kidzz story tests are preserved. Production code is
`scripts/daily.py`. It researches recent YouTube video metadata, ranks candidates by
views/hour, writes original scripts, generates narration, renders video, uploads,
and saves a receipt immediately after each upload. Re-running the same slot skips
completed uploads. A playlist lookup recovers uploads if a receipt commit was interrupted.

Public publishing times are US Eastern, automatically adjusted for daylight saving:

| Channel | Slot |
|---|---|
| Vice City | Short 12 PM; long 6 PM; Short 9 PM |
| Kidzz Rhythm | Long 3 PM weekdays; 9 AM weekends |

The requested original generation cron **14:17 UTC** remains unchanged. It is too late
for the same day's kids weekend slot. Moving generation earlier needs owner approval.
`AUTOMATION_ENABLED` must be `true` to enable scheduled jobs; manual test runs work
while schedules are disabled. Never enable before verifying successful uploads.

## Secrets

Reuse existing JSON secrets: `VICE_CITY_TOKEN`, `KIDZZ_RHYTHM_TOKEN`,
`YOUTUBE_CLIENT_SECRET`, plus `GEMINI_API_KEY`. Optional `PEXELS_API_KEY` enables stock
footage for GTA; without it, original illustrative city graphics are used and the
run explicitly logs this fallback. Do not commit credentials or provide them in chat.

Set a secret in your own terminal with a hidden prompt:

```
gh secret set PEXELS_API_KEY --repo imamnsri/yt-two-channels
```

`Verify live YouTube connections` refreshes tokens and checks actual channel
identities. `Daily videos` has `channel` (`vicecity`, `kidz`, `all`) and `mode`
(`test`, `live`). Test uploads remain private. Live uploads request `publishAt`;
YouTube's actual visibility restrictions and project approval still apply.
The four expected success lines are `OK vicecity short`, `OK vicecity long`,
`OK vicecity short`, and `OK kidz long`. Skipped/recovered receipts are reported
separately rather than pretending to be new successful uploads.

## Content and honest limitations

* Popular-video research uses titles, views, dates and duration, not downloaded
  competitor footage. A short-duration search finds candidates, not a guaranteed
  list of videos YouTube classifies as Shorts. Popularity is not factual evidence.
* Recent completed GTA livestreams are researched for topics. Their videos are NOT
  automatically downloaded or reused. Live/in-progress streams are not recorded.
* Rockstar pages are requested for evidence. Each declared factual claim requires
  an exact quote from readable official text. Without useful evidence, only clearly
  labelled wishlist commentary is allowed. This is a grounding check, not a guarantee
  that every generated sentence is accurate; review initial scripts/videos.
* GTA Shorts use energetic original narration, illustrative stock or original art.
  No Rockstar footage is included.
* Kidzz production currently creates original SPOKEN STORIES with simple original
  cartoon illustrations and camera motion. This is not character animation or singing.
  Singing vocals and a dependable free singing engine are still pending.
* No external image/music generation service or paid API is silently invoked.
* `generate_music.py` from the prior separate artifact is not integrated; its output
  is instrumental, not singing.

## Comments

The hourly `:37` job checks our GTA videos after they become public and adds one
first question. This may post up to about one hour after publication. It does not
comment on other creators' videos or impersonate viewers. It does not pin comments.
Kids comments are disabled because videos are made for kids.

The existing OAuth tokens may have only upload/read permissions. Posting comments
requires `youtube.force-ssl`; until reauthorization, runs log `COMMENT_PENDING`.
No token is silently broadened and no credentials are exposed.

## Licensed clipping

`config/approved_clips.json` is empty by default. Clipping remains disabled until
approved originals are supplied. `scripts/clip_approved.py --index 0` can render a
10-60 second vertical crop from a licensed direct MP4 export for review. This is a
manual manifest-based clip renderer, NOT an automatic viral-moment detector or an
integrated upload source. It does not rip YouTube streams.

A manifest entry requires `media_url` (direct HTTPS original), `rights_confirmed`:
true, `rights_note`, `start_seconds`, and `end_seconds`. Confirm underlying music and
footage rights as well. Do not put private/signed media links in the public repo.

## Operations

All production runs use GitHub-hosted Ubuntu. Your PC can be off. Standard runners
in public repos are free; API quotas and service availability still apply. Jobs can
be delayed, so generate ahead of publication. GitHub scheduled jobs can be disabled
following extended inactivity. Logs and metadata artifacts expire after seven days;
small upload receipts persist in `history/`. Never store video binaries in Git.

Local checks:

```
python -m pip install -r requirements.txt
python -m unittest discover -s tests
python -m compileall -q scripts
```
