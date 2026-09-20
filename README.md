# Termux Web Builder v2.0

AI-powered web app builder for Termux. Write in Arabic, AI builds your app.

## Features

- Build web apps from Arabic ideas
- 6 color themes
- App list with delete/export/open
- GitHub integration
- Local & free (BYOK)

## Requirements

- Termux
- Python 3.8+
- Node.js 20+
- Groq API key (free): https://console.groq.com/keys

## Install

    pkg update && pkg upgrade -y
    pkg install python nodejs-lts git curl -y

Save your Groq key:

    mkdir -p ~/.secrets
    printf '%s' "gsk_YOUR_KEY" > ~/.secrets/.groq-key
    chmod 600 ~/.secrets/.groq-key

## Run

    python3 web-builder-v2.py

Open: http://localhost:8000

## Usage

1. Write your app idea in Arabic
2. Choose a color
3. Click "Build App"
4. Wait 5-30 seconds
5. Click "Open" to launch

## Examples

- "todo list app" -> Task manager
- "calculator with modern design" -> Calculator
- "notes app" -> Notes

## Architecture

    Browser -> web-builder-v2.py -> Groq API -> Local Files -> Node.js App

## Troubleshooting

### HTTP 403 error 1010
Cloudflare blocks default Python requests. User-Agent is included in the script.

### HTTP 404
Wrong model name. Check available models:

    curl -s https://api.groq.com/openai/v1/models \
      -H "Authorization: Bearer $(cat ~/.secrets/.groq-key)"

### 401 Unauthorized
Wrong API key. Check:

    cat -A ~/.secrets/.groq-key

## Tech Stack

- Python 3
- Groq API (GPT-OSS-120B)
- Node.js + Express

## License

MIT

---

Made with love in Egypt
