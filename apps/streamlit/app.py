"""
Streamlit Dataset GUI

Purpose
- Browse a dataset where each row has text and one or more image paths
- Paths to images are local (absolute or relative). Relative paths are resolved against an "Images root" folder you choose in the sidebar.
- Quick search/filter, pagination, basic editing of text/labels, and save-back to CSV.

Assumptions
- Your CSV has at least these columns: an ID column (e.g., "id"), a text column (e.g., "text"), and an image path column (e.g., "image_path").
- If an entry has multiple images, the paths are separated by semicolons (e.g., "img1.jpg;img2.jpg").
- You can customize which columns to use in the sidebar.

Run
pip install streamlit pandas pillow
streamlit run app.py

Rename this file to app.py (or update the run command accordingly).
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import List

import pandas as pd
from PIL import Image
import streamlit as st


import argparse

st.set_page_config(page_title="Dataset GUI", layout="wide")
st.title("📂 Dataset GUI: Your extracted molecules and nerves")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv_fpath", type=str, default="")
    parser.add_argument("--images_fpath", type=str, default="")
    # parser.add_argument("--threshold", type=float, default=0.5)
    # parser.add_argument("--mode", choices=["fast", "accurate"], default="fast")
    # parse_known_args() is resilient if anything unexpected slips in
    args, _ = parser.parse_known_args()
    return args

args = parse_args()

# Use CLI values as widget defaults (initialize once)
if "initialized_from_cli" not in st.session_state:
    st.session_state.update(
        csv_fpath=args.csv_fpath,
        images_fpath=args.images_fpath,
        initialized_from_cli=True
    )


# -------- Sidebar: Inputs --------
with st.sidebar:
    st.header("Settings")
    csv_path = st.text_input("CSV file path", value="./PDF_extractor/with_photo_database_1/with_photo_database_1.csv", help="Path to your local CSV file.", key="csv_fpath")
    images_root = st.text_input("Images root folder", value='./PDF_extractor/with_photo_database_1/', help="Base folder used to resolve relative image paths.", key="images_fpath")

    st.markdown("---")
    st.subheader("Columns")
    id_col = st.text_input("ID column", value="molecule_name")
    text_col = st.text_input("1H NMR", value="1H NMR")
    text_col_2 = st.text_input("13C NMR", value="13C NMR")
    text_col_3 = st.text_input("IR", value="IR")
    text_col_4 = st.text_input("MS", value="MS")
    img_col = st.text_input("Image path column", value="image_path")
    labels_col = st.text_input("Optional labels column", value="", help="Optional column used for tags/labels; leave empty if none.")

    st.markdown("---")
    st.subheader("View")
    page_size = st.number_input("Items per page", 1, 64, 12)
    thumb_size = st.number_input("Thumbnail max size (px)", 64, 1024, 320)

    st.markdown("---")
    st.subheader("Filter")
    
    ###########
    ### EDIT ##
    ###########
    query = st.text_input("Search in text (simple contains)", value="")

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

def setup_st_text_area(row, col_name):
    original_text = str(row.get(col_name, ""))
    updated_text = st.text_area(col_name, value=original_text, key=f"{col_name}_text_{i}")
    return original_text, updated_text


# -------- Load data --------
df = load_df(csv_path)
if df.empty:
    st.info("Provide a valid CSV path in the sidebar to begin.")
    st.stop()

###############################
########## EDIT ###############
###############################

missing_cols = [c for c in [id_col, text_col, img_col] if c and c not in df.columns]
if missing_cols:
    st.error(f"Missing columns in CSV: {missing_cols}. Available: {list(df.columns)}")
    st.stop()

# -------- Filtering --------
work_df = df.copy()
if query and text_col in work_df.columns:
    work_df = work_df[work_df[text_col].fillna("").str.contains(query, case=False, na=False)]

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
        resolved = resolve_paths(images_root, paths)
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
        hnmr_text, new_hnmr_text = setup_st_text_area(row, text_col)
        cnmr_text, new_cnmr_text = setup_st_text_area(row, text_col_2)
        ir_text, new_ir_text = setup_st_text_area(row, text_col_3)
        ms_text, new_ms_text = setup_st_text_area(row, text_col_4)

        # current_labels = ""
        # new_labels = None
        # if labels_col and labels_col in work_df.columns:
        #     current_labels = str(row.get(labels_col, ""))
        #     new_labels = st.text_input("Labels (comma-separated)", value=current_labels, key=f"labels_{i}")


        # Optional labels editing
        # if new_text != current_text: #  or (labels_col and new_labels is not None and new_labels != current_labels)
        #     edited_rows.append((i, new_text)) # , new_labels

# -------- Save changes --------
# if edited_rows:
#     st.markdown("---")
#     st.subheader("Pending changes")
#     st.write(f"You modified {len(edited_rows)} row(s). Click **Save** to write back to the CSV.")
#     if st.button("💾 Save changes to CSV"):
#         # Apply edits back to original df by mapping through filtered index
#         for i, new_text, new_labels in edited_rows:
#             # Map work_df index to original df index
#             original_idx = work_df.index[i]
#             df.at[original_idx, text_col] = new_text
#             if labels_col and labels_col in df.columns and new_labels is not None:
#                 df.at[original_idx, labels_col] = new_labels
#         # Backup and save
#         csv_path_obj = Path(csv_path)
#         backup_path = csv_path_obj.with_suffix(csv_path_obj.suffix + ".bak")
#         try:
#             df.to_csv(backup_path, index=False)
#             df.to_csv(csv_path_obj, index=False)
#             st.success(f"Saved! Backup written to {backup_path}")
#         except Exception as e:
#             st.error(f"Failed to save: {e}")
# else:
#     st.caption("No edits yet.")

# -------- Optional: table preview --------
with st.expander("Data table preview"):
    st.dataframe(work_df[[c for c in [id_col, text_col, img_col, labels_col] if c and c in work_df.columns]])

st.markdown("---")
st.markdown(
    """
**Tips**
- Use semicolons to store multiple image paths per row in the image column.
- Keep relative paths short by setting the *Images root folder* to the directory that contains all images.
- For heavier datasets, consider converting images to web-resolution copies for snappier browsing.
    """
)