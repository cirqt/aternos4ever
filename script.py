"""
Aternos keep-alive — browser automation script.

How it works:
  - Opens a Chrome window and navigates to your Aternos server panel
  - Gives you 90 seconds to log in (skipped if already logged in)
  - Watches for the countdown extend button ("+" / "Keepalive") that appears
    when the server is about to shut down due to inactivity
  - Clicks it automatically whenever it appears

Requirements:
  pip install selenium webdriver-manager

Usage:
  c:/python312/python.exe script.py
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.firefox import GeckoDriverManager

# ── CONFIG ────────────────────────────────────────────────────────────────────
SERVER_URL   = "https://aternos.org/server/"   # your server panel
CHECK_EVERY  = 10   # seconds between button checks
LOGIN_WAIT   = 90   # seconds to log in before automation starts
# ──────────────────────────────────────────────────────────────────────────────

# Selectors to try for the keep-alive extend button, in priority order.
# Aternos uses Angular custom elements — update these if clicking stops working.
EXTEND_SELECTORS = [
    (By.XPATH, "//*[contains(@class,'countdown')]//button"),
]

def find_extend_button(driver):
    """Return the extend button element if visible, else None."""
    for by, selector in EXTEND_SELECTORS:
        try:
            el = driver.find_element(by, selector)
            if el.is_displayed():
                return el
        except NoSuchElementException:
            pass
    return None

def main():
    print("Starting Firefox...")
    service = Service(GeckoDriverManager().install())
    options = webdriver.FirefoxOptions()

    # Use your real Firefox profile so Aternos sees you as already logged in
    profile_path = os.path.join(os.environ["APPDATA"], r"Mozilla\Firefox\Profiles\l3oe4zey.default-release")
    options.add_argument("-profile")
    options.add_argument(profile_path)
    options.add_argument("--no-remote")  # allow new instance even if Firefox is already open

    driver = webdriver.Firefox(service=service, options=options)
    driver.maximize_window()
    driver.get(SERVER_URL)

    # Wait for the user to log in if needed
    print(f"\nIf you are not already logged in, do so now. "
          f"You have {LOGIN_WAIT} seconds...\n")
    try:
        WebDriverWait(driver, LOGIN_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".server-name, .servername, [class*='server']"))
        )
        print("Server panel detected. Starting keep-alive loop.\n")
    except TimeoutException:
        print("Timed out waiting for login — continuing anyway.\n")

    print(f"Watching for extend button every {CHECK_EVERY}s. Press Ctrl+C to stop.\n")

    while True:
        try:
            btn = find_extend_button(driver)
            if btn:
                btn.click()
                print(f"[{time.strftime('%H:%M:%S')}] Extend button found and clicked!")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] No extend button visible — server is fine.")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Error: {e}")

        time.sleep(CHECK_EVERY)

if __name__ == "__main__":
    main()
