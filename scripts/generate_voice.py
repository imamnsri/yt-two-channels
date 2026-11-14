
import asyncio
import json
import os
import sys

import edge_tts

VOICES = {
    "vice_city": "en-US-GuyNeural",
    "kidzz_rhythm": "en-US-JennyNeural",
}


async def generate_voice(channel, video_type):
    if channel not in VOICES:
        raise ValueError("Unknown channel")

    if video_type not in ("short", "long"):
        raise ValueError("Invalid video type")

    input_file = f"output/{channel}_{video_type}.json"
    output_file = f"output/{channel}_{video_type}.mp3"

    if not os.path.exists(input_file):
        raise FileNotFoundError(input_file)

    with open(input_file, encoding="utf-8") as file:
        script = json.load(file)

    narration = script.get("narration", "").strip()

    if not narration:
        raise ValueError("Narration is empty")

    voice = VOICES[channel]

    os.makedirs("output", exist_ok=True)

    communicate = edge_tts.Communicate(
        text=narration,
        voice=voice,
        rate="-5%" if channel == "kidzz_rhythm" else "+0%",
    )

    await communicate.save(output_file)

    print(f"Voice generated: {output_file}")
    print(f"Voice used: {voice}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python scripts/generate_voice.py "
            "<channel> <short|long>"
        )
        sys.exit(1)

    asyncio.run(generate_voice(sys.argv[1], sys.argv[2]))
