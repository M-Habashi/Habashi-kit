# Browser, Tooling & Native Recovery Playbook

## 1. Browser Selection: BrowserOS Neo vs Fallbacks

1. **Prefer BrowserOS Neo MCP (Strongly Recommended)**:
   - Persistent real browser profile with active logins (LinkedIn, Workday, iCIMS, email).
   - Supports batched `run` scripts (`scripts/neo/emit.mjs`), CDP DOM inspection/piercing (`setFiles`), and interactive accessibility snapshots.
2. **Fallback Browsers (Chrome / Built-in Browser / Playwright)**:
   - Allowed if BrowserOS Neo MCP is unavailable.
   - **Required notice**: explicitly inform the user upfront that **BrowserOS Neo is strongly recommended** because it keeps live logins, avoids repeated sign-in/CAPTCHA friction, and supports the fast `scripts/neo/` ATS helpers.

## 2. BrowserOS Neo Recovery Rules

When Neo calls fail with connection/tab errors:
1. Check whether the **real browser process** is running — do not assume a background helper process means the browser window is open.
2. If the browser window was closed, relaunch BrowserOS cleanly **without killing running windows or destroying active user sessions**.
3. Never force-kill an active browser session just to clear a single stuck tab; open a new tab or navigate the affected tab instead.

## 3. OS Computer Use (`@oai/sky` + Codex Desktop App)

When available (especially on Codex models with `@oai/sky` and the Codex desktop app running), OS Computer Use may be used **only** for native OS UI that browser automation cannot reach:
- Stubborn native OS file-picker dialogs when CDP/DOM file injection is blocked.
- Native browser prompts like `"Leave site?"` or external OAuth popups outside browser automation control.

### Strict Single-Step Return-to-Browser Boundary
1. **Name the single blocked step** before invoking OS Computer Use (e.g., *"Dismiss native file picker / select CV PDF"*).
2. Perform the **minimum single native action** needed to unblock that step.
3. **Return immediately to browser automation** — never continue filling web forms via OS clicks/typing.
4. **Hard security boundary**: never automate OS password managers, Windows Hello/PIN prompts, keychain unlocks, or OS credential dialogs. Pause and ask the user instead.
5. If OS Computer Use is unavailable, notify the user during Step 1 preflight that any stubborn native OS dialog will pause for a quick human click.

## 4. Embedded ATS & Iframe File-Upload Workarounds

Many ATS portals wrap forms in same-origin iframes or reuse confusing input IDs.

- **Paycor**: Watch out for misleading input IDs — `#uploadResumeInput`, `#transcript`, and `#coverLetter` may map to different visible slots than their IDs suggest, or be hidden behind custom dropzones. Always inspect the surrounding label/container before attaching files.
- **iCIMS**: Forms usually live inside `#icims_content_iframe` (or `iframe[src*="icims.com"]`). Use `setFiles(p, selector, [filePath], { frame: '#icims_content_iframe' })` via CDP (`DOM.getDocument` with `pierce: true`).
- **DOM `DataTransfer` fallback (when CDP file input is unavailable or ignored by JS frameworks)**:
  - Construct a `DataTransfer`, append the `File`, assign `input.files = dt.files`, and dispatch **bubbling** `input` and `change` events (`new Event('input', { bubbles: true })`, `new Event('change', { bubbles: true })`).
- **Never reload a partially filled form** just to retry an upload — you risk wiping every entered field.
- **Visible verification gate**: After uploading, verify the accepted filename appears visibly in the portal UI (or attachment list) before continuing.

## 5. Tab Hygiene

- Group paused/human-action tabs in a **`Needs your input`** tab group (when supported) or list their exact titles/URLs for the user.
- **Never close unfinished, blocked, draft, or unverified tabs.**
- After a submission is verified and logged, close completed confirmation tabs **one at a time**, checking each tab's live URL and title immediately before closing it so an active application tab is never closed by mistake.
