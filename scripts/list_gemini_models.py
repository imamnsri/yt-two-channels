
import os
import json
import urllib.request
import urllib.error

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing")

url = "https://generativelanguage.googleapis.com/v1beta/models"

request = urllib.request.Request(
    url,
    headers={"x-goog-api-key": api_key}
)

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)

    print("Available Gemini text-generation models:")

    for model in data.get("models", []):
        methods = model.get("supportedGenerationMethods", [])

        if "generateContent" in methods:
            print(model["name"])

except urllib.error.HTTPError as error:
    print(f"Gemini API error: HTTP {error.code}")
    raise SystemExit(1)
