from __future__ import annotations
import os
import streamlit as st
import time
import sys
import tempfile
import fitz
from pathlib import Path

from typing import List

import pandas as pd
from PIL import Image

project_root = os.path.dirname(os.path.abspath(__file__))
# os.chdir(project_root)
# sys.path.insert(0, project_root)
project_root = os.path.join(project_root, '..', '..')
sys.path.append(project_root)
# from build.full_process import process_doc_pics_first
from build.Manager.main import CHEMSIDB

chemsie_db = None

# ---------- Page config ----------
st.set_page_config(
    page_title="CHEMSIE - CHEMistry Suppl Info Extractor",
    layout="wide",
)
st.title("Chem Extraction Analysis")
chemsie_db = CHEMSIDB()

# # -------- Sidebar: Inputs --------
# with st.sidebar:
#     st.header("Base settings")
#     output_path = st.text_input("Output dir", value=Path(os.getcwd()), help="Path to save your local files", key="output_fpath")
#     st.markdown("---")
#     st.header("DB settings")
#     csv_path = st.text_input("CSV file path", value=".csv", help="Path to your local CSV file.", key="csv_path_input")
#     images_root = st.text_input("Images root folder", value='.dir', help="Base folder used to resolve relative image paths.", key="images_path_input")


tab_process, tab_database, tab_output_ls, tab_input_ls = st.tabs(["File Processor", "View Results", "Send to Label-studio", "Update from Label-studio"])

####
#### Tab 1
####

def process_pdf(pdf_path: Path, chemsie_db):
    chemsie_db.process_single_extracted_file(str(pdf_path))

with tab_process:
    database_name = st.text_input("Database name:", value="My CHEMSIE database", help="Name that will be given to your db", key="db_name")
    uploaded_files = st.file_uploader("Drag and drop files here", accept_multiple_files=True)

    if uploaded_files and st.button("Run processing"):
        progress = st.progress(0)
        with tempfile.TemporaryDirectory() as tmpdir:
            for i, uploaded_file in enumerate(uploaded_files):
                st.write(f"Processing {uploaded_file.name}")

                pdf_path = os.path.join(tmpdir, uploaded_file.name) # tmpdir + uploaded_file.name
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.write(f"Mounted temp file, running extractor")

                process_pdf(pdf_path, chemsie_db)

                progress.progress((i + 1) / len(uploaded_files))
        
        st.write(f"Finished Extraction, setting db")
        chemsie_db.setup_database(database_name = database_name)
        st.session_state["generated_csv_fpath"] = chemsie_db.database_csv_path
        st.session_state["generated_images_fpath"] = chemsie_db.image_dir_path
        st.success("All files processed")

####
#### Tab 2
####

with tab_database:    
        # -------- Helpers --------
        @st.cache_data(show_spinner=False)
        def load_df(path: str) -> pd.DataFrame:
            p = Path(path)
            if not p.exists():
                st.warning(f"CSV not found: {p.resolve()}")
                return pd.DataFrame()
            try:
                df = pd.read_csv(p)
            except Exception:
                df = pd.read_csv(p, sep="\t")
            return df

        @st.cache_data(show_spinner=False)
        def resolve_paths(img_root: str, paths: List[str]) -> List[Path]:
            root = Path(img_root)
            out = []
            for raw in paths:
                raw = raw.strip()
                if not raw:
                    continue
                p = Path(raw)
                out.append(p if p.is_absolute() else (root / p))
            return out

        @st.cache_data(show_spinner=False)
        def load_thumbnail(path: Path, max_size: int) -> Image.Image | None:
            try:
                im = Image.open(path)
                im.thumbnail((max_size, max_size))
                return im
            except Exception:
                return None

        # def setup_st_text_area(row, col_name):
        #     original_text = str(row.get(col_name, ""))
        #     updated_text = st.text_area(col_name, value=original_text, key=f"{col_name}_text_{i}")
        #     return original_text, updated_text
        
        # if chemsie_db.has_data():
        #     csv_path = st.session_state.get("generated_csv_fpath") # , st.session_state.get("csv_path_input")
        #     images_fpath = st.session_state.get("generated_images_fpath") #, st.session_state.get("images_path_input"))
        # else:
        
        csv_path = st.text_input("CSV file path", value=chemsie_db.database_csv_path, help="Path to your local CSV file.", key="input_csv_path")
        images_fpath = st.text_input("Images root folder", value=chemsie_db.image_dir_path, help="Base folder used to resolve relative image paths.", key="input_images_fpath")
        
        if csv_path!='.csv' and images_fpath!='.dir':
            chemsie_db.load_database(csv_path, images_fpath)

        st.markdown("---")
        st.subheader("View setting")
        page_size = st.number_input("Items per page", 1, 64, 12)
        thumb_size = st.number_input("Thumbnail max size (px)", 64, 1024, 320)

        st.markdown("---")
        st.subheader("Filter")
        
        ###########
        ### EDIT ##
        ###########
        query = st.text_input("Search in text (simple contains)", value="")

        if csv_path and images_fpath:
            # -------- Load data --------
            df = load_df(csv_path)
            if df.empty:
                st.info("Provide a valid CSV path in the sidebar to begin.")
                st.stop()

            id_col = "molecule_name"
            hnmr_col = "1H NMR"
            cnmr_col = "13C NMR"
            ir_col = "IR"
            ms_col = "MS"
            img_col = "image_path"
            all_cols = [id_col, hnmr_col, cnmr_col, ir_col, ms_col, img_col]
            all_cols = [col for col in all_cols if col in df.columns]
            # missing_cols = [c for c in all_cols if c and c not in df.columns]
            # if missing_cols:
            #     st.error(f"Missing columns in CSV: {missing_cols}. Available: {list(df.columns)}")
            #     st.stop()

            ###############################
            ########## EDIT ###############
            ###############################
            # -------- Filtering --------
            work_df = df.copy()
            if query and hnmr_col in work_df.columns:
                work_df = work_df[work_df[hnmr_col].fillna("").str.contains(query, case=False, na=False)]

            # Reset index after filtering
            work_df = work_df.reset_index(drop=True)

            # -------- Pagination --------
            N = len(work_df)
            if N == 0:
                st.warning("No rows match the current filter.")
                st.stop()

            page = st.number_input("Page", 1, max(1, (N - 1) // page_size + 1), 1)
            start = (page - 1) * page_size
            end = min(start + page_size, N)

            # -------- Grid display --------
            cols_per_row = 3
            cols = st.columns(cols_per_row)

            edited_rows = []  # (row_idx_in_work_df, updated_text, updated_labels)

            for i in range(start, end):
                row = work_df.iloc[i]
                col = cols[(i - start) % cols_per_row]
                with col:
                    st.markdown("---")
                    st.caption(f"Row {i+1} / {N}")
                    st.write(f"**{id_col}:** {row.get(id_col, '')}")

                    # Show images (can be multiple)
                    raw_paths = str(row.get(img_col, ""))
                    paths = [p for p in (raw_paths.split(";") if raw_paths else []) if p.strip()]
                    resolved = resolve_paths(images_fpath, paths)
                    images = []
                    for p in resolved:
                        thumb = load_thumbnail(p, int(thumb_size))
                        if thumb is not None:
                            images.append((p, thumb))
                    if images:
                        st.image([im for _, im in images], caption=[str(p.name) for p, _ in images])
                    else:
                        st.info("No images found / failed to load.")

                    # Text
                    st.text_area(hnmr_col, value=row.get(hnmr_col), key=f"{hnmr_col}_text_{i}") 
                    st.text_area(cnmr_col, value=row.get(cnmr_col), key=f"{cnmr_col}_text_{i}") 
                    st.text_area(ir_col, value=row.get(ir_col), key=f"{ir_col}_text_{i}") 
                    st.text_area(ms_col, value=row.get(ms_col), key=f"{ms_col}_text_{i}") 
            # -------- Optional: table preview --------
            with st.expander("Data table preview"):
                st.dataframe(work_df[[c for c in [id_col, hnmr_col] if c and c in work_df.columns]]) # img_col, labels_col

            st.markdown("---")
            st.markdown(
                """
            **Tips**
            - Use semicolons to store multiple image paths per row in the image column.
            - Keep relative paths short by setting the *Images root folder* to the directory that contains all images.
            - For heavier datasets, consider converting images to web-resolution copies for snappier browsing.
                """
            )

####
#### Tab 3
####

with tab_output_ls:
    pass


####
#### Tab 4
####

with tab_input_ls:
    pass