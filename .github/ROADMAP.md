# aternos4ever Development Roadmap (March 2026)

## ✅ Completed Features
- Basic keep-alive script using HTTP requests via `cloudscraper`
- Session cookie configuration
- Periodic ping loop with timestamped console output

## 📋 Future Work

### High Priority

#### Reliable Keep-Alive Endpoint
- **What:** Confirm the exact Aternos endpoint the "I'm still here" button hits
- **Why:** The endpoint may change between Aternos updates
- **How:**
  - Open Aternos in browser → F12 → Network tab
  - Click the keep-alive button and note the exact URL + method + payload
  - Update `KEEPALIVE_URL` in `script.py` accordingly

#### Credential Safety
- **What:** Move cookies out of the source file
- **Why:** Avoid accidental credential exposure if repo is made public
- **How:** Read from environment variables or a local `.env` file (add `.env` to `.gitignore`)

### Medium Priority

- Auto-detect session expiry and log a clear warning
- Retry with backoff on failed requests

### Low Priority

- Desktop notification when the server goes offline
- Config file (`config.json`) instead of hardcoded constants

---

## 🐛 Known Issues

| Issue | Impact | Notes |
|-------|--------|-------|
| Credentials in source file | Medium | Move to `.env` before sharing repo |
| Endpoint URL unverified | Medium | Confirm via DevTools before relying on script |

---

## 📝 Notes

- Follow CLAUDE.md principles: Think Before Coding, Simplicity First, Surgical Changes
- `cloudscraper` handles Cloudflare JS challenges automatically
- Script is intentionally minimal — add complexity only when needed

---

**Last Updated:** March 2026
