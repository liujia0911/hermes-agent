#!/usr/bin/env python3
"""Hybrid Vision Analysis: send screenshot to Gemini 3 Flash for desktop automation guidance.

Usage:
  python3 hybrid_vision_analyze.py <image_b64_file> "<prompt>"
  python3 hybrid_vision_analyze.py /tmp/screenshot-b64.txt "点击新对话按钮，返回元素索引"

Reads Gemini API config from ~/.hermes/profiles/vision/config.yaml
Outputs Gemini's text response to stdout.
"""

import yaml, urllib.request, json, base64, sys, os

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 hybrid_vision_analyze.py <b64_file> <prompt>")
        sys.exit(1)

    b64_file = sys.argv[1]
    prompt = sys.argv[2]

    # Load vision profile config
    config_path = os.path.expanduser('~/.hermes/profiles/vision/config.yaml')
    if not os.path.exists(config_path):
        print(f"ERROR: vision profile config not found at {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    key = config['inference']['api_key']
    model = config['model']
    base = config['inference']['base_url']

    # Load image
    with open(b64_file) as f:
        img_b64 = f.read().strip()

    if not img_b64:
        print("ERROR: empty base64 image file")
        sys.exit(1)

    # Build request
    url = f'{base}/models/{model}:generateContent?key={key}'
    body = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inlineData": {"mimeType": "image/png", "data": img_b64}}
            ]
        }]
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json'}
    )

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        text = data['candidates'][0]['content']['parts'][0]['text']
        print(text)
    except urllib.error.HTTPError as e:
        print(f"API Error {e.code}: {e.read().decode()[:500]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
