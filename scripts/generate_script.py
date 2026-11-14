
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
            "Create original GTA 6 commentary for a US audience. "
            "Only present officially confirmed Rockstar Games "
            "information as fact. Do not invent announcements, "
            "release dates, features, or gameplay details. "
            "If official source material is not supplied, "
            "create evergreen commentary clearly labeled "
            "as opinion or speculation, not breaking news."
        ),
    },
    "kidzz_rhythm": {
        "name": "Kidzz Rhythm",
        "instructions": (
            "Create an entirely original, age-appropriate "
            "nursery rhyme or musical story for young children. "
            "Use simple English, repetition, positive messages, "
            "and an easy-to-follow narrative. "
            "Do not copy existing copyrighted songs or lyrics."
        ),
    },
}


def generate(channel, video_type):
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing")

    if channel not in CHANNELS:
        raise ValueError("Unknown channel")

    if video_type not in ("short", "long"):
        raise ValueError("Video type must be short or long")

    target_words = 110 if video_type == "short" else 650

    prompt = f"""
You are writing for the YouTube channel:
{CHANNELS[channel]['name']}

Instructions:
{CHANNELS[channel]['instructions']}

Video format: {video_type}
Target narration length: approximately {target_words} words.

Return ONLY valid JSON with these fields:
"title": engaging YouTube title
"description": original YouTube description
"narration": complete spoken script
"visual_keywords": array of 5 safe stock-footage search terms

Use US English. Avoid misleading claims.
"""

    model = os.environ.get(
        "GEMINI_MODEL", "gemini-2.5-flash"
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
        raise

    text = result["candidates"][0]["content"]["parts"][0]["text"]
    content = json.loads(text)

    required = ["title", "description", "narration", "visual_keywords"]
    if any(key not in content for key in required):
        raise ValueError("Gemini returned incomplete content")

    os.makedirs("output", exist_ok=True)

    filename = f"output/{channel}_{video_type}.json"

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(content, file, ensure_ascii=False, indent=2)

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
