# Browser, Tooling & Native Recovery Playbook

## 1. Browser: BrowserOS Neo Only

Use BrowserOS Neo for all web work. It is the user's real browser profile with live logins. It runs batched `run` scripts and the `scripts/neo/` helpers, uploads files straight into page inputs (`setFiles`), and has a password manager (`credentials`). Don't switch to another browser.

## 2. When Neo Fails: Check, Debug, Fix

1. **Check**: Is the BrowserOS app running with a real browser window? A background `browseros-claw-server` process alone isn't enough. Does the Neo MCP answer `tabs` with action `list`?
2. **Debug**: Read the error and retry the call once. For a stuck or broken tab, open a new tab rather than restarting the browser.
3. **Not installed**: Tell the user and ask them to install BrowserOS Neo. Wait for them.
4. **Installed but closed, frozen, or erroring**: Use OS computer use to open BrowserOS or fix it (relaunch the app, dismiss its dialog). Close the OS session, then continue in Neo.
5. Don't close BrowserOS windows that hold active sessions just to clear one stuck tab.

## 3. OS Computer Use: Windows Outside the Browser

Use OS computer use whenever a specific task needs OS-level control. Typical tasks:
- Opening, relaunching, or fixing BrowserOS Neo.
- Native windows a page can't reach: file pickers, "Leave site?" prompts, popup windows outside Neo.
- Any other app's window the task needs.

**It works per window, not on the whole desktop**: list the open windows, pick the one target window, then capture or act on that window. Re-list after anything changes; never reuse old coordinates or element indexes.

**Rule**: name the task, do it at OS level, and **close the OS computer-use session as soon as that task is complete**. Then continue with Neo. Web-page work stays in Neo. If no OS computer-use tool is ready, ask the user to do that one step.

### Which tool provides it

| Agent | OS computer use available when | Not available when |
| --- | --- | --- |
| **Codex (default)** | Codex CLI is signed in, the **Codex desktop app is running**, and the computer-use plugin's config paths match the installed app version | The app is closed (the CLI has no computer-use engine of its own), or the app was updated and not reopened, which leaves the config pointing at a deleted folder |
| **Claude** | The session runs inside the Claude desktop app with Computer use turned on (Settings) | Claude Code CLI in a terminal, even with the desktop app open |

`render.py tools --live` checks all of this and runs a read-only Codex window test (list windows, capture one). On Windows the Codex app's process is named `ChatGPT`; detect it by its install folder (`OpenAI.Codex_*`), not by name. After a Codex update, opening the app rewrites the computer-use paths in `~/.codex/config.toml` within seconds.

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

## 6. Portal Accounts & Credentials

You are allowed to create new accounts on job portals for the user.

1. **Reuse first**: before creating an account, check `<workspace_dir>/credentials.md` and the browser's saved passwords (BrowserOS Neo: `credentials` action `list` with `query` set to the site). Workday tenants are per-company, so an account at one employer does not cover another.
2. **Create**: use the email from `profile.md` as the username unless the portal requires something else. Complete any email verification the portal sends.
3. **Save in `credentials.md`**: right after creating the account, add a row with the employer, ATS platform, login URL, username/email, password, creation date, and notes. Update the row when something changes (password reset, email verified, roles applied for).
4. **Save in the browser's password manager** so autofill works when the user signs in without the agent:
   - BrowserOS Neo: `credentials` with `action: "add"`, the login page's `page` id, `username`, and `password` (inside `run`: `browser.page(id).credentials({ action: 'add', ... })`). Confirm with `action: "list"`.
   - Other browsers: accept the browser's "Save password?" prompt, or add the entry in its password settings.
5. **Sign in later**: in Neo, use `credentials` with `action: "fill"` and the saved `credentialId`, or fill from `credentials.md`.
