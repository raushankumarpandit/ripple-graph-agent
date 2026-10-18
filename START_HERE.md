# Start here — Ripple

## Replacing your previous version

1. In the terminal running the old app, press **Control+C**.
2. Extract the new ZIP into a **new folder** so you keep your previous copy.
3. Keep Docker Desktop running. Do not delete the database container or volume.
4. Open the new `ripple` folder in VS Code: **File → Open Folder**.
5. Choose **Terminal → New Terminal**, type the following, then press Return:

```bash
bash start.command
```

6. Open http://localhost:5050. If you still see the old design, press **Command+Shift+R**.
7. The app reuses your existing database and investigations when using the same container and graph settings. You only need **Load sample system** when the graph is empty.

## Add your API key later

The download contains no API key. The first launch creates `.env` from `.env.example`.

1. Stop the app with **Control+C**.
2. Open `.env` in VS Code. Add your key after `GEMINI_API_KEY=`.
3. Restart with `bash start.command`.
4. Select **AI investigator · Gemini** and click **Investigate impact**.

Keep the key in `.env`, not in Python or JavaScript source. Never upload `.env` to GitHub. You can use **Graph evidence · no AI required** immediately without a key.

## Try the redesigned workspace

1. Select **Ledger DB**. Leave **Connect Notifications to Payments** off.
2. Click **Investigate impact**. Expect **6** potentially affected services.
3. Open **Evidence** to follow the paths; click map nodes to inspect dependencies.
4. Open **Tool activity** to see actual graph tool results.
5. Turn on **Connect Notifications to Payments**, then run again. Expect **7**.
6. Review the suggested response and click **Approve response task** to save a local task.
7. Use **History** to reopen reports or **Download report** to save JSON.

The **?** button explains the workflow. Graph evidence mode follows stored connections without an AI model; AI mode also generates a written brief.

## Before submission

Read `README.md` for setup and architecture, `DEMO_AND_SUBMISSION.md` for the recording flow, and `VALIDATION.md` for tested behavior. Fill `PARTICIPANT_NOTES.md` with your own results and contribution. Upload the source and record a working demo; these steps are not performed by this download.
