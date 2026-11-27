# Browser, Tooling & Native Recovery Playbook

## 1. Browser: BrowserOS Neo Only

Use BrowserOS Neo for all web work. It is the user's real browser profile with live logins. It runs batched `run` scripts and the `scripts/neo/` helpers, uploads files into page inputs (its `upload` tool, or CDP when the input is hidden, §4), and has a password manager (`credentials`). Don't switch to another browser.

## 2. When Neo Fails: Check, Debug, Fix

1. **Check**: Is the BrowserOS app running with a real browser window? A background `browseros-claw-server` process alone isn't enough. Does the Neo MCP answer `tabs` with action `list`?
2. **Debug**: Read the error and retry the call once. For a stuck or broken tab, open a new tab rather than restarting the browser.
3. **Not installed**: Tell the user and ask them to install BrowserOS Neo. Wait for them.
4. **Installed but closed, frozen, or erroring**: Use the Cua Driver (§3) to open BrowserOS or fix it (relaunch the app, dismiss its dialog). Close the OS session, then continue in Neo.
5. Don't close BrowserOS windows that hold active sessions just to clear one stuck tab.

## 3. Desktop Helper (Cua Driver): Windows Outside the Browser

Required next to BrowserOS Neo: **Cua Driver**, an open-source computer-use driver for Windows, macOS and Linux that any agent can call: https://github.com/trycua/cua (docs: https://cua.ai/docs/cua-driver).

- **Install** (official command from its README): Windows `irm https://cua.ai/driver/install.ps1 | iex`. Check with `cua-driver doctor` and `cua-driver status`.
- **Call it** as an MCP server (`cua-driver mcp`) or from the shell: `cua-driver call <tool> '<json>'`; `cua-driver list-tools` and `cua-driver describe <tool>` show the tools.
- **Use it for**: sign-in pop-ups, native dialogs, other apps' windows, opening or fixing BrowserOS. Web-page work stays in Neo. One window, one step, then back to Neo.

### Neo pop-up windows (e.g. LinkedIn "Authorize")

Neo can't see or click pop-up windows a page opens. Tested steps:
1. `list_windows` before and after your click in Neo; act only in the new window.
2. `bring_to_front` that window, then `get_desktop_state` for a screenshot. A window-only screenshot of a Neo pop-up comes back grey.
3. Click with `click` and `"scope":"desktop"` at the screen position from that screenshot (e.g. Allow).
4. Check the pop-up closed and the page moved on in Neo (Apply with LinkedIn lands on `.../apply/LinkedIn`). Close any pop-up you opened that is still open; never close Neo's main window.

### Native dialogs (file pickers, other apps)

`get_window_state` lists the controls with tokens. Fill a field with `set_value`, then `bring_to_front` and press the button with a desktop-scope `click`. A background click may not commit the dialog.

### Fallback: OS control through PowerShell

If the Cua Driver can't be used, any agent with a shell can act at OS level: find the window (user32 `EnumWindows`), bring it to the front (`SetForegroundWindow`), screenshot it (`System.Drawing` `CopyFromScreen`), then click and type with real input (`SetCursorPos` + `mouse_event`, `SendKeys`). New screenshot after each action.

### Who does the work

- **End to end**: whoever takes a task completes it from start to finish, including pop-ups and OS-level steps. Don't hand part of a task to another agent.
- If you start a helper agent, give it a whole task with its context (one application, one job search), never single clicks. Use reasoning effort high and standard speed unless the user asks otherwise. The helper stops and returns any question only the user can answer; then ask the user yourself.
- **Report**: follow SKILL.md "Reporting a Job" (job card plus a few points). The points end with "Done by <model> (<effort>, <speed>)", adding "sent by <model>" when another agent handed it over. Pass the same to the ledger (`--done-by`, `--sent-by`); the log shows it in a "Done by" column.

## 4. Embedded ATS & Iframe File-Upload Workarounds

Many ATS portals wrap forms in same-origin iframes or reuse confusing input IDs.

- **Paycor**: Watch out for misleading input IDs — `#uploadResumeInput`, `#transcript`, and `#coverLetter` may map to different visible slots than their IDs suggest, or be hidden behind custom dropzones. Always inspect the surrounding label/container before attaching files.
- **iCIMS**: Forms usually live inside `#icims_content_iframe` (or `iframe[src*="icims.com"]`). Use `setFiles(p, selector, [filePath], { frame: '#icims_content_iframe' })` via CDP (`DOM.getDocument` with `pierce: true`).
- **Hidden file input (e.g. Workday "Select files")**: Neo opens no native file dialog, and its `upload` tool can't target a hidden input. Inside `run`, set the file through CDP: `DOM.getDocument`, `DOM.querySelector` for the input (Workday: `input[data-automation-id="file-upload-input-ref"]`), then `DOM.setFileInputFiles` with the full file path.
- **DOM `DataTransfer` fallback (last resort, only when CDP file input is unavailable or ignored by JS frameworks)**:
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
