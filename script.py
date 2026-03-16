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

# "Continue with adblocker anyway" button.
# Uses a compound XPath so we hit the actual button div, not an ancestor container.
ADBLOCK_SELECTORS = [
    (By.XPATH, "//div[contains(@class,'btn') and contains(@class,'btn-white') and contains(.,'Continue with adblocker')]"),
    (By.XPATH, "//div[contains(@class,'btn-white') and .//i[contains(@class,'fa-sad-tear')]]")
]

# Selectors for the "action not possible" / error popup that blocks extend.
# Aternos shows various flavours — we cast a wide net on text content.
ACTION_NOT_POSSIBLE_SELECTORS = [
    (By.XPATH, "//*[contains(text(),'not possible')]"),
    (By.XPATH, "//*[contains(text(),'not available')]"),
    (By.XPATH, "//*[contains(text(),'cannot')]"),
    (By.XPATH, "//*[contains(@class,'alert') and contains(@class,'error')]"),
    (By.XPATH, "//*[contains(@class,'notification') and contains(@class,'error')]"),
    (By.XPATH, "//*[contains(@class,'modal') and .//*[contains(text(),'not')]]"),
]

# The green Start button shown when the server is offline.
START_BUTTON_SELECTOR = (By.CSS_SELECTOR, "button#start.btn-success")

# "Okay" dismiss button on the "This is currently not possible" popup.
OKAY_BUTTON_SELECTOR = (By.CSS_SELECTOR, "button.btn.btn-green")

# "Confirm now!" button shown in queue to confirm you're still waiting.
CONFIRM_NOW_SELECTORS = [
    (By.CSS_SELECTOR, "button#confirm.btn-success"),           # exact element
    (By.XPATH, "//button[contains(normalize-space(),'Confirm now')]"),  # text fallback
]

# Ad overlay / modal close selectors — update if one starts matching.
AD_SELECTORS = [
    (By.CSS_SELECTOR, ".modal-close"),
    (By.CSS_SELECTOR, ".ad-close"),
    (By.CSS_SELECTOR, "[class*='ad-'] button.close"),
    (By.CSS_SELECTOR, "[class*='advertisement'] .close"),
    (By.XPATH, "//button[@aria-label='Close']"),
    (By.XPATH, "//*[contains(@class,'ad')]//button[contains(@class,'close')]"),
]

def dismiss_safeframe_ad(driver):
    """Switch into Google safeframe ad iframes and click the Close button."""
    try:
        iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[title='3rd party ad content']")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                close = driver.find_element(
                    By.XPATH,
                    "//button[normalize-space()='Close'] | //*[normalize-space()='Close']"
                )
                if close.is_displayed():
                    try:
                        close.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", close)
                    return True
            except NoSuchElementException:
                pass
            finally:
                driver.switch_to.default_content()
    except Exception:
        driver.switch_to.default_content()
    return False


def _click_first_visible(driver, selectors):
    """Try each selector, click the first visible match. Return label if clicked."""
    for by, selector in selectors:
        try:
            el = driver.find_element(by, selector)
            if el.is_displayed():
                try:
                    el.click()          # normal click
                except Exception:
                    driver.execute_script("arguments[0].click();", el)  # JS fallback
                return selector
        except NoSuchElementException:
            pass
    return None

def check_action_not_possible(driver):
    """Return True if an 'action not possible' style popup/alert is visible."""
    for by, selector in ACTION_NOT_POSSIBLE_SELECTORS:
        try:
            el = driver.find_element(by, selector)
            if el.is_displayed():
                return True
        except NoSuchElementException:
            pass
    return False


def try_start_server(driver):
    """Click the Start button if it is visible. Return True if clicked."""
    by, selector = START_BUTTON_SELECTOR
    try:
        btn = driver.find_element(by, selector)
        if btn.is_displayed() and btn.is_enabled():
            try:
                btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", btn)
            return True
    except NoSuchElementException:
        pass
    return False


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
            # 1. Dismiss adblock warning if present
            label = _click_first_visible(driver, ADBLOCK_SELECTORS)
            if label:
                print(f"[{time.strftime('%H:%M:%S')}] Adblock warning dismissed. ('{label}')")

            # 2. Dismiss Google safeframe ad (iframe-based)
            if dismiss_safeframe_ad(driver):
                print(f"[{time.strftime('%H:%M:%S')}] Safeframe ad closed.")

            # 3. Dismiss other ad overlays if present
            label = _click_first_visible(driver, AD_SELECTORS)
            if label:
                print(f"[{time.strftime('%H:%M:%S')}] Ad dismissed. ('{label}')")

            # 5. Click "Confirm now!" if queue confirmation is required
            label = _click_first_visible(driver, CONFIRM_NOW_SELECTORS)
            if label:
                print(f"[{time.strftime('%H:%M:%S')}] Queue confirmation clicked.")

            if check_action_not_possible(driver):
                print(f"[{time.strftime('%H:%M:%S')}] 'Action not possible' popup detected — dismissing...")
                by, sel = OKAY_BUTTON_SELECTOR
                try:
                    okay = driver.find_element(by, sel)
                    if okay.is_displayed():
                        try:
                            okay.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", okay)
                        print(f"[{time.strftime('%H:%M:%S')}] Popup dismissed (Okay clicked).")
                except NoSuchElementException:
                    pass

            # 6. Click Start button whenever it's visible (server is offline)
            if try_start_server(driver):
                print(f"[{time.strftime('%H:%M:%S')}] Server was offline — Start button clicked.")
                time.sleep(5)  # give the page a moment to react
            else:
                # 7. Click extend button if countdown appeared
                btn = find_extend_button(driver)
                if btn:
                    btn.click()
                    print(f"[{time.strftime('%H:%M:%S')}] Extend button clicked!")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] OK — no action needed.")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Error: {e}")

        time.sleep(CHECK_EVERY)

if __name__ == "__main__":
    main()
