# AI First — Mappings Reference

> Consolidated from AI First Artifact Storage Strategy v3, AI Tools Inventory v0.9, and the AIFirstHub registry.
>
> Section order follows the field order in [`artefact-template.yaml`](./artefact-template.yaml): **Classification → Methodology → Distribution → Prerequisites → Product Mapping → Technologies → Free-text fields**.
>
> The DRIVE checklist mapping was removed from the template; the historical stages/items reference is archived in [`old/mappings-reference-DRIVE-checklist-mapping.md`](../../../../old/mappings-reference-DRIVE-checklist-mapping.md).
>
> **The `all` wildcard.** Multi-select fields — `roles`, `phases`, `methodologies`, `product-family`, `products`, and SureStep365 phase/activity lists — accept the literal token `all` meaning "the entire set". It is stored **verbatim** and is **not** expanded into individual values, so catalog consumers must treat `all` as a wildcard when matching. RAPID v2 `tasks` never accepts `all`; every mapping must cite exact canonical tasks. Do **not** use `all` on single-select fields (`type`, `category`, `installer-group`, `status`) or open free-form lists (`technologies`, `tags`).

---

# Classification

## Artefact Type

Used in `artefact.yaml` → `type` field. Pick exactly one.

| Value | Description |
|---|---|
| `mcp-server` | Model Context Protocol server |
| `agent` | AI agent |
| `skill` | Reusable Copilot skill |
| `prompts` | Prompt library |
| `tool` | Standalone tool or utility |
| `documentation` | Guide or reference material |
| `starter-kit` | Project template |

---

## Category

Used in `artefact.yaml` → `category` field. Functional domain grouping. Pick exactly one.

| Value | Description |
|---|---|
| `functional` | D365 functional design, FDD/IDD authoring, requirements |
| `technical` | Code generation, TDD, development execution |
| `testing` | Test execution, test case management, quality assurance |
| `governance` | DRIVE checklist, stakeholder management, compliance |
| `productivity` | Document generation, meetings, scheduling, personal productivity, repo/skill tooling |

---

## Installer Group

Used in `artefact.yaml` → `installer-group` field. Groups artefacts for the Agentic Skill Installer UI — independent of `category` (which describes the functional domain). Pick exactly one.

| Value | Description |
|---|---|
| `presales` | Presales discovery, proposals, pursuit, estimation, RFI/RFP support |
| `methodology-manager` | Methodology authoring, phase preparation, activity guidance, methodology catalog management |
| `governance` | DRIVE checklist, stakeholder management, compliance, risk and approvals |
| `delivery` | Sprint planning, status reporting, backlog management, build/test/deploy execution |
| `productivity` | Meeting notes, scheduling, time-saving automation, personal productivity, repo and skill tooling |

---

## Roles

Used in `artefact.yaml` → `roles` array. Pick one or more. This is the AiBS audience taxonomy. Canonical RAPID task ownership is derived separately from `rapid-registry.generated.json`; do not change or infer a skill's audience role merely to match a task owner.

| Value | Description |
|---|---|
| `solution-architect` | Solution architects — own designs and the design gate |
| `technical-architect` | Technical architects — platform/solution technical design |
| `data-architect` | Data architects — data model, migration, integration design |
| `security-architect` | Security architects — security design and controls |
| `engagement-lead` | Engagement lead — owns foundation & mobilisation |
| `program-director` | Program director — program-level governance |
| `project-manager` | Project managers and delivery leads |
| `customer-project-manager` | Customer-side project manager |
| `functional-consultant` | Functional consultants — requirements, design, config, demo |
| `technical-consultant` | Technical consultants — build, config-dev, X++ |
| `business-analyst` | Business analysts — requirements & process capture |
| `ux-designer` | UX / experience designers |
| `ai-engineer` | AI / ML engineers — agents and models |
| `platform-engineer` | Platform / infrastructure engineers |
| `devops-lead` | DevOps lead — CI/CD and pipelines |
| `release-manager` | Release manager — release & deployment orchestration |
| `service-operations-lead` | Service operations lead — run / operate |
| `hypercare-lead` | Hypercare lead — post-go-live stabilisation |
| `security-engineer` | Security engineers — implementation-side security |
| `test-lead` | Test lead — test design, execution, and defects |
| `all` | All roles (wildcard) |

---

## Phases

Used in `artefact.yaml` → `phases` array. Generic delivery phases (methodology-agnostic). Pick one or more.

| Value | Description |
|---|---|
| `presales` | Pursuit, RFI/RFP, proposals, estimation, discovery |
| `planning` | Discovery, estimation, architecture |
| `build` | Development, testing, integration |
| `delivery` | Deployment, handover, go-live |
| `operations` | Post-go-live support and monitoring |
| `all` | All phases (wildcard) |

---

## Status

Used in `artefact.yaml` → `status` field. Pick exactly one.

| Value | Meaning |
|---|---|
| `draft` | Work in progress |
| `beta` | Usable but may change |
| `production` | Stable, recommended |
| `deprecated` | No longer maintained |

---

# Methodology Mapping

## Methodology

Used in `artefact.yaml` → `methodologies` array. Pick one or more.

| Value | Description |
|---|---|
| `SureStep365` | SureStep365 methodology — flat activity numbering, format `PP-AA` |
| `all` | Methodology-agnostic compatibility (wildcard); RAPID module membership is declared separately under `distribution.rapid-module` |

---

## SureStep365 Phases

Used in `artefact.yaml` → `surestep365.phases` array. Pick one or more.

| Code | Value | Description |
|------|-------|-------------|
| 01 | `presales-discovery` | Presales & Discovery |
| 02 | `mobilize-delivery` | Mobilize Delivery |
| 03 | `initiate` | Initiate |
| 04 | `solution-modelling` | Solution Modelling |
| 05 | `config-dev-sprints` | Config & Dev Sprints |
| 06 | `solution-testing` | Solution Testing |
| 07 | `prepare-deploy` | Prepare & Deploy |
| 08 | `operate` | Operate |
| 09 | `monitor-optimise` | Monitor & Optimise |
| — | `all` | All phases (wildcard) |

---

## SureStep365 Activities

Used in `artefact.yaml` → `surestep365.activities` array. Activity IDs use the format `PP-AA` — phase number + activity number (e.g., `05-02`). Use `{code, name}` objects (plain strings lose their names when aggregated to JSON). The wildcard `{ code: "all", name: "All activities" }` marks a skill that spans every activity.

### Phase Directory Names

Folder layout under `delivery/methodologies/SureStep365/` — reference only, not used in `artefact.yaml`.

| Directory | Phase |
|---|---|
| `01-Presales-and-Discovery` | Presales & Discovery |
| `02-Mobilize-Delivery` | Mobilize Delivery |
| `03-Initiate` | Initiate |
| `04-Solution-Modeling` | Solution Modelling |
| `05-Config-and-Dev-Sprints` | Config & Dev Sprints |
| `06-Solution-Testing` | Solution Testing |
| `07-Prepare-and-Deploy` | Prepare & Deploy |
| `08-Operate` | Operate |

### Activities by Phase

#### 01 — Presales & Discovery

| Code | Activity |
|---|---|
| 01-01 | Conduct the Presales & Discovery Phase kickoff |
| 01-02 | Create the initial solution architecture |
| 01-03 | Perform Discovery workshop(s) and workstream planning |
| 01-04 | Conduct Discovery workshop(s) |
| 01-05 | Capture business outcomes and high-level requirements and dependencies |
| 01-06 | Demo relevant D365 Copilot(s) to identify possible synergies |
| 01-07 | Create an initial solution demo configuration and update the solution architecture |
| 01-08 | Load required sample customer data |
| 01-09 | Demo initial solution configuration |
| 01-10 | Document risks, actions, issues, and decisions (RAID) |
| 01-11 | Create/refine the One Services Estimator (OSE) |
| 01-12 | Develop an initial high-level project implementation schedule |
| 01-13 | Create/refine the Statement of Work (SOW) |
| 01-14 | Conduct reviews (internal and w/customer) including value positioning |
| 01-15 | Review additional EMEA-derived DRIVE Checklist items |

#### 02 — Mobilize Delivery

| Code | Activity |
|---|---|
| 02-01 | Review onboarding, discovery outcomes, SOW, and customer readiness |
| 02-02 | Conduct the Mobilize Delivery kick off meeting |
| 02-03 | Perform Sales to Delivery internal handover |
| 02-04 | Perform SS365 & WBS alignment with customer |
| 02-05 | Plan readiness training and workshops |
| 02-06 | Establish baseline project governance & management plans |
| 02-07 | Request team-internal tools & licenses |
| 02-08 | Discuss onboarding ramp up & scope management plan |
| 02-09 | Review ISD, customer, and partner staffing checkpoints |
| 02-10 | Review additional DRIVE Checklist items (Mobilization & Communication) |

#### 03 — Initiate

| Code | Activity |
|---|---|
| 03-01 | Conduct the Initiate phase kick off |
| 03-02 | Finalize tailoring the governance & project management plans and artifacts |
| 03-03 | Finalize tailoring and instantiating the 360 Governance boards and stakeholder management |
| 03-04 | Complete project tools installation and configuration |
| 03-05 | Conduct SS365 methodology and tools training |
| 03-06 | Conduct Dynamics overview training |
| 03-07 | Perform infrastructure planning and environment setup |
| 03-08 | Perform feature team & project-wide workstream planning |
| 03-09 | Develop Solution Modeling plans |
| 03-10 | Review and Update the Release plan |
| 03-11 | Develop the draft Solution Testing plan with the customer |
| 03-12 | Tailor the ACSM Plan with the customer |
| 03-13 | Provide internal stakeholder update prior to concluding Initiate |
| 03-14 | Review Additional DRIVE Checklist Items |

#### 04 — Solution Modelling

| Code | Activity |
|---|---|
| 04-00 | Review DRIVE Checklist items pre-Solution Modeling and throughout |
| 04-01 | Conduct Solution Modeling phase kick off |
| 04-02 | Review/map business outcomes and processes for the release |
| 04-03 | Conduct solution modeling workshops (Functional, Technical, and Performance) |
| 04-04 | Review/identify requirements/user stories |
| 04-05 | Establish data, integration, security strategy |
| 04-06 | Conduct high-Level extensions/customizations workshop |
| 04-07 | Demo "show and tell" baseline configuration |
| 04-08 | Prototype transformative business process and baseline configuration |
| 04-09 | Demo D365 Copilot or Copilot Studio GenAI and agentic capabilities |
| 04-10 | Document outcomes and key areas of change impact |
| 04-11 | Start first version of Solution Design Document with all sections updated |
| 04-12 | Update the Project and Release plans |
| 04-13 | Create/update the Sprint plan and schedule |
| 04-14 | Create/update Test plan and schedule |
| 04-15 | Release sign off |

#### 05 — Config & Dev Sprints

| Code | Activity |
|---|---|
| 05-01 | Conduct Config & Dev phase kick off |
| 05-02 | Functional analysis & design activity set |
| 05-03 | Technical analysis & design activity set |
| 05-04 | Configuration & Development activity set |
| 05-05 | Integration config & development |
| 05-06 | Data Migration mapping & script development |
| 05-07 | Test scripts development |
| 05-08 | Sprint Testing activity set |
| 05-09 | CI/CD Release Management |
| 05-10 | Sprint Demo |
| 05-11 | Conduct E2E/SIT & UAT preparation |

#### 06 — Solution Testing

| Code | Activity |
|---|---|
| 06-01 | Conduct the Solution Testing phase kick-off |
| 06-02 | Start cutover/go-live planning |
| 06-03 | Execute E2E data migration scripts in the SIT and UAT environments |
| 06-04 | Run process test scripts |
| 06-05 | Run E2E SIT test scripts |
| 06-06 | Run performance & benchmarking tests |
| 06-07 | Run user acceptance tests |
| 06-08 | Complete final Infosec security assessment & fixes |
| 06-09 | Triage results with dev team and customer to disposition, status and assign |
| 06-10 | Finalize training guides & job aids |

#### 07 — Prepare & Deploy

| Code | Activity |
|---|---|
| 07-01 | Conduct Deployment phase kick-off |
| 07-02 | Execute the Go-Live readiness checklist |
| 07-03 | Perform Operations readiness planning |
| 07-04 | Conduct final build and mock cutover process |
| 07-05 | Deploy build to production environment |
| 07-06 | Run final data migrations |
| 07-07 | Validate final application configurations |
| 07-08 | Perform smoke test |
| 07-09 | Validate security configuration |
| 07-10 | Run deployment checklist activities |
| 07-11 | Release system to end users |

#### 08 — Operate

| Code | Activity |
|---|---|
| 08-01 | Conduct Operate phase kick off |
| 08-02 | Create/update transition plan |
| 08-03 | Conduct system/infrastructure configuration walk-through |
| 08-04 | Conduct application configuration walk-through |
| 08-05 | Review incident management processes |
| 08-06 | Conduct support incident walk-through for critical issues |
| 08-07 | Conduct standard operating procedures walk-through |
| 08-08 | Conduct full solution deployment in pre-production environment |
| 08-09 | Conduct defect identification process walk-through |
| 08-10 | Fix and deploy a production defect (Microsoft led) |
| 08-11 | Review defect management process (SDLC/ALM) |
| 08-12 | Fix and deploy a production defect (customer led) |
| 08-13 | Review configuration update process (SDLC/ALM) |
| 08-14 | Review application security management process |
| 08-15 | Create system operations guide |
| 08-16 | Review data management procedures |
| 08-17 | Conduct mock financial closing (Dynamics 365 F&O only) |
| 08-18 | Conduct support handoff meeting |
| 08-19 | Goto Solution Modeling for the next release or perform project closure |

---

# Distribution

## RAPID Module Distribution

Used in `artefact.yaml` → `distribution.rapid-module`. This is the sole per-skill RAPID declaration in AiBS: canonical methodology references, module membership, packaging readiness, and redistribution approval live together here.

- Every skill must include the complete assessment block. A nonmember keeps `enabled: false` and omits `mapping`.
- A `mapping` block means the skill belongs to the RAPID module at the declared phase/stream scope.
- `enabled: false` means the mapped skill is not yet approved for mirroring into RAPID projects.
- `enabled: true` means the owner approved distribution and all portability gates pass.
- A disabled `rapid-module` block without `mapping` records an assessment only; it does not make the skill a RAPID module member.

| Field | Type | Meaning |
|---|---|---|
| `enabled` | boolean | Explicit owner approval for RAPID to mirror the skill. Never infer `true` from methodology tags. |
| `mapping.phases` | string array | One or more canonical RAPID phase folder slugs. |
| `mapping.streams` | string array | Canonical RAPID stream folder slugs. May be empty for genuinely unstreamed scope. |
| `mapping.tasks` | string array | Optional exact canonical task filename stems. Empty means phase/stream applicability without a task ownership claim. |
| `namespace-safe` | boolean | The skill works when installed at `.github/skills/AIBS/<name>/`; it has no runtime dependency on `.github/skills/<name>/`. |
| `self-contained` | boolean | Runtime content is inside the skill folder or in skills named by `required-skills`; it does not depend on undeclared repository-level files. |
| `mode` | enum | `standalone`, `supporting`, or `substitute`. Ignored while disabled. |
| `required-skills` | array | AiBS skill folder names that must be installed with this skill as one dependency closure. |
| `conflicts-with` | array | Skill folder names that must not coexist with this skill in a target repository. |
| `plane-access.reads` | array | RAPID planes read directly: `raw`, `context`, `state`, `artefacts`. |
| `plane-access.writes` | array | RAPID planes written directly: `context`, `state`, `artefacts`. `raw` is immutable and forbidden. |

### Canonical Source and Registry

RAPID methodology metadata is owned by [mcaps-microsoft/RAPID](https://github.com/mcaps-microsoft/RAPID). AiBS does not define a second activity taxonomy.

1. Task files under [`methodology/<phase>/<stream>/`](https://github.com/mcaps-microsoft/RAPID/tree/main/methodology) define task identity and frontmatter (`task`, `phase`, `stream`, `task_group`, `output_type`, archetypes), plus owner, purpose, inputs, outputs, and execution behavior.
2. [`outcomes-catalogue.md`](https://github.com/mcaps-microsoft/RAPID/blob/main/methodology/references/outcomes-catalogue.md) defines outcomes and accountable owners.
3. [`tasks-index.md`](https://github.com/mcaps-microsoft/RAPID/blob/main/methodology/references/tasks-index.md) defines predecessor order within each phase/stream lane.
4. [`methodology/README.md`](https://github.com/mcaps-microsoft/RAPID/blob/main/methodology/README.md) defines the methodology structure.

[`rapid-registry.generated.json`](rapid-registry.generated.json) is a deterministic offline cache of those sources at one commit. `--check` rebuilds from the recorded commit, so PR validation is reproducible and does not follow floating `main`. Run the refresh command without `--check` only in an intentional registry-update change:

```bash
python scripts/sync_rapid_registry.py --check
python scripts/sync_rapid_registry.py  # intentionally advance to current main
```

The catalog validator rejects unknown phases, streams, and tasks. When tasks are listed, their canonical phase and stream must be included in the mapping. Task groups, owners, I/O, outcomes, and predecessor sequencing are derived from RAPID and must not be copied into skill metadata.

### Mapping Rules

- Use explicit canonical values; do not use `all`.
- `mapping.tasks` is optional in meaning but always present as an array. Use `[]` when no exact task is claimed.
- Add a task only when the skill materially performs, produces, or validates it. Shared keywords or phase placement are insufficient.
- Do not create artificial activities such as `project-setup`, `foundation-strategy`, `authored`, `solutioned`, `designed`, `built`, `tested`, `loop-complete`, `loop-govern`, `release`, or `knowledge-harvest`.
- AiBS runtime tags may remain in operational contracts, but they do not define RAPID methodology placement.
- Do not add `RAPID` to `methodologies` and do not create a top-level `rapid:` block.

### Modes

| Value | Meaning |
|---|---|
| `standalone` | Portable utility that does not replace or participate in RAPID methodology behavior. |
| `supporting` | Complements RAPID tasks or consumes RAPID project context without replacing the authoritative RAPID outcome skill. |
| `substitute` | Intentionally replaces one or more canonical RAPID tasks. Requires non-empty `mapping.tasks` and explicit owner approval. |

### Eligibility Rules

Set `enabled: true` only when all of these statements are true:

1. Status is `beta` or `production`, and the licence permits redistribution.
2. The complete package has been checked for hard-coded `.github/skills/<name>/` paths and works from the AIBS namespace.
3. Every runtime dependency is bundled or declared in `required-skills`.
4. Required skill dependencies are themselves eligible for RAPID distribution.
5. Every mapped phase, stream, and task was validated against the current commit-pinned RAPID registry.
6. `substitute` mappings have explicit owner approval; ordinary integrations should use `supporting`.

```yaml
distribution:
  rapid-module:
    enabled: true
    mapping:
      phases: [02-delivery-loops]
      streams: [solution]
      tasks: [run-process-testing]
    namespace-safe: true
    self-contained: true
    mode: supporting
    required-skills: []
    conflicts-with: []
    plane-access:
      reads: [context, state]
      writes: [artefacts]
```

---

# Prerequisites

## Prerequisites Catalog

Used in `artefact.yaml` → `prerequisites` block. Six supported categories — every skill must include all six keys (use `[]` when empty) so downstream tooling (Agentic Skill Installer, setup-check) can iterate consistently.

| Key | Purpose | Required fields | Optional fields |
|---|---|---|---|
| `mcp_servers` | Model Context Protocol servers the skill talks to | `name`, `purpose`, `required`, `install` | — |
| `cli_tools` | Command-line tools the skill invokes (e.g. `gh`, `git`, `az`) | `name`, `purpose`, `required`, `install`, `verify` | — |
| `python_packages` | Python packages installed via `pip` | `name`, `purpose`, `required`, `install` | `verify` |
| `npm_packages` | Node.js / npm packages installed via `npm` (global or local) | `name`, `purpose`, `required`, `install` | `verify` |
| `extensions` | VS Code extensions | `name`, `purpose`, `required` | — |
| `environment` | Runtime environments / IDEs / platforms that are provisioned, not one-command-installed (e.g. a Unified Development Environment, Visual Studio, an LCS project, a deployed D365 environment) | `name`, `purpose`, `required` | `setup` |

**Field semantics:**
- `name` — display name or package identifier (e.g. `@anthropic-ai/workiq-mcp`, `python-docx`, `ms-playwright.playwright`)
- `purpose` — one-line reason the skill needs it
- `required` — `true` if the skill cannot function without it; `false` if optional / graceful-degradation
- `install` — exact install command (e.g. `npm install -g <pkg>`, `pip install <pkg>`, `winget install <id>`)
- `verify` — command that returns 0 on success (e.g. `gh --version`, `npm list -g <pkg>`)
- `setup` — (environment only) a URL or short reference to provisioning/setup docs (environments can't be installed with one command)

**Example — `npm_packages`:**
```yaml
prerequisites:
  npm_packages:
    - name: "@anthropic-ai/workiq-mcp"
      purpose: "WorkIQ MCP server runtime"
      required: true
      install: "npm install -g @anthropic-ai/workiq-mcp"
      verify: "npm list -g @anthropic-ai/workiq-mcp"
```

---

# Product Mapping

Used in `artefact.yaml` → `product-family` (Level 1) and `products` (Level 2) arrays. A curated two-level Microsoft product taxonomy: `product-family` is the broad family used for roll-up filters, and `products` is the specific surface a skill acts on. Each Level 2 value belongs to exactly one family, and both fields accept the `all` wildcard. This vocabulary is separate from the free-form `technologies` field, which stays granular (languages, SDKs, MCP servers).

Families are organised by solution area, so AI copilots and agents, data and analytics, and DevOps tooling are first-class families rather than being folded into their licensing suites.

## Product Family

Used in `artefact.yaml` → `product-family` array. Pick one or more.

| Value | Description |
|---|---|
| `d365-finance-operations` | Dynamics 365 finance and operations apps |
| `d365-business-central` | Dynamics 365 Business Central |
| `power-platform` | Microsoft Power Platform and Dynamics 365 customer engagement apps |
| `microsoft-365` | Microsoft 365 productivity and collaboration |
| `ai-and-agents` | AI and agents (copilots, agents, models) |
| `data-and-analytics` | Data and analytics (reporting and data platform) |
| `azure` | Microsoft Azure cloud platform |
| `azure-devops` | Azure DevOps |
| `github` | GitHub |
| `security-and-identity` | Microsoft security and identity |
| `cross-cutting` | Cross-cutting or non-product |
| `all` | All product families (wildcard) |

## Products

Used in `artefact.yaml` → `products` array. Pick one or more. Every value rolls up to exactly one product family.

| Value | Product Family | Official name |
|---|---|---|
| `d365-fo` | `d365-finance-operations` | Dynamics 365 finance and operations apps (umbrella) |
| `d365-finance` | `d365-finance-operations` | Dynamics 365 Finance |
| `d365-supply-chain` | `d365-finance-operations` | Dynamics 365 Supply Chain Management |
| `d365-commerce` | `d365-finance-operations` | Dynamics 365 Commerce |
| `d365-hr` | `d365-finance-operations` | Dynamics 365 Human Resources |
| `d365-project-operations` | `d365-finance-operations` | Dynamics 365 Project Operations |
| `d365-bc` | `d365-business-central` | Dynamics 365 Business Central |
| `power-platform` | `power-platform` | Microsoft Power Platform (umbrella) |
| `dataverse` | `power-platform` | Microsoft Dataverse |
| `power-apps` | `power-platform` | Power Apps |
| `power-automate` | `power-platform` | Power Automate |
| `power-pages` | `power-platform` | Power Pages |
| `ai-builder` | `power-platform` | AI Builder |
| `d365-ce` | `power-platform` | Dynamics 365 customer engagement apps (umbrella) |
| `d365-sales` | `power-platform` | Dynamics 365 Sales |
| `d365-cs` | `power-platform` | Dynamics 365 Customer Service |
| `d365-fs` | `power-platform` | Dynamics 365 Field Service |
| `d365-customer-insights` | `power-platform` | Dynamics 365 Customer Insights (formerly Marketing) |
| `d365-contact-center` | `power-platform` | Dynamics 365 Contact Center |
| `microsoft-365` | `microsoft-365` | Microsoft 365 (umbrella) |
| `microsoft-teams` | `microsoft-365` | Microsoft Teams |
| `sharepoint` | `microsoft-365` | SharePoint |
| `outlook` | `microsoft-365` | Outlook |
| `onedrive` | `microsoft-365` | OneDrive |
| `microsoft-loop` | `microsoft-365` | Microsoft Loop |
| `microsoft-graph` | `microsoft-365` | Microsoft Graph |
| `microsoft-stream` | `microsoft-365` | Microsoft Stream |
| `microsoft-viva` | `microsoft-365` | Microsoft Viva |
| `copilot-studio` | `ai-and-agents` | Microsoft Copilot Studio (formerly Power Virtual Agents) |
| `microsoft-365-copilot` | `ai-and-agents` | Microsoft 365 Copilot |
| `github-copilot` | `ai-and-agents` | GitHub Copilot |
| `azure-ai-foundry` | `ai-and-agents` | Microsoft Foundry (formerly Azure AI Foundry, Azure AI Studio) |
| `azure-openai` | `ai-and-agents` | Azure OpenAI in Microsoft Foundry Models |
| `microsoft-agent-365` | `ai-and-agents` | Microsoft Agent 365 |
| `microsoft-fabric` | `data-and-analytics` | Microsoft Fabric |
| `power-bi` | `data-and-analytics` | Power BI |
| `azure` | `azure` | Microsoft Azure (umbrella) |
| `azure-devops` | `azure-devops` | Azure DevOps |
| `github` | `github` | GitHub |
| `microsoft-entra-id` | `security-and-identity` | Microsoft Entra ID (formerly Azure Active Directory) |
| `microsoft-purview` | `security-and-identity` | Microsoft Purview |
| `microsoft-intune` | `security-and-identity` | Microsoft Intune |
| `microsoft-sentinel` | `security-and-identity` | Microsoft Sentinel |
| `pure-business` | `cross-cutting` | Pure business change, no product surface |
| `all` | `cross-cutting` | Product-agnostic (wildcard) |

---

# Technologies & Tags

## Technologies

Used in `artefact.yaml` → `technologies` array. Common technology tags used across artefacts (not exhaustive — add as needed).

| Category | Values |
|---|---|
| **Microsoft 365** | `microsoft-teams`, `microsoft-365`, `microsoft-graph`, `onedrive`, `microsoft-stream`, `sharepoint` |
| **Dynamics 365** | `dynamics-365`, `d365-fo`, `d365-ce`, `d365-sales`, `d365-cs`, `d365-fs`, `d365-bc`, `d365-commerce`, `d365-hr`, `dataverse`, `power-platform` |
| **Azure** | `azure`, `azure-devops`, `azure-functions`, `azure-app-service`, `azure-sql`, `azure-storage`, `bicep`, `arm-templates` |
| **AI / MCP** | `github-copilot`, `work-iq-mcp`, `azure-devops-mcp`, `playwright-mcp`, `dataverse-mcp`, `azure-mcp`, `microsoft-learn-mcp` |
| **Languages** | `typescript`, `python`, `csharp`, `xpp`, `powershell` |

---

# Free-text Fields

These `artefact.yaml` fields don't have enum values — they're free-form strings, dates, or version constraints.

| Field | Format | Notes |
|---|---|---|
| `name` | string | Should match the skill folder name |
| `description` | string | 1–2 sentences — what it does and when to use it |
| `author` | string | Full name of primary author |
| `maintainers` | array of strings | Microsoft aliases (e.g., `["@dwojcik_microsoft"]`) |
| `support` | string | Contact email |
| `version` | semver string | e.g., `"0.1"`, `"1.2.3"` |
| `created` / `updated` | date | `YYYY-MM-DD` |
| `license` | string | Usually `"MIT"` — repo-level `LICENSE.TXT` is authoritative |
| `compatibility.vs_code` | version constraint | e.g., `">=1.85"` |
| `compatibility.copilot` | string | e.g., `"Agent mode required"` |
| `documentation` | URL | Link to README.md on GitHub |
| `repo` | string | `org/repo` (e.g., `mcaps-microsoft/ISDAIFirstAiBS`) |
| `project` | string | Project name; empty = "Generic / Reusable" |
| `tags` | array of strings | Free-form tags for search (e.g., `[meetings, recordings, weekly-report]`) |
| `allowed-tools` | string | Optional tool-access restriction (e.g., `"Bash(python:*) WebFetch"`) |
