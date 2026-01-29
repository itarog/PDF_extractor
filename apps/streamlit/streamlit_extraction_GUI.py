# apps/streamlit/streamlit_extraction_GUI.py
from __future__ import annotations
import os
import streamlit as st
import sys
import json
import tempfile
import fitz
from pathlib import Path
from typing import List, Dict
import io

import pandas as pd
from PIL import Image

# --- New pipeline import ---
# This assumes the project is installed in the Conda env.
from chemsie.pipeline import run_extraction
from chemsie.schemas import Molecule, BoundingBox

# ---------- Page config ----------
st.set_page_config(
    page_title="CHEMSIE - CHEMistry Suppl Info Extractor",
    layout="wide",
)
st.title("ChemSIE Extractor")

# ----- Session State Initialization -----
if "processing_queue" not in st.session_state:
    st.session_state.processing_queue = {}
if "extraction_results" not in st.session_state:
    st.session_state.extraction_results: Dict[str, List[Molecule]] = {}
if "pdf_files_bytes" not in st.session_state:
    st.session_state.pdf_files_bytes: Dict[str, bytes] = {}

# Create tabs
tab_process, tab_database = st.tabs(["File Processor", "View Results"])

# ==============================================================================
# ---- Tab 1: File Processor
# ==============================================================================
with tab_process:
    st.subheader("File Processing Dashboard")

    uploaded_files = st.file_uploader("Drag and drop PDF files here", accept_multiple_files=True, type="pdf")

    # Update queue and PDF bytes cache with new uploads
    if uploaded_files:
        for uf in uploaded_files:
            if uf.name not in st.session_state.pdf_files_bytes:
                st.session_state.pdf_files_bytes[uf.name] = uf.getvalue()
            if uf.name not in st.session_state.processing_queue:
                st.session_state.processing_queue[uf.name] = {"status": "Pending", "message": "Ready to process"}

    # Display Dashboard
    if st.session_state.processing_queue:
        queue_data = [{"File": fname, "Status": info["status"], "Message": info["message"]} for fname, info in st.session_state.processing_queue.items()]
        status_table = st.dataframe(pd.DataFrame(queue_data), use_container_width=True)

        if st.button("Run Extraction"):
            pending_files = [f for f in uploaded_files if st.session_state.processing_queue[f.name]["status"] in ["Pending", "Failed"]]
            if not pending_files:
                st.info("No pending files to process.")
            else:
                progress_bar = st.progress(0)
                with tempfile.TemporaryDirectory() as tmpdir:
                    for i, uploaded_file in enumerate(pending_files):
                        fname = uploaded_file.name
                        st.session_state.processing_queue[fname].update({"status": "Processing", "message": "Extracting..."})
                        
                        # Rerun to update the table display
                        st.rerun()

                        try:
                            # Write file to temp dir to get a stable path
                            pdf_path = Path(tmpdir) / fname
                            pdf_path.write_bytes(uploaded_file.getbuffer())

                            # === THE ONLY BACKEND CALL ===
                            validated_molecules = run_extraction(pdf_path)
                            # =============================
                            
                            st.session_state.extraction_results[fname] = validated_molecules
                            st.session_state.processing_queue[fname].update({"status": "Completed", "message": f"Extracted {len(validated_molecules)} molecules."})
                        
                        except Exception as e:
                            import traceback
                            st.session_state.processing_queue[fname].update({"status": "Failed", "message": str(e)})
                            st.error(f"Failed processing {fname}: {e}")
                            st.error(traceback.format_exc())

                        progress_bar.progress((i + 1) / len(pending_files))
                
                # Final rerun to update table
                st.rerun()

# ==============================================================================
# ---- Tab 2: View Results
# ==============================================================================
with tab_database:
    # -------- Visualization Helpers (Kept from old UI) --------
    @st.cache_data(show_spinner=False)
    def highlight_provenance_on_page(pdf_bytes: bytes, page_num: int, bbox: BoundingBox, color: tuple = (1, 0, 0), width: int = 2) -> Image.Image | None:
        if not pdf_bytes or not bbox:
            return None
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page = doc.load_page(page_num - 1) # page_num is 1-based, page.load_page is 0-based
            rect = fitz.Rect(bbox.x0, bbox.y0, bbox.x1, bbox.y1)
            page.draw_rect(rect, color=color, width=width)
            pix = page.get_pixmap(dpi=200)
            doc.close()
            return Image.open(io.BytesIO(pix.tobytes("png")))
        except Exception as e:
            st.error(f"Failed to render provenance highlight: {e}")
            return None

    @st.cache_data(show_spinner=False)
    def load_thumbnail(path: str, max_size: int) -> Image.Image | None:
        try:
            p = Path(path)
            if not p.exists(): return None
            im = Image.open(p)
            im.thumbnail((max_size, max_size))
            return im
        except Exception:
            return None

    # Get all extracted molecules from the session state
    all_molecules: List[Molecule] = [mol for res in st.session_state.extraction_results.values() for mol in res]

    if not all_molecules:
        st.info("No molecules extracted yet. Please process files in the 'File Processor' tab.")
        st.stop()

    st.subheader("View settings")
    page_size = st.number_input("Items per page", 1, 64, 24)
    thumb_size = st.number_input("Thumbnail max size (px)", 64, 1024, 225)

    st.markdown("---")
    st.subheader(f"Displaying {len(all_molecules)} Extracted Molecules")

    # -------- Pagination --------
    N = len(all_molecules)
    page = st.number_input("Page", 1, max(1, (N - 1) // page_size + 1), 1)
    start = (page - 1) * page_size
    end = min(start + page_size, N)
    
    # -------- Grid display --------
    cols_per_row = 3
    grid_cols = st.columns(cols_per_row)

    for i in range(start, end):
        mol = all_molecules[i]
        col = grid_cols[(i - start) % cols_per_row]
        
        with col:
            st.markdown("---")
            st.caption(f"Molecule {i+1} / {N} (from: {mol.source_file})")
            st.text_input('Label:', value=mol.label, key=f"label_{mol.id}", disabled=True)
            st.text_input('SMILES (from image):', value=mol.smiles, key=f"smiles_{mol.id}", disabled=True)
            st.text_input('Confidence:', value=f"{mol.smiles_confidence:.2f}" if mol.smiles_confidence is not None else "N/A", key=f"conf_{mol.id}", disabled=True)

            # --- Visual Provenance ---
            if mol.provenance:
                # For simplicity, show the first provenance record
                prov = mol.provenance[0]
                if st.button("Show in PDF", key=f"show_pdf_{mol.id}"):
                    pdf_bytes = st.session_state.pdf_files_bytes.get(mol.source_file)
                    if pdf_bytes:
                        highlighted_img = highlight_provenance_on_page(
                            pdf_bytes, prov.page_number, prov.bbox
                        )
                        if highlighted_img:
                            with st.expander("Source Location in PDF", expanded=True):
                                st.image(highlighted_img, use_column_width=True)
                    else:
                        st.warning(f"Original PDF '{mol.source_file}' not found in session.")

            # --- Image Thumbnail ---
            if mol.image_path:
                thumb = load_thumbnail(mol.image_path, int(thumb_size))
                if thumb:
                    st.image(thumb, caption=f"Extracted Image: {Path(mol.image_path).name}")
            
            # --- Spectra ---
            if mol.spectra:
                with st.expander("Associated Spectra"):
                    for spectrum in mol.spectra:
                        st.text_area(spectrum.type, value=spectrum.text_representation, key=f"spec_{mol.id}_{spectrum.type}", disabled=True)
