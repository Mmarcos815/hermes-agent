#!/usr/bin/env python3
"""
Install mitmproxy CA on Phone-02 via Settings UI using uiautomator2.

Flow:
1. Open Settings > Security & privacy > Device security
2. Find "Install from storage" card (scroll if needed)
3. Tap → wait for system file picker
4. Find mitmproxy-ca-cert.der in /sdcard/Download and tap it
5. Confirm cert name dialog
6. Confirm install warning dialog
7. Verify with adb: check logcat for TrustManager...

Requires: uiautomator2 (pip install uiautomator2), adb bridge to 192.168.1.158:35493
"""
from __future__ import annotations

import logging
import subprocess
import sys
import time

import uiautomator2 as u2

LOG = logging.getLogger("cert-install")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s %(levelname)s] %(message)s",
    stream=sys.stdout,
)

PHONE = "192.168.1.158:35493"
CERT_FILENAME = "mitmproxy-ca-cert.der"

# Screen geometry for vertical scrolling on 1080x2340
SWIPE_X = 540
SWIPE_Y_FROM = 1700
SWIPE_Y_TO = 600


def log(fmt, *args):
    LOG.info(fmt, *args)


def sleep(sec):
    time.sleep(sec)


def find_install_from_storage_card(d, timeout=25):
    """Locate the 'Install from storage' card by text / className / content-desc."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for selector in [
            lambda: d(text="Install from storage"),
            lambda: d(textContains="Install from storage"),
            lambda: d(descriptionContains="Install from storage"),
        ]:
            card = selector()
            if card.exists:
                log("Found Install from storage via %s", selector)
                return card
        # fallback: scan TextViews for the label
        for tv in d(className="android.widget.TextView"):
            txt = (tv.info or {}).get("text") or ""
            if txt.startswith("Install from storage"):
                log("Found Install from storage TextView: %s", txt)
                return tv
        sleep(1)
        log("Scroll tick (looking for Install from storage)")
        d.swipe(SWIPE_X, SWIPE_Y_FROM, SWIPE_X, SWIPE_Y_TO, 0.4)
    return None


def install_from_storage(d):
    card = find_install_from_storage_card(d)
    if card is None:
        log("ERROR: Install from storage card not found; aborting")
        return False
    card.click()
    sleep(1)
    return True


def wait_for_file_picker(d, timeout=30):
    """Wait until the system file picker is on top."""
    deadline = time.time() + timeout
    last_exception = None
    while time.time() < deadline:
        try:
            current = d.app_current()
            pkg = (current.get("package") or "")
            if "filemanager" in pkg or "documentsui" in pkg or "picker" in pkg:
                log("File picker detected: %s/%s", pkg, current.get("activity"))
                return True
            if d(descriptionContains=CERT_FILENAME).exists or d(textContains=CERT_FILENAME).exists:
                log("Cert filename visible in current view")
                return True
        except Exception as e:
            last_exception = e
        sleep(1)
    log(
        "File picker not detected within %ds; current app=%s; last err=%s",
        timeout, d.app_current(), last_exception,
    )
    return False


def tap_cert_in_picker(d, timeout=20):
    """Tap the row that contains our cert filename."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        target = d(textContains=CERT_FILENAME)
        if target.exists:
            target.click()
            log("Tapped cert row: %s", CERT_FILENAME)
            sleep(1)
            return True
        for el in d(className="android.widget.TextView"):
            txt = (el.info or {}).get("text") or ""
            if CERT_FILENAME in txt:
                el.click()
                log("Tapped cert via TextView: %s", txt)
                sleep(1)
                return True
        sleep(1)
    log("ERROR: cert row not found in picker")
    return False


def confirm_install_dialogs(d, timeout=40):
    """Dismiss/confirm the cert-installer warning dialogs."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for positive in ["Install", "OK", "Confirm", "Aceptar", "Done"]:
            btn = d(text=positive)
            if btn.exists:
                btn.click()
                log("Confirmed dialog with '%s'", positive)
                sleep(1)
                break
        else:
            sleep(1)
        top = d.app_current()
        if top.get("package") == "com.android.settings":
            has_dialog = any(d(text=p).exists for p in
                             ["Install", "OK", "Confirm", "Aceptar", "Done", "Cancel"])
            if not has_dialog:
                log("Settings screen back; no more dialogs — install likely complete")
                return True
    log("Timed out waiting for dialogs to clear")
    return False


def verify_trust_via_logcat(d, timeout=30):
    """Ask adb to grep recent TrustManager/TrustedCertificate log lines for our cert."""
    try:
        proc = subprocess.run(
            ["adb", "-s", PHONE, "shell",
             "logcat -d -t 200 2>/dev/null | grep -iE 'TrustManager|TrustedCertificate|trust|SSLContext|Certificate|mitm|UserCA'"],
            capture_output=True, text=True, timeout=30,
        )
        out = proc.stdout or ""
        if out.strip():
            log("logcat trust lines:\n%s", out[:2000])
        else:
            log("No trust-related log lines in last 200 logcat entries")
    except Exception as e:
        log("logcat verification failed: %s", e)
    return out


def run():
    log("Connecting to %s ...", PHONE)
    d = u2.connect(PHONE)
    sleep(2)

    log("Current app before install: %s", d.app_current())
    d.app_stop("com.emeraldmyth.riprush.and")
    sleep(1)

    log("Opening Settings > Security & privacy > Device security ...")
    d.app_start(
        "com.android.settings",
        "com.android.settings.Settings$SecurityAndPrivacySettingsActivity",
    )
    sleep(3)
    if not d.exists:
        log("WARNING: settings activity did not come up; retrying open")
        d.open("am start -a android.settings.SECURITY_SETTINGS")
        sleep(3)

    log("--- Step: find 'Install from storage' ---")
    if not install_from_storage(d):
        return False

    log("--- Step: wait for file picker ---")
    if not wait_for_file_picker(d):
        return False

    log("--- Step: tap cert in picker ---")
    if not tap_cert_in_picker(d):
        return False

    log("--- Step: confirm install dialogs ---")
    if not confirm_install_dialogs(d):
        return False

    log("--- Verifying trust via logcat ---")
    verify_trust_via_logcat(d)

    log("Done")
    return True


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
