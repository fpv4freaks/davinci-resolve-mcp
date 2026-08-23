---
description: "Check your AI-First Delivery environment setup — CLI tools, VS Code extensions, and MCP servers. Use when: setup check, check setup, environment check, what's missing, am I set up, verify setup, check my tools."
agent: "agent"
---

# AI-First Delivery — Environment Setup Check

First, briefly inform the user what this prompt will do:

> **AI-First Setup Check** — I'll verify your environment by checking **CLI tools** (Git, Node, Python, etc.), **VS Code extensions** (Copilot, ADO Assistant, etc.), and **MCP servers** (Learn, DevOps, WorkIQ, Playwright, etc.). Results will appear as a formatted table with install links for anything missing.

Then detect the operating system and processor architecture:
- **Windows:** run `(Get-CimInstance Win32_Processor).Architecture` — `12` = ARM64, `9` = x64.
- **macOS / Linux:** run `uname -sm` — e.g. `Darwin arm64` (Apple Silicon), `Darwin x86_64` (Intel Mac), `Linux x86_64`.

Prepend the matching note before starting the checks:

> 🔶 **ARM detected** (Windows ARM64 or Apple Silicon). Install commands auto-select the correct architecture — `winget` on Windows, `brew` on macOS. If you download installers manually, always pick the **ARM64 / Apple Silicon** variant (look for the 🔶 icon in the README).

> 🍎 **macOS detected.** Prefer the `brew install …` commands where shown (they work on both Intel and Apple Silicon). Windows-only steps (winget, `%APPDATA%` paths) are adapted or skipped automatically.

Then run all checks below **sequentially** and present results as a single formatted table in chat.
Do NOT ask the user anything before running — just show the brief info above and start checking.

## Checks

### CLI Tools and Runtimes (items 1–9)

Run each command in the terminal to check if it's installed and capture the version. Do NOT run commands in parallel — run one at a time.

| # | Tool | Check command | Required | Setup Guide | Install |
|---|------|--------------|----------|-------------|--------|
| 1 | Git | `git --version` | Yes | [Section 8.1](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#81-install-git-required) | `winget install Git.Git` or [download](https://git-scm.com/download/win) |
| 2 | Node.js | `node --version` | Yes | [Section 8.2](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#82-install-github-cli-gh-required) | `winget install OpenJS.NodeJS.LTS` or [download](https://nodejs.org/en/download) |
| 3 | npx | `npx --version` | Yes | — | *(bundled with Node.js)* |
| 4 | GitHub CLI | `gh --version` | Yes | [Section 8.2](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#82-install-github-cli-gh-required) | `winget install GitHub.cli` or [download](https://cli.github.com) |
| 5 | gh auth | `gh auth status` | Yes | [Section 8.2](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#82-install-github-cli-gh-required) | `gh auth login --hostname github.com --git-protocol https --web` |
| 6 | Pandoc | `pandoc --version` | No | [Section 8.9](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#89-install-pandoc-document-conversion-optional) | `winget install JohnMacFarlane.Pandoc` or [download](https://pandoc.org/installing.html) |
| 7 | Python | `python --version` | Yes | [Section 8.4](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#84-python-required) | `winget install Python.Python.3.12` or [download](https://python.org/downloads) |
| 8 | .NET SDK | `dotnet --list-runtimes` | No | — | `winget install Microsoft.DotNet.SDK.10` or [download](https://dotnet.microsoft.com/download/dotnet/10.0) |
| 9 | Azure CLI | `az --version` | No | [Section 8.12](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#812-install-azure-cli-az-optional) | `winget install Microsoft.AzureCLI` (Windows) · `brew install azure-cli` (macOS) · [install guide](https://learn.microsoft.com/cli/azure/install-azure-cli) |

For Pandoc: if the command fails, check if `C:\Program Files\Pandoc\pandoc.exe` exists on disk. If it exists but can't execute, report "Installed but blocked by Application Control policy" as OK.

For Azure CLI: it is **optional** (used by ADO / Microsoft Graph / D365 skills). `az --version` works on all platforms. Recommend the installer that matches the detected OS/architecture — `winget install Microsoft.AzureCLI` on Windows (auto-selects x64/ARM64), `brew install azure-cli` on macOS (Intel & Apple Silicon), or the [Linux install guide](https://learn.microsoft.com/cli/azure/install-azure-cli-linux).

### VS Code Extensions (items 10–23)

Run this single command to get all installed extensions:
```
code --list-extensions
```

If the command returns empty, fall back to scanning the extensions directory:
```
Get-ChildItem "$env:USERPROFILE\.vscode\extensions" -Directory | Select-Object -ExpandProperty Name
```

Check for each extension in the output (case-insensitive). For any missing extension, show the `Ctrl+Shift+X` search term and the Marketplace install link.

| # | Extension | Extension ID | Required | Setup Guide | Install |
|---|-----------|-------------|----------|-------------|---------|
| 10 | GitHub Copilot | `github.copilot` | Yes | [Section 4](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#4-install--activate-github-copilot) | `Ctrl+Shift+X` → search **GitHub Copilot** — [Marketplace](https://marketplace.visualstudio.com/items?itemName=github.copilot) |
| 11 | Azure DevOps Assistant | `ms-daw-tca.ado-productivity-copilot` | No | [Section 8.3](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#83-azure-devops-assistant-extension-optional) | `Ctrl+Shift+X` → search **Git DevOps Assistant** — [Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-daw-tca.ado-productivity-copilot). ⚠️ Only install if you use Azure DevOps. Note: this extension connects at the **global level** (not per-workspace), so it applies to all workspaces. If you work with multiple tenants in separate workspaces, prefer the **Azure DevOps MCP Server** (item 25) which supports workspace-specific configuration. Without a configured connection, it shows a popup in the **Command Palette** (top center of screen) on every startup asking for credentials, which can block other MCP servers from starting. |
| 12 | Agentic Skill Installer | `christiankayser.agentic-skill-installer` | Yes | [Section 7](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#7-install-the-agentic-skill-installer) | `Ctrl+Shift+X` → search **Agentic Skill Installer** — [Marketplace](https://marketplace.visualstudio.com/items?itemName=christiankayser.agentic-skill-installer) |
| 13 | Azure MCP Server | `ms-azuretools.vscode-azure-mcp-server` | Yes | [Section 9.4](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#94-azure-mcp-server-required) | `Ctrl+Shift+X` → search **Azure MCP Server** — [Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azure-mcp-server) |
| 14 | GitHub Copilot for Azure | `ms-azuretools.vscode-azure-github-copilot` | Yes | [Section 9.4](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#94-azure-mcp-server-required) | `Ctrl+Shift+X` → search **GitHub Copilot for Azure** — [Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azure-github-copilot) |
| 15 | GitHub PR & Issues | `github.vscode-pull-request-github` | No | [Section 8.5](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#85-github-pull-requests--issues-optional) | `Ctrl+Shift+X` → search **GitHub Pull Requests** — [Marketplace](https://marketplace.visualstudio.com/items?itemName=GitHub.vscode-pull-request-github) |
| 16 | Markdown All in One | `yzhang.markdown-all-in-one` | No | [Section 8.8](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#88-markdown-all-in-one-optional) | `Ctrl+Shift+X` → search **Markdown All in One** — [Marketplace](https://marketplace.visualstudio.com/items?itemName=yzhang.markdown-all-in-one) |
| 17 | Python | `ms-python.python` | Yes | [Section 8.4](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#84-python-required) | `Ctrl+Shift+X` → search **Python** — [Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-python.python) |
| 18 | Live Share | `ms-vsliveshare.vsliveshare` | No | [Section 8.6](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#86-live-share-optional) | `Ctrl+Shift+X` → search **Live Share** — [Marketplace](https://marketplace.visualstudio.com/items?itemName=MS-vsliveshare.vsliveshare) |
| 19 | Docx Reader | `shahilkumar.docxreader` | No | [Section 8.7](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#87-docx-reader-optional) | `Ctrl+Shift+X` → search **Docx Reader** — [Marketplace](https://marketplace.visualstudio.com/items?itemName=shahilkumar.docxreader) |
| 20 | vscode-pandoc | `chrischinchilla.vscode-pandoc` | No | [Section 8.9](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#89-install-pandoc-document-conversion-optional) | `Ctrl+Shift+X` → search **vscode-pandoc** — [Marketplace](https://marketplace.visualstudio.com/items?itemName=chrischinchilla.vscode-pandoc) |
| 21 | Copilot Studio | `ms-copilotstudio.vscode-copilotstudio` | No | [Section 8.10](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#810-microsoft-copilot-studio-optional) | `Ctrl+Shift+X` → search **Copilot Studio** — [Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-CopilotStudio.vscode-copilotstudio) |
| 22 | Skills for Copilot Studio plugin | *(see note below)* | No | [Section 8.10.1](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#8101-skills-for-copilot-studio-plugin-optional--manual-install-only) | **⚠️ Manual install only — do NOT auto-install.** See note below. |
| 23 | Power Platform Skills plugin | *(see note below)* | No | [Section 8.11](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#811-power-platform-skills-optional--manual-install-only) | **⚠️ Manual install only — do NOT auto-install.** See note below. |

> **Items 21 & 22 work together.** The Copilot Studio extension (item 21) provides clone/edit/sync for Copilot Studio agents. The Skills for Copilot Studio plugin (item 22) supercharges it — adding AI-powered authoring, testing, and troubleshooting sub-agents that generate agent YAML via natural language. Install both in a **dedicated Copilot Studio workspace**.
>
> **Item 23 is separate.** The Power Platform Skills plugin (item 23) is for building Power Apps and Power Pages — a different domain. It does **not** complement the Copilot Studio extension. Install it in a **separate Power Platform workspace**.
>
> **⚠️ Items 22 & 23: DO NOT auto-install.** These plugins register sub-agents, hooks, and commands designed for specialist development. Installing them in a general-purpose delivery workspace adds noise to your agent list and may interfere with other workflows. Even if the user explicitly asks to install them, do NOT install them automatically. Instead, show this warning and direct the user to [Section 8.10.1](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#8101-skills-for-copilot-studio-plugin-optional--manual-install-only) (Copilot Studio) or [Section 8.11](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#811-power-platform-skills-optional--manual-install-only) (Power Platform) to read the warnings and follow the manual installation steps.
>
> **Detection for items 22 & 23:** These are plugins, not regular VS Code extensions — they cannot be detected via `code --list-extensions`. Always show them with status ➡️ (informational) and the manual-install note. Never mark them as ✅ installed or ❌ missing — they are always "manual check required".

### MCP Server Configuration (items 24–30)

Check for MCP server configuration in these two files (read both, merge server keys):
- Workspace: `.vscode/mcp.json`
- User-level: `%APPDATA%\Code\User\mcp.json` (on Windows)

Parse the JSON (strip `//` comments that don't follow `:`) and collect all server key names from the `servers` object.

**Important: A server counts as installed if it exists in EITHER file.** If a server is configured at workspace level (`.vscode/mcp.json`) but disabled at user level (`"disabled": true` in user mcp.json), it is still **installed and active** — the workspace configuration takes precedence. Only report a server as missing if it does not appear in either file. If it appears in one file but is disabled in the other, report it as ✅ installed with a note like "Configured in workspace mcp.json (disabled at user level)".

**Scope reporting:** For each found MCP server, indicate where it is configured by appending a scope label:
- `(this workspace — enabled)` — found in `.vscode/mcp.json` and not disabled
- `(user/global — enabled)` — found in user-level `mcp.json` and not disabled
- `(this workspace + user/global — both enabled)` — found in both files, neither disabled
- `(this workspace — enabled, disabled at user/global level)` — active in this workspace but disabled globally; may also be enabled in other workspaces that have their own `.vscode/mcp.json`
- `(user/global — enabled, disabled in this workspace)` — active globally but disabled in this workspace
- `(disabled in both)` — configured but disabled everywhere visible — report as ❌ with note: "Configured but disabled in this workspace and at user/global level. Enable it or re-install to use it here."
- `(disabled in this workspace, not found globally)` — disabled here and no user-level config — report as ❌ with note: "Configured but disabled in this workspace. Enable it to use it here."
- `(disabled globally, not in this workspace)` — disabled at user level and not in workspace config — report as ❌ with note: "Configured at user level but disabled, and not configured in this workspace. Add it to `.vscode/mcp.json` or enable it globally."

**Key rule:** If an MCP server is not configured in this workspace AND the global/user-level entry is disabled, treat it as **not installed** (❌). A disabled global entry does not make it available — it must be actively enabled somewhere to work. Only ✅ if it is enabled in at least one scope (this workspace or user/global).
**When reporting ❌ for disabled/missing MCP servers, always explain the reason and give options to fix:**

For each ❌ item, include a "Reason & fix" block like this:

> **Reason:** `<server-name>` — found in user mcp.json (`%APPDATA%\Code\User\mcp.json`) with `"disabled": true`. Not configured in this workspace (`.vscode/mcp.json` does not contain this server / `.vscode/mcp.json` does not exist).
>
> **Options to fix:**
> 1. **Enable globally** — open `%APPDATA%\Code\User\mcp.json`, find the `<server-key>` entry, and remove the `"disabled": true` line or set it to `false`
> 2. **Add to this workspace** — add the server to `.vscode/mcp.json` (this keeps it workspace-specific and does not affect other workspaces)
> 3. **Re-install** — use the one-click install link above to add it fresh

Adapt the reason text to the actual situation:
- If the server is found nowhere at all: "Not found in workspace `.vscode/mcp.json` or user-level `%APPDATA%\Code\User\mcp.json`."
- If `.vscode/mcp.json` does not exist: mention that explicitly — "This workspace has no `.vscode/mcp.json` file."
- If the global file has `"disabled": true`: show the exact key name and file path so the user can find it quickly.
This check can only see the **current workspace** and user-level config. It cannot scan other workspaces on disk. If a server is disabled globally but enabled here, it may also be enabled in other workspaces — this check has no way to know.

> **💡 Tip:** To check MCP server configuration in another workspace, open that workspace in VS Code and run this setup check there.

Check for these required MCP servers (match any alias):

| # | MCP Server | Aliases to match | Required | Setup Guide | Install |
|---|------------|-----------------|----------|-------------|--------|
| 24 | Microsoft Learn (9.1) | `microsoftdocs/mcp`, `microsoft-learn`, `mslearn` | Yes | [Section 9.1](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#91-microsoft-learn-mcp-server-required) | [One-click install](https://vscode.dev/redirect/mcp/install?name=microsoft-learn&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Flearn.microsoft.com%2Fapi%2Fmcp%22%7D) |
| 25 | Azure DevOps (9.2) | `ado`, `microsoft/azure-devops-mcp`, `azure-devops`, `azure-devops-mcp` | Yes | [Section 9.2](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#92-azure-devops-mcp-server-required) | [One-click install](https://vscode.dev/redirect/mcp/install?name=ado&config=%7B%22type%22%3A%22stdio%22%2C%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22-y%22%2C%22%40azure-devops%2Fmcp%22%2C%22%24%7Binput%3Aado_org%7D%22%5D%7D&inputs=%5B%7B%22id%22%3A%22ado_org%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22Azure%20DevOps%20organization%20name%20(e.g.%20contoso)%22%7D%5D) |
| 26 | WorkIQ (9.3) | `workiq`, `work-iq`, `microsoft/workiq` | Yes | [Section 9.3](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#93-workiq-mcp-server-required) | [One-click install](https://vscode.dev/redirect/mcp/install?name=workiq&config=%7B%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22-y%22%2C%22%40microsoft%2Fworkiq%22%2C%22mcp%22%5D%7D) |
| 27 | Playwright (9.5) | `playwright`, `microsoft/playwright-mcp` | Yes | [Section 9.5](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#95-playwright-mcp-server-required) | [One-click install](https://vscode.dev/redirect/mcp/install?name=playwright&config=%7B%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22%40playwright%2Fmcp%40latest%22%5D%7D) |

Also check these optional specialist MCP servers:

| # | MCP Server | Aliases to match | Required | Setup Guide | Reference |
|---|------------|-----------------|----------|-------------|----------|
| 28 | Dataverse MCP (9.6) | `dataverse`, `DataverseDevelopmentMcp` | No | [Section 9.6](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#96-dataverse--power-platform-mcp-server-optional) | [Chrysalis repo](https://dev.azure.com/chrysalis-innersource/DevBridge/) |
| 29 | D365 F&O Dev MCP (9.7) | `xpp`, `fno`, `fo-mcp` | No | [Section 9.7](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#97-dynamics-365-fo-mcp-server-optional) | [GitHub repo](https://github.com/mcaps-microsoft/Xpp-MCP-for-Dynamics-Finance-and-Operations/tree/main) |
| 30 | D365 F&O ERP MCP (9.8) | `d365`, `erp`, `dynamics`, `volcano` | No | [Section 9.8](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#98-d365-fo-erp-mcp-configurator-optional) | [MS Learn guide](https://learn.microsoft.com/dynamics365/fin-ops-core/dev-itpro/copilot/mcp/mcp-vscode) |

For Dataverse, also check VS Code extensions for `DataverseDevelopmentMcp`.

## Output Format

Present results as a **single summary** with three tables (CLI Tools, Extensions, MCP Servers) using **continuous numbering** from 1 to 30 across all tables.

### Column requirements — ALWAYS include these columns in every table:

**CLI Tools table columns:** `#`, `Status`, `Component`, `Version`, `Required`, `Setup Guide`, `Install`
**Extensions table columns:** `#`, `Status`, `Extension`, `Required`, `Setup Guide`, `Install`
**MCP Servers table columns:** `#`, `Status`, `MCP Server`, `Required`, `Setup Guide`, `Install`

- **Setup Guide** — Always show the README section link (e.g., `[Section 8.1](url)`) even when the item is already installed. Users may want to review the guide.
- **Install** — Always show the full install command/link even when the item is already installed. For CLI tools, show `winget install ...` AND the `[download](url)` fallback. For extensions, show `Ctrl+Shift+X` search term AND `[Marketplace](url)` link. For MCP servers, show the `[One-click install](url)` or repo/guide link.
- Never omit Setup Guide or Install columns — they serve as reference documentation regardless of install status.

Each table must include these columns:
- **#** — continuous item number
- **Status** — icon (see below)
- **Component** — name of the tool/extension/server
- **Version** — detected version or "—"
- **Required** — Yes / No
- **Install** — **ALWAYS show the install method**, regardless of whether the item is installed or not. Use the install command/link/search from the checklist above. This column is a reference — users may need it later even if everything is installed now.

For the **CLI Tools** table, always show the `winget` command and download link.

For the **Extensions** table, always show:
- `Ctrl+Shift+X` → search **ExtensionName**
- `[Marketplace](https://marketplace.visualstudio.com/...)` link
- Setup Guide link to the README section

For the **MCP Servers** table, always show the one-click install link or reference link.

Use these status icons:
- Installed: ✅
- Missing (required): ❌
- Missing (optional): ⚠️
- Skipped: ➖
- Manual check required (items 22 & 23): ➡️

**All tables** must include a **Setup Guide** column with a link to the corresponding README section. Use the links from the "Setup Guide" column in the checklists above. Show `—` if no dedicated guide section exists (e.g., npx, .NET SDK).

At the end, show a **summary line** like:
> **24/26 components installed.** 1 required missing, 1 optional missing.

If anything required is missing, list the missing items with full install instructions (winget command, one-click link, or `Ctrl+Shift+X` search), plus the README section link for detailed instructions.

If WorkIQ is found, add this tip:
> 💡 Run `workiq accept-eula` in Copilot Chat to activate WorkIQ.

Finally, list any extra MCP servers configured that aren't in the checklist above.

## Installation Options

After presenting the results, if **any items are missing**, show this menu:

> **What would you like to do?**
>
> 1. **Install all missing** — install every missing component (required + optional)
> 2. **Install required only** — install only missing required components
> 3. **Install optional only** — install only missing optional components
> 4. **Pick specific items** — choose by number (e.g., `4, 12, 20`)
> 5. **No thanks** — just show the report, I'll install manually

Wait for the user's response before proceeding.

### How to install each type

**CLI tools (items 1–9):**
- Run the `winget install` command from the Install column in the terminal.
- For `gh auth` (item 5): run `gh auth login --hostname github.com --git-protocol https --web` and tell the user to complete the browser sign-in.
- After installing Node.js, npx becomes available automatically — no separate install needed.
- For Azure CLI (item 9): pick the command that matches the detected OS/architecture — `winget install Microsoft.AzureCLI` on Windows (x64/ARM64 auto-selected), `brew install azure-cli` on macOS (Intel & Apple Silicon), or the [Linux install guide](https://learn.microsoft.com/cli/azure/install-azure-cli-linux). After install, run `az login` to sign in.
- After any CLI install, remind the user: "Close and reopen VS Code for PATH changes to take effect."

**VS Code extensions (items 10–23):**
- Use the terminal command: `code --install-extension <extension-id>` for each missing extension.
- Example: `code --install-extension christiankayser.agentic-skill-installer`
- After installing, run `Developer: Reload Window` or tell the user to reload.

**MCP servers (items 24–27, required):**
- Open the one-click install link in the user's browser. Tell the user: "A browser tab will open — click **Open Visual Studio Code** when prompted, then click **Allow/Install** in VS Code."
- Install one at a time and confirm each before proceeding to the next.

**Specialist MCP servers (items 28–30, optional):**
- These require manual/custom installation. Show the reference link and explain what's needed:
  - **Dataverse (28):** Custom installer from Chrysalis Innersource — see [README section 9.6](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#96-dataverse--power-platform-mcp-server-optional)
  - **D365 F&O Dev (29):** Not publicly distributed — contact Denis Shlykov / Max Hentschel
  - **D365 F&O ERP (30):** Environment-specific HTTP server — see [README section 9.8](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#98-d365-fo-erp-mcp-configurator-optional)

### After installation

Once the user's selected installations are complete, **re-run the full check automatically** and present the updated results table. This confirms everything installed correctly.
