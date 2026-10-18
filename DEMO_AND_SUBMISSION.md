# Demo and submission preparation

Target track: **Agents That Act on Connected Data**. Keep the entry focused on Track 01. Persistent memory supports the investigation; do not claim multi-agent coordination.

## Redesign walkthrough

Use the sidebar to reach investigations, history and response tasks. The question form starts a run; the map explains connections; the Overview tab presents the brief and response. Download report exports the selected snapshot as JSON. New history entries include a saved map; older ones explicitly warn when showing the current graph.

## Before recording

- Confirm your registration on the event page.
- Run all integration tests locally. Record the output in PARTICIPANT_NOTES.md.
- Enable AI mode and verify a complete live response. A mocked test is not an AI demonstration.
- Start with the Notifications dependency switch off.
- Confirm an Evidence-mode Ledger DB investigation returns six affected services.
- Review graph.py and agent.py using the explanation below.
- Record only the app, never your API key or .env.

## Suggested 3-minute demo (our suggested length, not an official limit)

0:00–0:20 — Problem
“When a shared database fails, the hard part is understanding what else may be affected and who should act. Ripple connects dependencies, owners, runbooks and previous investigations in FalkorDB.”

0:20–1:00 — Live AI investigation
Choose Ledger DB and **AI investigator · Gemini**. Run an investigation. Show the mode badge, six affected services and the Storefront → Checkout → Payments → Ledger DB evidence path. Open **Evidence** to inspect paths and **Tool activity** to expand tool results. Explain that the model called constrained graph tools and the graph supplied the facts. You may edit waiting time out of the recording; do not imply edited latency is measured latency.

1:00–1:35 — Graph changes the answer
Enable Connect Notifications to Payments. Run a NEW investigation. Show seven affected services and the new Notifications → Payments → Ledger DB path. Explain that the answer changed because an edge changed in FalkorDB. Turn it off afterward if desired.

1:35–2:05 — Memory
Run again or reopen the app and investigate the same service. Show the previous investigation ID under remembered context. Explain that memory comes from Investigation → ABOUT → Service relationships. Opening an old history item alone is not a fresh investigation.

2:05–2:30 — Action
Show the linked runbook and proposed local response task. Click approve and show the stored task. State clearly that the prototype does not restart production systems or send messages.

2:30–3:00 — Honest limits and contribution
Say the data is synthetic, impact is potential, and root cause is not established. State your own verified contribution accurately and acknowledge AI assistance. End with the public repository link.

## Explain the implementation in your own words

1. A node represents a service, team, runbook, incident, investigation or task.
2. An edge records a relationship such as depends on or owned by.
3. To investigate Ledger DB, the query ends at Ledger DB and follows incoming dependency paths up to eight hops.
4. The model chooses read-only functions; Python executes fixed parameterized Cypher. The model never executes arbitrary database queries.
5. Previous investigations are saved in FalkorDB and retrieved by service, so the next session has context.
6. A human approval creates one local task with a stable ID; repeated approvals do not duplicate it.
7. The graph establishes connections, not proof of failure or causality. Missing owners and missing runbooks are explicitly reported.

## Meaningful participant work before submission

Choose one small domain change yourself: add a new synthetic service and its owner/dependency in graph.py, or write another expected-impact test. Predict what the graph should return, run the app/tests, and record what you learned. Do not merely claim you made a change. Keep the project within the event's originality and AI-assistance rules.

## Suggested project description — review against your actual run

Ripple investigates potential outage impact using FalkorDB as the central context layer. A tool-calling AI agent retrieves multi-hop dependency paths, service ownership, source-labelled runbooks, prior incidents and persistent investigation memory. Users can inspect the graph evidence and approve a local response task. Changing a dependency changes the investigation result. The prototype uses synthetic data and distinguishes potential impact from observed failures.

## Required submission checklist

- [ ] Public source-code repository, accessible while signed out.
- [ ] README with setup instructions and graph model.
- [ ] Essential queries in graph.py and documented in README.
- [ ] Working demo video link, accessible to judges.
- [ ] Complete local setup instructions; no live deployment is claimed.
- [ ] Track 01 selected in the submission form.
- [ ] AI assistance disclosed, with truthful participant notes.
- [ ] No credentials, .env, .venv, private data or generated database files in the repository.
- [ ] Final submission sent before the deadline shown by the event page.

## GitHub upload

Create a new public GitHub repository called `ripple-graph-agent`. You can upload source through GitHub's “Add file → Upload files”. Upload the contents of this project's folder, not just the ZIP. Include app.py, graph.py, agent.py, requirements.txt, start.command, README and other Markdown files, static/, tests/, .env.example and .gitignore. Do not upload your local .env or .venv.

For a Git upload, use your own repository URL and authentication. No repository has been created or submission sent by this package.

## Troubleshooting

- `Cannot connect to Docker`: open Docker Desktop first.
- `python3: command not found`: install Python from python.org, then reopen VS Code.
- Port 6379 already allocated: your existing FalkorDB may already be running. Do not create a second container; use it.
- Port 5050 in use: change PORT in .env to 5051, restart and open localhost:5051.
- Database unavailable: verify `docker ps`, start graph-practice, and refresh.
- AI HTTP 400/404: check that GEMINI_MODEL is a model your account supports for generateContent/function calling.
- AI HTTP 401/403: check key validity and model access.
- AI HTTP 429: quota/rate limit. Retry later or choose an available model. Do not label evidence-only output as AI.
- Same task after approving twice: expected; approval is idempotent.
