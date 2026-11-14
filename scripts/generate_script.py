
import os
import json
import sys
import urllib.request
import urllib.error

API_KEY = os.environ.get("GEMINI_API_KEY")

CHANNELS = {
    "vice_city": {
        "name": "Vice City - Unlocked",
        "instructions": (
            "Write original GTA 6 commentary for a US audience. "
            "Only present officially confirmed Rockstar Games "
            "information as fact. Never invent news, release dates, "
            "gameplay features, or announcements. "
            "If official sources are not provided, create evergreen "
            "opinion-based commentary clearly labeled as opinion. "
            "Do not copy Rockstar footage or copyrighted scripts."
        ),
    },
    "kidzz_rhythm": {
        "name": "Kidzz Rhythm",
        "instructions": (
            "Create completely original nursery rhymes and "
            "musical stories for young children. "
            "Use simple US English, repetition, and positive "
            "educational themes. Do not copy copyrighted lyrics."
        ),
    },
}


def generate(channel, video_type):
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing")

    if channel not in CHANNELS:
        raise ValueError("Unknown channel")

    if video_type not in ("short", "long"):
        raise ValueError("Invalid video type")

    target_words = 110 if video_type == "short" else 650

    prompt = f"""
You are creating an original YouTube script.

Channel: {CHANNELS[channel]['name']}
Video type: {video_type}
Target narration: approximately {target_words} words

Requirements:
{CHANNELS[channel]['instructions']}

Return ONLY a valid JSON object with:
"title": YouTube title
"description": YouTube description
"narration": complete narration
"visual_keywords": array of 5 stock-video search terms

Use US English.
"""

    model = os.environ.get(
        "GEMINI_MODEL", "gemini-2.5-flash-lite"
    )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model}:generateContent"
    )

    payload = json.dumps({
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        },
    }).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=90
        ) as response:
            result = json.load(response)

    except urllib.error.HTTPError as error:
        print(
            f"Gemini API HTTP error: {error.code}",
            file=sys.stderr,
        )

        error_body = error.read().decode(
            "utf-8", errors="replace"
        )

        try:
            details = json.loads(error_body)
            message = details.get("error", {}).get(
                "message", "No error details provided"
            )
            print(
                f"Gemini error details: {message}",
                file=sys.stderr,
            )
        except json.JSONDecodeError:
            print(
                "Gemini returned a non-JSON error response.",
                file=sys.stderr,
            )

        raise SystemExit(1)

    text = result["candidates"][0]["content"]["parts"][0]["text"]
    content = json.loads(text)

    required = [
        "title",
        "description",
        "narration",
        "visual_keywords",
    ]

    if any(key not in content for key in required):
        raise ValueError("Gemini returned incomplete content")

    os.makedirs("output", exist_ok=True)

    filename = f"output/{channel}_{video_type}.json"

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(
            content,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Script generated: {filename}")
    print(f"Title: {content['title']}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python scripts/generate_script.py "
            "<channel> <short|long>"
        )
        sys.exit(1)

    generate(sys.argv[1], sys.argv[2])
