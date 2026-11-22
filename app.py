import io
import json
import os
import time
from datetime import datetime
from pathlib import Path
import httpx
import pandas as pd
import streamlit as st

# Configure Streamlit page layout
st.set_page_config(
    page_title="AI Project Documentation Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1B365D;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4A5568;
        margin-bottom: 1.5rem;
    }
    .status-card {
        padding: 1rem;
        border-radius: 8px;
        background-color: #F7FAFC;
        border: 1px solid #E2E8F0;
        margin-bottom: 1rem;
    }
    .metric-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-digital { background-color: #EBF8FF; color: #2B6CB0; }
    .badge-scanned { background-color: #FEFCBF; color: #B7791F; }
    .badge-mixed { background-color: #E9D8FD; color: #6B46C1; }
</style>
""", unsafe_allow_html=True)

# Application Configuration
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000").rstrip("/")

# Initialize session state variables
if "current_doc_id" not in st.session_state:
    st.session_state.current_doc_id = None
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None
if "processing_complete" not in st.session_state:
    st.session_state.processing_complete = False
if "docx_ready" not in st.session_state:
    st.session_state.docx_ready = False


def check_backend_health():
    """Checks FastAPI backend and services connectivity."""
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{BACKEND_URL}/health")
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None


# Sidebar Navigation & System Diagnostics
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/documents.png", width=64)
    st.markdown("### System Diagnostics")

    health = check_backend_health()
    if health:
        st.success("Backend API: Online")
        ollama_info = health.get("ollama", {})
        if ollama_info.get("status") in ["healthy", "ready"]:
            st.success(f"Ollama: Ready ({ollama_info.get('configured_model')})")
        else:
            st.warning(f"Ollama: {ollama_info.get('status', 'Offline')}")

        tesseract_info = health.get("tesseract", {})
        if tesseract_info.get("installed"):
            st.success("Tesseract OCR: Enabled")
        else:
            st.info("Tesseract OCR: Not installed (Digital PDF mode only)")
    else:
        st.warning("Backend API: Offline\n(Ensure FastAPI is running at localhost:8000)")

    st.markdown("---")
    st.markdown("### Navigation")
    menu = st.radio(
        "Go to",
        ["Dashboard & Upload", "Review & Edit", "Document History", "About & Architecture"],
        index=0
    )


# Section 1: Dashboard & Upload
if menu == "Dashboard & Upload":
    st.markdown('<div class="main-title">AI-Powered Project Documentation Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Extract Terms of Reference, Project Charters, and SRS PDFs into structured, editable Word documents.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1.8, 1.2])

    with col1:
        st.markdown("#### Upload Project Document")
        uploaded_file = st.file_uploader(
            "Choose a project requirements PDF (Digital or Scanned)",
            type=["pdf"],
            help="Accepts ToR, SRS, proposals, or RFP PDFs up to 25 MB."
        )

        if uploaded_file is not None:
            st.info(f"Selected file: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
            if st.button("🚀 Ingest & Extract Information", type="primary", use_container_width=True):
                with st.spinner("Uploading and analyzing document..."):
                    try:
                        # Upload to FastAPI backend
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                        with httpx.Client(timeout=30.0) as client:
                            upload_res = client.post(f"{BACKEND_URL}/api/documents/upload", files=files)

                        if upload_res.status_code == 202:
                            data = upload_res.json()
                            doc_id = data["document_id"]
                            st.session_state.current_doc_id = doc_id
                            st.success("Upload verified! Document extraction initiated.")

                            # Polling for processing status
                            progress_bar = st.progress(15, text="Extracting text from PDF...")
                            status_placeholder = st.empty()

                            completed = False
                            for attempt in range(60):  # poll up to 120s
                                time.sleep(2)
                                with httpx.Client(timeout=5.0) as client:
                                    status_res = client.get(f"{BACKEND_URL}/api/documents/{doc_id}/status")
                                if status_res.status_code == 200:
                                    s_data = status_res.json()
                                    p_status = s_data.get("processing_status")
                                    status_placeholder.info(f"Current Phase: **{p_status}**")

                                    if p_status == "EXTRACTING":
                                        progress_bar.progress(35, text="Detecting text layout and running OCR...")
                                    elif p_status == "ANALYZING":
                                        progress_bar.progress(65, text="Synthesizing project information with Ollama...")
                                    elif p_status == "VALIDATING":
                                        progress_bar.progress(85, text="Validating schema and anti-hallucination guardrails...")
                                    elif p_status in ["READY_FOR_REVIEW", "COMPLETED"]:
                                        progress_bar.progress(100, text="Extraction Complete!")
                                        completed = True
                                        break
                                    elif p_status == "FAILED":
                                        st.error(f"Processing failed: {s_data.get('error_message')}")
                                        break

                            if completed:
                                # Fetch result
                                with httpx.Client(timeout=5.0) as client:
                                    result_res = client.get(f"{BACKEND_URL}/api/documents/{doc_id}/result")
                                if result_res.status_code == 200:
                                    st.session_state.extracted_data = result_res.json().get("extracted_data")
                                    st.session_state.processing_complete = True
                                    st.success("Extraction succeeded! Proceed to 'Review & Edit' to inspect and confirm.")
                        else:
                            st.error(f"Upload rejected: {upload_res.text}")
                    except Exception as e:
                        st.error(f"Failed to communicate with backend: {str(e)}")

    with col2:
        st.markdown("#### Extraction Specifications")
        st.markdown("""
        The engine extracts 5 foundational project dimensions:
        1. **Project Title**: Formal name, sponsor, and acronym.
        2. **Scope of Work**: Deliverables, boundaries, and acceptance goals.
        3. **Objectives**: Quantifiable primary & secondary targets.
        4. **Methodology**: Sequential technical execution steps & QA.
        5. **Project Timeline**: Milestone schedules, dates, and durations.

        ---
        **Anti-Hallucination Guarantee**:
        - All unmentioned parameters are recorded as:  
          `"Not specified in the source document"`.
        - Source page numbers are tracked for every milestone.
        """)


# Section 2: Review & Edit
elif menu == "Review & Edit":
    st.markdown('<div class="main-title">Human-in-the-Loop Review & Verification</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Inspect, refine, and approve extracted project information before generating the official Word document.</div>', unsafe_allow_html=True)

    if not st.session_state.extracted_data:
        st.warning("No active document loaded. Please upload a PDF in the 'Dashboard & Upload' section first.")
    else:
        data = st.session_state.extracted_data

        # Form for reviewing and editing
        with st.form("review_form"):
            st.markdown("### 1. Project Title")
            proj_title = st.text_input("Project Name", value=data.get("project_title", ""))

            st.markdown("### 2. Scope of Work")
            scope_text = st.text_area("Scope Narrative & Deliverables", value=data.get("scope_of_work", ""), height=130)

            st.markdown("### 3. Project Objectives")
            raw_objs = "\n".join(data.get("objectives", []))
            objs_text = st.text_area("Objectives (One per line)", value=raw_objs, height=110)

            st.markdown("### 4. Methodology Steps")
            methodology_list = data.get("methodology", [])
            method_df = pd.DataFrame(methodology_list)
            if not method_df.empty:
                st.dataframe(method_df, use_container_width=True)
            else:
                st.info("No explicit methodology steps detected in source PDF.")

            st.markdown("### 5. Project Timeline & Milestones")
            timeline_list = data.get("project_timeline", [])
            timeline_df = pd.DataFrame(timeline_list)
            if not timeline_df.empty:
                st.dataframe(timeline_df, use_container_width=True)
            else:
                st.info("No timeline milestones detected in source PDF.")

            # Missing info and warnings
            missing_info = data.get("missing_information", [])
            if missing_info:
                st.markdown("#### ⚠ Missing Information Detected in Source PDF:")
                for item in missing_info:
                    st.warning(item)

            submitted = st.form_submit_button("💾 Save Revisions & Generate Word Document", type="primary")

            if submitted:
                # Update data model with user edits
                data["project_title"] = proj_title
                data["scope_of_work"] = scope_text
                data["objectives"] = [line.strip() for line in objs_text.split("\n") if line.strip()]

                with st.spinner("Generating Microsoft Word (.docx) document..."):
                    try:
                        doc_id = st.session_state.current_doc_id
                        with httpx.Client(timeout=30.0) as client:
                            gen_res = client.post(
                                f"{BACKEND_URL}/api/documents/{doc_id}/generate",
                                json={"reviewed_data": data}
                            )

                        if gen_res.status_code == 200:
                            st.session_state.docx_ready = True
                            st.success("Word document successfully synthesized with corporate typography and tables!")
                        else:
                            st.error(f"Document generation failed: {gen_res.text}")
                    except Exception as e:
                        st.error(f"Error connecting to backend: {e}")

        # Download button if Word document was generated
        if st.session_state.docx_ready and st.session_state.current_doc_id:
            doc_id = st.session_state.current_doc_id
            st.markdown("---")
            st.markdown("### 📥 Download Word Document")
            try:
                with httpx.Client(timeout=10.0) as client:
                    dl_res = client.get(f"{BACKEND_URL}/api/documents/{doc_id}/download")

                if dl_res.status_code == 200:
                    st.download_button(
                        label="📄 Download Official Project Specification (.docx)",
                        data=dl_res.content,
                        file_name=f"Project_Specification_{doc_id[:8]}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary"
                    )
            except Exception as ex:
                st.error(f"Error fetching download: {ex}")


# Section 3: Document History
elif menu == "Document History":
    st.markdown('<div class="main-title">Document Processing History</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Previously processed requirements documents and generated Word files.</div>', unsafe_allow_html=True)

    try:
        with httpx.Client(timeout=5.0) as client:
            hist_res = client.get(f"{BACKEND_URL}/api/documents")
        if hist_res.status_code == 200:
            records = hist_res.json()
            if records:
                df = pd.DataFrame(records)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No documents have been processed yet.")
        else:
            st.error("Failed to load history.")
    except Exception as e:
        st.error(f"Could not reach backend: {e}")


# Section 4: About & Architecture
elif menu == "About & Architecture":
    st.markdown('<div class="main-title">System Architecture & Engineering Design</div>', unsafe_allow_html=True)
    st.markdown("""
    ### Project Overview
    This application automates the conversion of unstructured project documents (Terms of Reference, Statements of Work, Software Requirements Specifications) into standardized, corporate-ready Microsoft Word documents.

    ### Architectural Pillars
    1. **Hybrid Ingestion**: High-throughput digital parsing with **PyMuPDF**, with seamless fallback to **Tesseract OCR** for scanned images.
    2. **Local AI Inference**: Zero data leakage using **Ollama** running local Llama 3 / Qwen models.
    3. **Anti-Hallucination & Provenance**: Hard schema constraints with **Pydantic**; missing values default to `"Not specified in the source document"`.
    4. **Enterprise Document Rendering**: Programmatic `.docx` construction using **python-docx** with corporate color palettes, cover page, and styled milestone tables.
    5. **Human-in-the-Loop**: Comprehensive interactive review screen before final report authorization.
    """)
