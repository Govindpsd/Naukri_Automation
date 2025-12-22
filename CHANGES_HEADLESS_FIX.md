# Headless Mode Fixes — Summary of Changes

Date: 2025-12-22

## Overview
This document summarizes the code changes made to improve resume-upload reliability when running in headless mode and the small anti-detection tweaks added to the driver. It includes what was changed, why, how to test, and suggested next steps.

## Files Modified

- `workflows/update_resume_flow.py`
- `core/driver_factory.py`
- (Todo list updated via the internal task tracker)

## What I changed (concise)

- Added an iframe- and shadow-DOM-aware file-input finder:
  - `find_file_input(driver, locators, per_locator_timeout=5)` — searches the main document first, then iterates same-origin iframes and tries the provided locators inside each frame. Returns the element and the iframe element (if any).
  - `find_file_input_js(driver)` — JS fallback that searches recursively through DOM, shadow roots and tries same-origin iframes via `execute_script`. Used when the Selenium locators fail.

- Integrated the finder into the upload flow in `UpdateResumeFlow.run()`:
  - Replaced the original direct locator loop with the new helper.
  - If a file input is found inside an iframe, the code switches into that iframe, interacts with the input, then switches back to the default content.
  - Added a safer click fallback (calls `.click()` and falls back to `driver.execute_script('arguments[0].click()')`).
  - Ensured the script makes hidden inputs visible (adjusts styles) and triggers a `change` event after sending the file path.
  - Kept the existing verification (file input `value` check, success-message checks, screenshot capture on failure).

- Added headless anti-detection and usability tweaks to `core/driver_factory.py`:
  - When `Settings.HEADLESS` is true, added flags:
    - `--disable-blink-features=AutomationControlled`
    - a more common desktop `--user-agent` string
  - Injected a small CDP script (`Page.addScriptToEvaluateOnNewDocument`) to define `navigator.webdriver` as `undefined` where supported.

- Fixed a few small locator/string syntax issues encountered while editing.

## Why these changes

- Headless browsers sometimes hide or move DOM elements (or load different markup via A/B tests) and can appear differently to the server. The upload input can be inside an iframe or shadow root, or be dynamically created only after clicking a visible button.
- Searching inside same-origin iframes and exploring shadow DOM increases the chance of finding the actual `input[type=file]` control.
- The anti-detection flags and `navigator.webdriver` override reduce simple bot-detection heuristics that may alter page behavior for headless sessions.

## How to test (run locally)

1. From repository root, run the headless automation:

```bash
HEADLESS=1 python3 main.py
```

2. If the run fails, provide the log excerpt and the screenshot file `upload_error_screenshot.png` (created in the repo root when failures occur). The script also saves `upload_verification_screenshot.png` on verification issues.

3. If the upload succeeds, you should see logs similar to the non-headless run with "✓ File path sent to input field" and "✅ Resume upload verified successfully!".

## Next steps / Suggestions

- Increase timeouts or add network-idle waits in particularly slow environments.
- Optionally add a configurable `Settings.USER_AGENT` so you can vary the UA without code changes.
- Consider using the `selenium-stealth` helper or a headless-stealth Chrome extension for tougher anti-bot checks.
- If the upload input remains hidden, I can add a temporary visual overlay (JS) during test runs to outline discovered inputs and produce a screenshot showing coordinates.

## Patch Summary (high level)

- `workflows/update_resume_flow.py`:
  - New helper functions: `find_file_input`, `find_file_input_js`.
  - Replaced file input search and clicking logic to be iframe-aware, added JS fallback, switched frame context when necessary, persisted prior verification steps.

- `core/driver_factory.py`:
  - Added headless flags and UA; inject CDP script to reduce `navigator.webdriver` visibility.
