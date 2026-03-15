# aternos4ever

Keeps your Aternos Minecraft server alive by automatically clicking the extend button before it shuts down due to inactivity.

## How it works

Aternos starts a countdown when no players are online. When ~1 minute remains a `+` button appears — if you don't click it the server stops. This script opens Firefox on your server panel and clicks that button automatically whenever it shows up.

## Requirements

- Python 3.12+
- Firefox

```
pip install selenium webdriver-manager
```

## Setup

1. Open `script.py` and set `SERVER_URL` to your server panel URL (e.g. `https://aternos.org/server/`)
2. Make sure you are logged into Aternos in your **normal Firefox profile** — the script reuses it so no login is needed

## Usage

```
python script.py
```

Firefox will open on your server panel. The script checks for the extend button every 10 seconds and clicks it automatically.

Press `Ctrl+C` to stop.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `SERVER_URL` | `https://aternos.org/server/` | Your Aternos server panel URL |
| `CHECK_EVERY` | `10` | Seconds between button checks |

## Notes

- Close your normal Firefox before running, or it may conflict with the profile lock
- If the button stops being detected, right-click it in the browser → Inspect and check the selector in `EXTEND_SELECTORS`
