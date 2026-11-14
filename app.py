from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from docx import Document

from agents.orchestrator import JourneyOrchestrator
from models.journey_state import STAGE_LABELS, STAGE_ORDER, next_stage_for, progress_from_outputs
from reports.report_generator import generate_final_markdown, generate_stage_markdown, save_report_and_state
from reports.pdf_report import build_pricing_pdf
from utils.pdf_evidence import REQUIRED, extract_pdf
from utils.validation import load_json_bytes


load_dotenv()

SAMPLE_PATH = Path("data/sample_service.json")


def init_state() -> None:
    st.session_state.setdefault("service_data", {})
    st.session_state.setdefault("agent_outputs", {})
    st.session_state.setdefault("last_resume_stage", "")


def load_sample_service() -> None:
    st.session_state.service_data = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    st.session_state.service_json_editor = json.dumps(st.session_state.service_data, indent=2)
    st.session_state.agent_outputs = {}
    st.session_state.last_resume_stage = "service_profile"


def output_downloads(stage: str, output: dict[str, Any]) -> None:
    service = st.session_state.service_data
    all_outputs = st.session_state.agent_outputs
    report_path, state_path = save_report_and_state(output, service, all_outputs)
    report_text = report_path.read_text(encoding="utf-8")
    state_text = state_path.read_text(encoding="utf-8")
    cols = st.columns(2)
    cols[0].download_button(
        "Download Markdown Report",
        data=report_text,
        file_name=report_path.name,
        mime="text/markdown",
        key=f"download-md-{stage}",
    )
    cols[1].download_button(
        "Download JSON State",
        data=state_text,
        file_name=state_path.name,
        mime="application/json",
        key=f"download-json-{stage}",
    )
    if stage == "final":
        st.download_button(
            "Download Final PDF Report",
            data=build_pricing_pdf(report_text),
            file_name="final_pricing_report.pdf",
            mime="application/pdf",
        )


def service_editor() -> None:
    st.subheader("Service Data")
    st.session_state.setdefault("service_json_editor", json.dumps(st.session_state.service_data, indent=2))
    raw = st.text_area(
        "Edit service JSON",
        key="service_json_editor",
        height=360,
        help="Use local prototype data only. Do not paste confidential data.",
    )
    if st.button("Update Service Data"):
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                st.error("Service JSON must be an object.")
                return
            st.session_state.service_data = data
            st.session_state.agent_outputs = {}
            st.success("Service data updated.")
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")


def review_pdf_evidence(name: str, content: bytes, index: int) -> None:
    pages, fields, sources, issues = extract_pdf(content)
    if not any(text or tables for _, text, tables in pages):
        st.warning("No readable text or tables found. For scanned pages, upload a searchable copy.")
        return
    current = st.session_state.service_data
    if fields:
        st.json({key: {"value": value, "page": sources[key]} for key, value in fields.items()})
    conflicts = sorted(key for key, value in fields.items() if current.get(key) not in (None, "", value))
    if conflicts:
        st.warning("Existing values differ for " + ", ".join(conflicts))
    missing = sorted(key for key in REQUIRED if fields.get(key, current.get(key)) in (None, ""))
    if missing:
        st.warning("Missing pricing inputs: " + ", ".join(missing))
    for issue in dict.fromkeys(issues):
        st.warning(issue)
    if fields and st.button("Apply PDF inputs", key=f"apply-evidence-{index}"):
        if current.get("service_id") and fields.get("service_id", current["service_id"]) != current["service_id"]:
            st.error("The PDF service ID differs from the active service. Clear the service data before importing.")
        else:
            updated = {**current, **fields}
            st.session_state.service_data = updated
            st.session_state.service_json_editor = json.dumps(updated, indent=2)
            st.session_state.agent_outputs = {}
            st.session_state.last_resume_stage = "service_profile"
            st.success(f"Applied inputs from {name}. Run the pricing journey to refresh the analysis.")
    for page_number, text, tables in pages:
        st.write(f"Page {page_number}")
        st.text(text)
        for table in tables:
            st.dataframe(table)


def preview_evidence(name: str, content: bytes, index: int) -> None:
    extension = Path(name).suffix.lower()
    if extension == ".pdf":
        review_pdf_evidence(name, content, index)
    elif extension == ".docx":
        document = Document(BytesIO(content))
        st.text("\n".join(paragraph.text for paragraph in document.paragraphs))
        for table in document.tables:
            st.dataframe([[cell.text for cell in row.cells] for row in table.rows])
    elif extension == ".xlsx":
        with pd.ExcelFile(BytesIO(content), engine="openpyxl") as workbook:
            sheet = st.selectbox("Worksheet", workbook.sheet_names, key=f"evidence-sheet-{index}")
            st.dataframe(workbook.parse(sheet, nrows=100))
    elif extension == ".csv":
        st.dataframe(pd.read_csv(BytesIO(content), nrows=100))
    else:
        st.image(content)


def upload_evidence() -> None:
    st.subheader("Upload Supporting Documents")
    uploaded = st.file_uploader(
        "Upload government service evidence",
        type=["pdf", "docx", "xlsx", "csv", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    if uploaded:
        st.caption("Review and apply extracted PDF inputs, or enter verified details in Service Data.")
    for index, file in enumerate(uploaded):
        with st.expander(f"{index + 1}. {file.name}"):
            try:
                preview_evidence(file.name, file.getvalue(), index)
            except Exception as exc:
                st.error(f"Could not preview this file. {exc}")


def upload_state() -> None:
    st.subheader("Upload Previous State")
    uploaded = st.file_uploader("Upload a previous JSON state file", type=["json"])
    if uploaded:
        data, message = load_json_bytes(uploaded.read())
        if data is None:
            st.error(message)
            return
        stage = data["stage"]
        if stage not in STAGE_ORDER:
            st.error(f"Unknown stage in state file: {stage}")
            return
        st.session_state.agent_outputs[stage] = data
        st.session_state.last_resume_stage = data.get("next_stage") or next_stage_for(stage)
        st.success(f"Loaded {STAGE_LABELS.get(stage, stage)} state. Continue from {STAGE_LABELS.get(st.session_state.last_resume_stage, 'final review')}.")


def sidebar_progress() -> None:
    st.sidebar.header("Pricing Journey Progress")
    progress = progress_from_outputs(st.session_state.agent_outputs)
    for stage in STAGE_ORDER:
        st.sidebar.write(f"**{STAGE_LABELS[stage]}**")
        st.sidebar.caption(progress[stage])
    if st.session_state.last_resume_stage:
        st.sidebar.info(f"Resume target: {STAGE_LABELS.get(st.session_state.last_resume_stage, st.session_state.last_resume_stage)}")


def run_stage_ui(stage: str, orchestrator: JourneyOrchestrator) -> None:
    label = STAGE_LABELS[stage]
    output = st.session_state.agent_outputs.get(stage)
    with st.expander(label, expanded=stage == st.session_state.last_resume_stage or output is None):
        status = output.get("status", "not_started") if output else "not_started"
        st.write(f"Status: `{status}`")
        cols = st.columns(3)
        if cols[0].button("Run Agent", key=f"run-{stage}"):
            try:
                result = orchestrator.run_stage(stage, st.session_state.service_data, st.session_state.agent_outputs)
                st.session_state.agent_outputs[stage] = result
                st.session_state.last_resume_stage = result.get("next_stage", "")
                st.success(f"{label} completed with status: {result['status']}")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not run {label}: {exc}")
        if output and cols[1].button("Generate Report", key=f"report-{stage}"):
            save_report_and_state(output, st.session_state.service_data, st.session_state.agent_outputs)
            st.success("Report and state file saved.")
        if cols[2].button("Continue Journey", key=f"continue-{stage}"):
            next_stage = output.get("next_stage") if output else stage
            st.session_state.last_resume_stage = next_stage or stage
            st.info(f"Continue from {STAGE_LABELS.get(st.session_state.last_resume_stage, 'final review')}.")

        if output:
            st.json(output)
            output_downloads(stage, output)
            if stage == "final":
                markdown = generate_final_markdown(output, st.session_state.service_data, st.session_state.agent_outputs)
            else:
                markdown = generate_stage_markdown(output, st.session_state.service_data)
            st.markdown(markdown)


def main() -> None:
    st.set_page_config(page_title="Government Service Pricing AI Prototype", layout="wide")
    init_state()
    sidebar_progress()
    orchestrator = JourneyOrchestrator()

    st.title("Government Service Pricing AI Agent")
    st.caption("Local Streamlit prototype with modular evidence agents, staged reports, and resumable JSON state.")
    st.warning(
        "This is a prototype decision-support tool. Outputs are for testing and internal review only. "
        "Final fee decisions require validated evidence, service owner confirmation, and formal approval "
        "through the applicable governance process."
    )

    cols = st.columns(2)
    if cols[0].button("Load Sample Service"):
        load_sample_service()
        st.success("Sample service loaded.")
        st.rerun()
    if cols[1].button("Run Full Journey"):
        if not st.session_state.service_data:
            st.error("Load or enter service data first.")
        else:
            st.session_state.agent_outputs = orchestrator.run_all(st.session_state.service_data, st.session_state.agent_outputs)
            st.session_state.last_resume_stage = "final"
            if "_journey_warning" in st.session_state.agent_outputs:
                warning = st.session_state.agent_outputs["_journey_warning"]
                st.warning(f"{warning['message']} Final approval blocked: {warning['blocks_final_approval']}")
            else:
                st.success("Full journey completed.")
            st.rerun()

    state_col, evidence_col = st.columns(2)
    with state_col:
        upload_state()
    with evidence_col:
        upload_evidence()

    if not st.session_state.service_data:
        st.info("Load the sample service or enter service data to begin.")
        st.session_state.service_data = {}

    service_editor()

    if st.session_state.service_data:
        st.subheader("Journey Stages")
        for stage in STAGE_ORDER:
            run_stage_ui(stage, orchestrator)

        st.subheader("Available Outputs")
        rows = [
            {"stage": STAGE_LABELS[stage], "status": output.get("status"), "blocks_final_approval": output.get("blocks_final_approval")}
            for stage, output in st.session_state.agent_outputs.items()
            if stage in STAGE_LABELS
        ]
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        if "_journey_warning" in st.session_state.agent_outputs:
            warning = st.session_state.agent_outputs["_journey_warning"]
            st.warning(f"{warning['message']} Final approval blocked: {warning['blocks_final_approval']}")


if __name__ == "__main__":
    main()
