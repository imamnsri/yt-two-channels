
import json
import os

# Required GitHub Actions secrets
REQUIRED_SECRETS = [
    "VICE_CITY_TOKEN",
    "KIDZZ_RHYTHM_TOKEN",
    "YOUTUBE_CLIENT_SECRET",
]


def main():
    print("================================")
    print(" YouTube Automation Setup Check")
    print("================================")

    missing = []

    for name in REQUIRED_SECRETS:
        value = os.environ.get(name)

        if not value:
            print(f"[MISSING] {name}")
            missing.append(name)
            continue

        try:
            data = json.loads(value)

            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object")

            print(f"[OK] {name}")

        except (json.JSONDecodeError, ValueError):
            print(f"[INVALID JSON] {name}")
            missing.append(name)

    print("--------------------------------")

    if missing:
        print("Setup check failed.")
        print("Missing or invalid secrets:", len(missing))
        raise SystemExit(1)

    print("SUCCESS!")
    print("Both YouTube channel credentials")
    print("are available for automation.")


if __name__ == "__main__":
    main()
