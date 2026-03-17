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

---

## Contributing

Contributions are welcome. Here's how to get started.

### Reporting a broken selector

Aternos updates their frontend regularly, which can break the CSS/XPath selectors used to find buttons. If something stops working:

1. Open your browser DevTools (`F12`) on the Aternos server panel
2. Inspect the element that the script should be clicking
3. Open an issue and paste the full HTML of that element (e.g. `<button id="..." class="...">`)

### Submitting a fix or feature

1. Fork the repository and create a branch from `master`
2. Keep changes focused — one fix or feature per pull request
3. Test manually by running `script.py` against a real Aternos server session
4. Open a pull request with a short description of what changed and why

### Adding a new automation step

All automation steps live in `script.py`'s main loop. The pattern to follow:

1. Add a selector constant near the top of the file alongside the existing ones (e.g. `MY_BUTTON_SELECTOR`)
2. If it needs iframe-switching, add a dedicated function like `dismiss_safeframe_ad()`; otherwise `_click_first_visible()` handles it
3. Add a numbered step in the `while True` loop in `main()` with a `print` log line
4. Update the relevant selector list or add a new one with a comment explaining when the element appears

### Code style

- Plain Python — no type hints required, no extra dependencies beyond `selenium` and `webdriver-manager`
- Keep selector lists as constants at the top so they are easy to update without reading the logic
- Log every automated action with a timestamp using `time.strftime('%H:%M:%S')`
