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

import atexit
import os
import shutil
import tempfile
import time
from collections import deque
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

# The green Start button shown when the server is offline.
START_BUTTON_SELECTOR = (By.CSS_SELECTOR, "button#start.btn-success")

# Selectors for the green "Okay" button on the "This is currently not possible" popup.
OKAY_CLOSE_SELECTORS = [
    (By.CSS_SELECTOR, "button.btn.btn-green"),          # green Okay button
    (By.XPATH, "//button[normalize-space()='Okay']"),   # text fallback
]

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

def make_driver() -> webdriver.Firefox:
    """Create and return a new Firefox WebDriver pointed at SERVER_URL."""
    print("Starting Firefox...")
    service = Service(GeckoDriverManager().install())
    options = webdriver.FirefoxOptions()

    # Use your real Firefox profile so Aternos sees you as already logged in.
    # Copy it to a temp dir so it works even when Firefox is already running.
    _profiles_dir = os.path.join(os.environ["APPDATA"], r"Mozilla\Firefox\Profiles")
    _profile_name = next(
        (p for p in os.listdir(_profiles_dir) if p.endswith(".default-release")),
        None,
    )
    if _profile_name is None:
        print("ERROR: Could not find a Firefox profile ending in '.default-release'.")
        print(f"Profiles found in {_profiles_dir}:")
        for p in os.listdir(_profiles_dir):
            print(f"  {p}")
        raise RuntimeError("No default-release Firefox profile found.")
    src_profile = os.path.join(_profiles_dir, _profile_name)
    tmp_dir = tempfile.mkdtemp(prefix="aternos_ff_profile_")
    profile_path = os.path.join(tmp_dir, "profile")
    print(f"Copying Firefox profile to {profile_path} ...")
    shutil.copytree(src_profile, profile_path, ignore_dangling_symlinks=True)
    # Remove the lock files so Firefox doesn't think the profile is already open
    for lock_file in ("lock", ".parentlock"):
        lf = os.path.join(profile_path, lock_file)
        if os.path.exists(lf):
            os.remove(lf)
    atexit.register(shutil.rmtree, tmp_dir, True)  # clean up on exit
    options.add_argument("-profile")
    options.add_argument(profile_path)
    options.add_argument("--no-remote")

    driver = webdriver.Firefox(service=service, options=options)
    driver.maximize_window()
    driver.get(SERVER_URL)
    return driver


def main():
    driver = make_driver()

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

    recent_log: deque = deque(maxlen=10)  # rolling window of last 10 log entries

    while True:
        try:
            # 0. Verify we are still on the correct server panel URL.
            #    Aternos sometimes redirects /server/ → /servers/ after a refresh.
            current_url = driver.current_url
            if current_url.rstrip("/") != SERVER_URL.rstrip("/"):
                print(f"[{time.strftime('%H:%M:%S')}] URL drifted to {current_url!r} — navigating back to {SERVER_URL!r}.")
                driver.get(SERVER_URL)
                time.sleep(3)
                # If we're still not on the right page, restart the browser entirely.
                if driver.current_url.rstrip("/") != SERVER_URL.rstrip("/"):
                    print(f"[{time.strftime('%H:%M:%S')}] Redirect failed — reopening Firefox from scratch.")
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    time.sleep(2)
                    driver = make_driver()
                    time.sleep(3)
                    continue

            # 1. Dismiss "This is currently not possible" popup FIRST — it sits on
            #    top of everything and will block all other clicks if left open.
            for by, sel in OKAY_CLOSE_SELECTORS:
                try:
                    el = driver.find_element(by, sel)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                        print(f"[{time.strftime('%H:%M:%S')}] 'Not possible' popup dismissed (Okay clicked).")
                        break
                except NoSuchElementException:
                    pass

            # 2. Dismiss adblock warning if present
            label = _click_first_visible(driver, ADBLOCK_SELECTORS)
            if label:
                msg = "adblock"
                recent_log.append(msg)
                print(f"[{time.strftime('%H:%M:%S')}] Adblock warning dismissed. ('{label}')")
                if recent_log.count(msg) > 3:
                    print(f"[{time.strftime('%H:%M:%S')}] Adblock warning stuck — refreshing page.")
                    recent_log.clear()
                    driver.refresh()
                    time.sleep(3)
            else:
                recent_log.append("ok")

            # 3. Dismiss Google safeframe ad (iframe-based)
            if dismiss_safeframe_ad(driver):
                print(f"[{time.strftime('%H:%M:%S')}] Safeframe ad closed.")

            # 4. Dismiss other ad overlays if present
            label = _click_first_visible(driver, AD_SELECTORS)
            if label:
                print(f"[{time.strftime('%H:%M:%S')}] Ad dismissed. ('{label}')")

            # 5. Click "Confirm now!" if queue confirmation is required
            label = _click_first_visible(driver, CONFIRM_NOW_SELECTORS)
            if label:
                print(f"[{time.strftime('%H:%M:%S')}] Queue confirmation clicked.")

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
