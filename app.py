from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from agents.orchestrator import JourneyOrchestrator
from models.journey_state import STAGE_LABELS, STAGE_ORDER, next_stage_for, progress_from_outputs
from reports.report_generator import generate_final_markdown, generate_stage_markdown, save_report_and_state
from utils.validation import load_json_bytes


load_dotenv()

SAMPLE_PATH = Path("data/sample_service.json")


def init_state() -> None:
    st.session_state.setdefault("service_data", {})
    st.session_state.setdefault("agent_outputs", {})
    st.session_state.setdefault("last_resume_stage", "")


def load_sample_service() -> None:
    st.session_state.service_data = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
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


def service_editor() -> None:
    st.subheader("Service Data")
    raw = st.text_area(
        "Edit service JSON",
        value=json.dumps(st.session_state.service_data, indent=2),
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
            st.success("Service data updated.")
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")


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

    upload_state()

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
