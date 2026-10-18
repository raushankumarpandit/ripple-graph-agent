# Ripple — trace the impact, remember the response

A local incident investigation application built for Graph Hacks 2026, **Track 01: Agents That Act on Connected Data**.

When a service fails, Ripple follows dependency paths in FalkorDB, identifies potential downstream impact and owners, retrieves linked runbooks and past incidents, recalls earlier investigations, and proposes a response task for human approval.

**All data is fictional. Potential dependency impact is not proof of an outage or root cause.**

## Interface

A light investigation workspace with a dark navigation rail, restrained teal accents and a clear three-step flow. Features include:

- Interactive dependency map with node inspection, evidence highlighting and zoom.
- Separate Overview, Evidence and Tool activity tabs; searchable affected services.
- Safely formatted AI briefs with expandable long responses.
- Actual elapsed waiting time, empty states, connection status and readable errors.
- Saved history, JSON report downloads and explicit human approval of local tasks.
- Responsive layouts, keyboard-accessible tabs and graph nodes, visible focus and reduced-motion support.
- In-app help explaining the investigation and API-key setup.

Updating an older copy? Follow **START_HERE.md**. Keep your existing database container; no reset is required.

## Quick start on a Mac (Apple silicon supported)

Requirements: Docker Desktop running, Python 3.10+, internet for package installation. The existing `graph-practice` container is reused; the app uses a separate graph named `ripple` and does not modify the `practice` graph.

1. Extract the ZIP. Open the `ripple` folder in VS Code using File → Open Folder.
2. Open Terminal → New Terminal. Confirm the terminal is in the folder containing `app.py`.
3. Run:

```bash
bash start.command
```

4. Open http://localhost:5050 if it does not open automatically.
5. Click **Load sample system** once. Select **Ledger DB**, leave **Graph evidence · no AI required** selected, and click **Investigate impact**.
6. With **Connect Notifications to Payments** off, expect **6 potentially affected services**. Inspect the evidence and tool trace.

If Python is missing, install the macOS universal installer from https://www.python.org/downloads/macos/ and reopen VS Code. Do not paste Python/Cypher into the shell unless explicitly instructed.

## Enable the real AI agent

Evidence mode is deterministic graph querying, not an AI model. For the hackathon agent demonstration, enable and verify AI mode:

1. Create your own Gemini API key at https://aistudio.google.com/apikey. Access and quotas depend on your account.
2. Stop the app with Control+C in the terminal.
3. In VS Code open `.env` (created by the start script). Set `GEMINI_API_KEY` to your key. Do not quote or share it. `.env` is ignored by Git.
4. `GEMINI_MODEL` defaults to `gemini-3.8-flash`, the model in the current official function-calling example. If your account does not have it, set an available Gemini model supporting generateContent function calling. A denied model or quota produces a visible error, not a fabricated AI answer.
5. Restart: `bash start.command`.
6. Select **AI investigator · Gemini** and investigate. Wait for a completed brief and all three tool calls.

Gemini receives the question and synthetic graph evidence, including prior investigation summaries. Do not enter private information. No API key goes to the browser or graph.

## What makes this an agent?

In AI mode the model chooses and invokes three constrained tools through a bounded tool loop:

- `get_impact`: graph traversal of transitive dependents; paths and ownership.
- `get_context`: source-labelled runbooks and past incidents.
- `get_memory`: earlier investigations stored in FalkorDB.

The model must obtain all three results before its final brief is accepted. Maximum five model rounds; repeated tools use that run's cached result. The model never generates executable Cypher or invokes write tools. The application saves completed investigations. A separate user click approves a local task.

A structured graph-derived summary and evidence cards remain separate from the model-generated narrative. Generated narrative can still contain mistakes and must be checked against evidence.

## Graph model

| Node | Key properties | Relationships |
|---|---|---|
| Service | id, name, criticality, layer | DEPENDS_ON Service; OWNED_BY Team; HAS_RUNBOOK Runbook |
| Team | name | Incoming OWNED_BY |
| Runbook | id, title, steps, source | Incoming HAS_RUNBOOK |
| Incident | id, summary, resolution, source | INVOLVED Service |
| Investigation | id, created, summary, payload | ABOUT Service; PROPOSED Task |
| Task | id, title, owner, status, created | Incoming PROPOSED |

Twelve services, six fictional owning teams, three runbooks, three incidents. Analytics deliberately lacks an owner to demonstrate missing context. A `DEPENDS_ON` arrow goes from the dependent to its dependency: Checkout → Payments → Ledger DB.

## Essential Cypher

The full queries and parameter bindings are in `graph.py`. They are executed against FalkorDB; no alternative graph engine or hard-coded impact answer is used.

```cypher
MATCH p=(s:Service)-[:DEPENDS_ON*1..8]->(root:Service {id:$service})
RETURN s.id, s.name, s.criticality,
       [n IN nodes(p) | n.name], length(p)
ORDER BY length(p), s.id
```

The failed service is at the right-hand end: this finds its dependents, not its dependencies. Results are grouped by service while preserving supporting paths. Eight hops bound traversal; larger graphs can have additional impacts beyond that limit. Enumerating all paths is appropriate for this small demo, not arbitrary production-scale graphs.

```cypher
MATCH (i:Investigation)-[:ABOUT]->(s:Service {id:$service})
RETURN i.id, i.created, i.summary
ORDER BY i.created DESC LIMIT 5
```

Task approval uses `MERGE` with a stable task ID, so approving twice does not create duplicates.

## Architecture and files

Browser HTML/CSS/JS → local Flask API → restricted graph tools → FalkorDB.
The optional Gemini tool loop calls these same graph tools. FalkorDB stores topology, domain knowledge, history and tasks. Without it, investigations fail visibly.

- `app.py`: API routes, input checks and local-only server.
- `graph.py`: synthetic seed, parameterized queries, memory and task persistence.
- `agent.py`: actual model tool loop and explicitly labelled deterministic mode.
- `static/`: interface and dependency visualization, no frontend build needed. `format.js` escapes model text before rendering a limited Markdown subset.
- `tests/test_integration.py`: real database tests plus a mocked model protocol test.
- `DEMO_AND_SUBMISSION.md`: recording sequence, explanation and checklist.
- `START_HERE.md`: short beginner instructions.

## Manual setup (alternative)

If you do not already have FalkorDB, run:

```bash
docker run -d --name ripple-db -p 127.0.0.1:6379:6379 -p 127.0.0.1:3000:3000 -v ripple-data:/data falkordb/falkordb:latest --appendonly yes
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python app.py
```

Do not overwrite an existing `.env` with that copy command. Existing practice containers keep their own persistence settings. Investigations survive application/browser restarts while the database remains available. The new-container command enables AOF with a Docker volume for database restart persistence. Never delete the database container/volume during the demo. The start script does not migrate the earlier practice container to AOF.

The Docker image is `latest` for compatibility with the existing installation; record the actual image digest/server version in your submission for reproducibility.

## Tests

With FalkorDB running:

```bash
source .venv/bin/activate
python -m pip install pytest
python -m pytest tests -q
```

If Node.js is available, also run `node tests/test_format.cjs` to check safe brief formatting and UI element references. Node is not required to run Ripple.

Tests use a unique temporary graph and delete only that test graph. They do not require an API key. The model protocol test mocks the external API and is not proof of live model access. See `VALIDATION.md` for checks actually performed before delivery.

## Demonstration scenarios

- Ledger DB: six downstream services; Storefront path is three hops.
- Enable **Connect Notifications to Payments**, re-investigate Ledger DB: seven downstream services. Disable it to return to six.
- Identity: Login only. This is a separate subsystem.
- Analytics: no downstream dependents, no owner, no runbook. The app reports the gaps.
- Run the same investigation twice: the second retrieves the first through a graph relationship.
- Approve a task twice: a single task remains.

## Limits

Local single-user prototype, not production incident automation. No live telemetry, authentication, external messaging, recovery execution or real incident integrations. No causal root-cause claim. A saved report is a snapshot and can become stale when topology changes; rerun to refresh. New reports store a topology snapshot, and their map shows that snapshot. Older reports without one explicitly label the map as current topology. Snapshots and evidence are not collected in an atomic transaction; this demo assumes a single user. Restart the app after environment changes. The UI uses system fonts and has no external font dependency.

If a key is not configured, Evidence mode remains useful for verification, but do not present it as an LLM agent. Verify AI mode before recording the submission.

## AI assistance disclosure

This project was built with substantial ChatGPT/Codex assistance for implementation, documentation and tests. The participant must personally review, run, verify and understand it before submission. Do not claim independent authorship or work that was not done. Record your own changes and verification in `PARTICIPANT_NOTES.md`.

## References

- Hackathon rules: https://www.wemakedevs.org/hackathons/falkordb/rules
- FalkorDB quick start: https://docs.falkordb.com/getting-started
- Gemini function calling: https://ai.google.dev/gemini-api/docs/function-calling
- Gemini generateContent reference: https://ai.google.dev/api/generate-content
