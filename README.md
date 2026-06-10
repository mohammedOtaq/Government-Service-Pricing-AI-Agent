# Government Service Pricing AI Prototype

Local Streamlit prototype for a modular, evidence-based government service pricing journey. Each agent can run independently, produce a Markdown report, save a JSON state file, and resume from a previously uploaded state.

## Local Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Loading Sample Service
Open the app and click **Load Sample Service**. The sample data is non-confidential prototype data for `SRV-001`.

## Running Each Agent
Use the journey stage expanders in the app:
1. Service Intake
2. Policy Assessment
3. Costing
4. Benchmarking
5. Scenarios
6. Risk & Impact
7. Business Case
8. Final Recommendation

Each stage has a **Run Agent** button and can be executed independently.

## Generating Reports
After running a stage, click **Generate Report** or use the download buttons. Files are saved under `outputs/{stage}/` as Markdown and JSON.

## Uploading Previous State
Use **Upload Previous State** and select a prior `*_state.json` file. The app validates the standard agent output keys and updates journey progress so you can continue from `next_stage`.

## Final Consolidated Report
Run the **Final Recommendation** stage after enough evidence is available, or click **Run Full Journey** for the sample service. The final report blocks approval if critical policy, costing, or benchmark evidence is missing.

## Testing
```bash
python -m compileall .
pytest
```

If `pytest` is not installed:
```bash
pip install pytest
```

## Streamlit Cloud Deployment
1. Push repository to GitHub.
2. Go to Streamlit Cloud.
3. Create new app.
4. Select repository.
5. Select branch.
6. Set main file path to app.py.
7. Add secrets if needed.
8. Deploy.

## Deployment Checklist
- Main app file is `app.py`.
- Required packages are listed in `requirements.txt`.
- `.env` is ignored.
- No API keys or secrets are committed.
- Sample data is non-confidential.
- `outputs/` folders are created if missing.
- Reports and state files are local JSON/Markdown artifacts.

## Known Limitations
- Benchmark data is only analyzed when provided; the app does not search or invent benchmarks.
- SQLite persistence from Phase 1 is not expanded in this scaffold.
- Prototype reports are generated from deterministic local rules, not external AI services.
- Final approval is a readiness recommendation, not a legal approval.
