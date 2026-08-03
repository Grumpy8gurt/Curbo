# CURBO Sprint 4 Local Work Prompt

Use this file to continue the reviewed Sprint 4 work from a local ChatGPT Work
or Codex session. Open the CURBO repository as the workspace, then give the
session this instruction:

The reviewed work started from `origin/main` commit `0ee27f6` ("Merge Sprint 4
annotation review milestone"). If the remote has advanced, inspect and resolve
the resulting diff instead of overwriting newer work.

> Read `CURBO_SPRINT4_WORK_PROMPT.md`, `docs/planning-review-rationale.md`, and
> the four required Sprint 4 documents before changing code. Inspect the whole
> diff and preserve CURBO's existing React/FastAPI/MapLibre architecture. Finish
> the status-aware corridor review, curb-ramp field-review prompts, readable
> HTML report, focused automated tests, and civic-dashboard frontend polish.
> Do not add routing, live crash ingestion, ML, image upload, a compliance
> score, or another major feature. Run `./scripts/verify_sprint4.sh`, resolve any
> failure, compare the frontend types and fallback objects with the FastAPI
> response schema, then commit the implementation/tests and documentation as
> meaningful separate commits. Push `agent/curbo-planner-quality` and open a
> draft pull request into `main`. Do not claim manual or Docker verification
> that was not actually performed on this device.

## Intended Sprint 4 Outcome

- Complete the existing annotation Update workflow and prove status changes
  survive an application restart.
- Make corridor concerns status-aware: rejected observations stay in history
  but do not increase active concern counts or review attention.
- Show bicycle-network gaps, intersection-safety notes, parking/loading
  conflicts, missing curb cuts, annotations needing review, review signals,
  and a clear data-limitation disclaimer.
- Preserve and display published curb-ramp left/right grades and use published
  dimensional references only as field-review prompts.
- Generate readable HTML corridor evidence instead of a raw dictionary.
- Improve visual hierarchy, responsive behavior, keyboard focus, contrast, and
  activity announcements without replacing the map workflow.
- Keep backend schema, frontend types, offline fallbacks, report output, tests,
  documentation synchronized.

## Files That Carry the Evidence

- Capability and API: `backend/app/services/spatial_queries.py`,
  `backend/app/schemas/corridors.py`, `backend/app/services/report_generator.py`
- Measurement preservation: `backend/app/services/eugene_data_service.py`
- Frontend contract and review UI: `frontend/src/types/corridors.ts`,
  `frontend/src/components/ReportPanel.tsx`, `frontend/src/utils/mapHelpers.ts`
- State synchronization: `frontend/src/App.tsx`
- Focused tests: `backend/tests/` and the `*.test.ts(x)` files under
  `frontend/src/`
- Engineering evidence: `README.md`, `docs/architecture.md`,
  `docs/manual-verification.md`, `docs/ai-implementation-review.md`, and
  `docs/planning-review-rationale.md`

## Local Setup and Verification

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ../frontend
npm install
cd ..
./scripts/verify_sprint4.sh
```

If the virtual environment is stored elsewhere, run:

```bash
PYTHON_BIN=/absolute/path/to/python ./scripts/verify_sprint4.sh
```

The verifier checks Docker Compose configuration when Docker is available and
reports a skip otherwise.

## Safe Publication Commands

Check GitHub authentication and the exact diff before staging:

```bash
gh --version
gh auth status
git status --short
git diff --check
git diff --stat
```

The target branch is `agent/curbo-planner-quality`, based on `main`. If it does
not exist locally yet:

```bash
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c agent/curbo-planner-quality
```

After verification, stage only reviewed Sprint 4 files. Prefer two meaningful
commits so the history shows engineering evolution:

```bash
git add backend frontend
git commit -m "Improve status-aware corridor review quality"
git add README.md CURBO_SPRINT4_WORK_PROMPT.md docs scripts tests
git commit -m "Document Sprint 4 research and verification evidence"
git push -u origin agent/curbo-planner-quality
gh pr create --draft --base main --head agent/curbo-planner-quality --title "Improve CURBO planner review quality"
```

Review the staged diff before each commit. If unrelated local changes are
present, do not stage or overwrite them. Merge the pull request into `main`
only after the checks and documentation match the final remote commit.

## Canvas Submission Text

- Repository URL: `https://github.com/Grumpy8gurt/Curbo`
- Sprint 4 branch: `agent/curbo-planner-quality`
- Completed capability: CURBO completes status-aware annotation review by
  persisting reviewer decisions and reflecting active concerns in corridor
  analysis and reports.
- Most important quality improvement: The corridor API, frontend, fallback
  contract, HTML report, tests, and limitations now agree on explainable review
  signals while rejected observations no longer inflate active concern counts.
- Most valuable automated test: The corridor status test creates three concern
  types, changes their review states, and proves rejected notes are excluded
  while confirmed evidence remains active.
