import json
from pathlib import Path

import pandas as pd
import streamlit as st


# ---------- Data loading ----------

@st.cache_data
def load_results(path: str):
    p = Path(path)
    if not p.exists():
        st.error(f"File not found: {p.resolve()}")
        return []

    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Add index so we can refer back to original order
    for i, d in enumerate(data):
        d.setdefault("_idx", i)
    return data


# ---------- Page config ----------

st.set_page_config(
    page_title="Chem Extraction Analysis (Text + Mol Images)",
    layout="wide",
)

st.title("Chem Extraction Analysis")

# ---------- Sidebar: data path ----------

st.sidebar.header("Data")

data_file = st.sidebar.text_input("Path to results JSON", "results_with_images.json")
data = load_results(data_file)
if not data:
    st.stop()

df = pd.DataFrame(data)

# Ensure expected columns exist so nothing crashes
text_cols = [
    "gt_text",
    "ext_text",
    "gt_peaks",
    "extracted_peaks",
    "sim_score",
    "precision",
    "recall",
    "f1",
    "TP",
    "FN",
    "FP",
]

mol_cols = [
    "gt_mol_name",
    "extracted_mol_name",
    "mol_name_score",
    "smiles_sim",
    "gt_molpic_path",
    "extracted_molpic_path",
]

for col in text_cols + mol_cols:
    if col not in df.columns:
        df[col] = None

# ---------- Tabs ----------

tab_text, tab_mol = st.tabs(["Text / Peak Analysis", "Molecule Image Analysis"])


# ======================================================================
# TAB 1: TEXT / PEAK ANALYSIS
# ======================================================================
with tab_text:
    st.header("Text / Peak Error Analysis")

    # ---------- Summary section ----------
    st.subheader("Overall Summary (Text / Peaks)")

    metric_cols = ["precision", "recall", "f1"]
    count_cols = ["TP", "FN", "FP"]

    # Only use rows where metrics are present
    metric_df = df[metric_cols].dropna(how="all")
    count_df = df[count_cols].dropna(how="all")

    if not metric_df.empty:
        summary_metrics = metric_df.mean().to_frame("mean").T
    else:
        summary_metrics = pd.DataFrame(columns=["precision", "recall", "f1"])

    if not count_df.empty:
        summary_counts = count_df.sum().to_frame("total").T
    else:
        summary_counts = pd.DataFrame(columns=["TP", "FN", "FP"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Average metrics**")
        if not summary_metrics.empty:
            st.table(summary_metrics.style.format("{:.3f}"))
        else:
            st.info("No metric data available.")

    with col2:
        st.markdown("**Total counts**")
        if not summary_counts.empty:
            st.table(summary_counts.astype("Int64"))
        else:
            st.info("No count data available.")

    st.markdown("---")

    # ---------- Filters ----------
    st.subheader("Filters (Text / Peaks)")

    # cols = st.columns(4)
    # with cols[0]:
    #     min_sim = st.slider("Min similarity score", 0.0, 1.0, 0.0, 0.01)
    # with cols[1]:
    #     min_prec = st.slider("Min precision", 0.0, 1.0, 0.0, 0.01)
    # with cols[2]:
    #     min_rec = st.slider("Min recall", 0.0, 1.0, 0.0, 0.01)
    # with cols[3]:
    #     min_f1 = st.slider("Min F1", 0.0, 1.0, 0.0, 0.01)

    cols = st.columns(4)
    with cols[0]:
        max_sim = st.slider("Max similarity score", 0.0, 1.0, 1.0, 0.01)
    with cols[1]:
        max_prec = st.slider("Max precision", 0.0, 1.0, 1.0, 0.01)
    with cols[2]:
        max_rec = st.slider("Max recall", 0.0, 1.0, 1.0, 0.01)
    with cols[3]:
        max_f1 = st.slider("Max F1", 0.0, 1.0, 1.0, 0.01)

    perfect_only_text = st.checkbox(
        "Show only perfect matches (precision=recall=F1=1)",
        value=False,
        key="perfect_only_text",
    )

    filtered_text_df = df.copy()

    # Fill NAs with 0 so filters behave nicely
    filtered_text_df["sim_score"] = filtered_text_df["sim_score"].fillna(0.0)
    filtered_text_df["precision"] = filtered_text_df["precision"].fillna(0.0)
    filtered_text_df["recall"] = filtered_text_df["recall"].fillna(0.0)
    filtered_text_df["f1"] = filtered_text_df["f1"].fillna(0.0)

    filtered_text_df = filtered_text_df[
        (filtered_text_df["sim_score"] <= max_sim)
        & (filtered_text_df["precision"] <= max_prec)
        & (filtered_text_df["recall"] <= max_rec)
        & (filtered_text_df["f1"] <= max_f1)
    ]

    if perfect_only_text:
        filtered_text_df = filtered_text_df[
            (filtered_text_df["precision"] == 1.0)
            & (filtered_text_df["recall"] == 1.0)
            & (filtered_text_df["f1"] == 1.0)
        ]

    st.caption(f"Showing {len(filtered_text_df)} / {len(df)} records after filtering.")

    # ---------- Table view ----------
    st.subheader("Table View (Text / Peaks)")

    show_cols_text = [
        "_idx",
        "sim_score",
        "precision",
        "recall",
        "f1",
        "TP",
        "FN",
        "FP",
    ]

    if len(filtered_text_df) > 0:
        st.dataframe(
            filtered_text_df[show_cols_text].sort_values("_idx").reset_index(drop=True),
            use_container_width=True,
        )
    else:
        st.info("No rows match the current filters.")

    st.markdown("---")

    # ---------- Record browser ----------
    st.subheader("Record Browser (Text / Peaks)")

    if len(filtered_text_df) == 0:
        st.warning("No records match the current filters.")
    else:
        selected_idx_text = st.number_input(
            "Select row number (in filtered set)",
            min_value=0,
            max_value=len(filtered_text_df) - 1,
            value=0,
            step=1,
            key="selected_idx_text",
        )

        row_t = filtered_text_df.iloc[int(selected_idx_text)]

        st.markdown(f"**Original index in data:** `{row_t['_idx']}`")

        c1_t, c2_t = st.columns(2)

        with c1_t:
            st.markdown("### Ground Truth Text")
            st.code(str(row_t.get("gt_text", "")))
            st.markdown("**GT peaks:**")
            st.write(row_t.get("gt_peaks", []))

        with c2_t:
            st.markdown("### Extracted Text")
            st.code(str(row_t.get("ext_text", "")))
            st.markdown("**Extracted peaks:**")
            st.write(row_t.get("extracted_peaks", []))

        st.markdown("### Metrics for this record")

        c3_t, c4_t, c5_t, c6_t = st.columns(4)
        with c3_t:
            st.metric("sim_score", float(row_t["sim_score"]))
        with c4_t:
            st.metric("precision", f"{float(row_t['precision']):.3f}")
        with c5_t:
            st.metric("recall", f"{float(row_t['recall']):.3f}")
        with c6_t:
            st.metric("F1", f"{float(row_t['f1']):.3f}")

        c7_t, c8_t, c9_t = st.columns(3)
        with c7_t:
            st.metric("TP", int(row_t["TP"]) if pd.notna(row_t["TP"]) else 0)
        with c8_t:
            st.metric("FN", int(row_t["FN"]) if pd.notna(row_t["FN"]) else 0)
        with c9_t:
            st.metric("FP", int(row_t["FP"]) if pd.notna(row_t["FP"]) else 0)

        st.markdown("---")

        # ---------- Manual annotation ----------
        st.subheader("Manual Error Annotation (Text / Peaks)")

        if "annotations_text" not in st.session_state:
            st.session_state["annotations_text"] = {}

        record_key_t = str(row_t["_idx"])
        current_annotation_t = st.session_state["annotations_text"].get(record_key_t, "")

        error_type_t = st.selectbox(
            "Error type",
            [
                "",
                "Correct",
                "Partial extraction",
                "Wrong peak value",
                "Missing peaks (FN)",
                "Spurious peaks (FP)",
                "Text segmentation issue",
                "Parser error",
                "Other",
            ],
            key="error_type_text",
        )

        free_text_t = st.text_area(
            "Notes",
            value=current_annotation_t if current_annotation_t not in ("", "Correct") else "",
            height=100,
            key="notes_text",
        )

        if st.button("Save annotation for this record", key="save_annotation_text"):
            st.session_state["annotations_text"][record_key_t] = (
                free_text_t or error_type_t or ""
            )
            st.success(f"Annotation saved for record {record_key_t}.")

        if st.checkbox("Show all annotations (Text / Peaks)", key="show_annotations_text"):
            ann_items_t = [
                {"_idx": int(k), "annotation": v}
                for k, v in st.session_state["annotations_text"].items()
            ]
            if ann_items_t:
                ann_df_t = pd.DataFrame(ann_items_t).sort_values("_idx")
                st.table(ann_df_t)
            else:
                st.info("No annotations yet.")


# ======================================================================
# TAB 2: MOLECULE IMAGE ANALYSIS
# ======================================================================
with tab_mol:
    st.header("Molecule Image Comparison")

    # ---------- Summary section ----------
    st.subheader("Overall Summary (Molecules)")

    mol_metric_cols = ["mol_name_score", "smiles_sim"]
    mol_metric_df = df[mol_metric_cols].dropna(how="all")

    if not mol_metric_df.empty:
        summary_mol_metrics = mol_metric_df.mean().to_frame("mean").T
        st.table(summary_mol_metrics.style.format("{:.3f}"))
    else:
        st.info("No molecule metric data available.")

    st.markdown("---")

    # ---------- Filters ----------
    st.subheader("Filters (Molecules)")

    cols_m = st.columns(3)
    # with cols_m[0]:
    #     min_name_score = st.slider("Min mol_name_score", 0.0, 1.0, 0.0, 0.01)
    # with cols_m[1]:
    #     min_smiles_sim = st.slider("Min smiles_sim", 0.0, 1.0, 0.0, 0.01)
    with cols_m[0]:
        max_name_score = st.slider("Max mol_name_score", 0.0, 1.0, 1.0, 0.01)
    with cols_m[1]:
        max_smiles_sim = st.slider("Max smiles_sim", 0.0, 1.0, 1.0, 0.01)
    with cols_m[2]:
        perfect_only_mol = st.checkbox(
            "Show only perfect matches", value=False, key="perfect_only_mol"
        )

    filtered_mol_df = df.copy()

    filtered_mol_df = filtered_mol_df.drop_duplicates(['gt_mol_name'])

    filtered_mol_df["mol_name_score"] = filtered_mol_df["mol_name_score"].fillna(0.0)
    filtered_mol_df["smiles_sim"] = filtered_mol_df["smiles_sim"].fillna(0.0)

    filtered_mol_df = filtered_mol_df[
        (filtered_mol_df["mol_name_score"] <= max_name_score)
        & (filtered_mol_df["smiles_sim"] <= max_smiles_sim)
    ]

    if perfect_only_mol:
        filtered_mol_df = filtered_mol_df[
            (filtered_mol_df["mol_name_score"] == 1.0)
            & (filtered_mol_df["smiles_sim"] == 1.0)
        ]

    st.caption(f"Showing {len(filtered_mol_df)} / {len(df)} records after filtering.")

    # ---------- Table view ----------
    st.subheader("Table View (Molecules)")

    show_cols_mol = [
        "_idx",
        "gt_mol_name",
        "extracted_mol_name",
        "mol_name_score",
        "smiles_sim",
    ]

    if len(filtered_mol_df) > 0:
        st.dataframe(
            filtered_mol_df[show_cols_mol].sort_values("_idx").reset_index(drop=True),
            use_container_width=True,
        )
    else:
        st.info("No rows match the current filters.")

    st.markdown("---")

    # ---------- Record browser ----------
    st.subheader("Record Browser (Molecules)")

    if len(filtered_mol_df) == 0:
        st.warning("No records match the current filters.")
    else:
        selected_idx_mol = st.number_input(
            "Select row number (in filtered set)",
            min_value=0,
            max_value=len(filtered_mol_df) - 1,
            value=0,
            step=1,
            key="selected_idx_mol",
        )

        row_m = filtered_mol_df.iloc[int(selected_idx_mol)]

        st.markdown(f"**Original index in data:** `{row_m['_idx']}`")

        # Names and scores
        c0_m, c1_m, c2_m = st.columns([2, 1, 1])

        with c0_m:
            st.markdown("### Names")
            st.write("**GT name:**", row_m.get("gt_mol_name", ""))
            st.write("**Extracted name:**", row_m.get("extracted_mol_name", ""))

        with c1_m:
            val_name_score = row_m["mol_name_score"]
            st.metric(
                "mol_name_score",
                f"{float(val_name_score):.3f}" if pd.notna(val_name_score) else "N/A",
            )

        with c2_m:
            val_smiles_sim = row_m["smiles_sim"]
            st.metric(
                "smiles_sim",
                f"{float(val_smiles_sim):.3f}" if pd.notna(val_smiles_sim) else "N/A",
            )

        st.markdown("---")

        # Images side by side
        from pathlib import Path as _Path

        c3_m, c4_m = st.columns(2)

        gt_img_path = row_m.get("gt_molpic_path", "")
        ext_img_path = row_m.get("extracted_molpic_path", "")

        with c3_m:
            st.markdown("### Ground Truth Molecule Image")
            if gt_img_path and _Path(gt_img_path).exists():
                st.image(gt_img_path, use_column_width=True)
                st.caption(gt_img_path)
            else:
                st.warning(f"Image not found: {gt_img_path}")

        with c4_m:
            st.markdown("### Extracted Molecule Image")
            if ext_img_path and _Path(ext_img_path).exists():
                st.image(ext_img_path, use_column_width=True)
                st.caption(ext_img_path)
            else:
                st.warning(f"Image not found: {ext_img_path}")

        st.markdown("---")

        # ---------- Manual annotation ----------
        st.subheader("Manual Error Annotation (Molecules)")

        if "annotations_mol" not in st.session_state:
            st.session_state["annotations_mol"] = {}

        record_key_m = str(row_m["_idx"])
        current_annotation_m = st.session_state["annotations_mol"].get(record_key_m, "")

        error_type_m = st.selectbox(
            "Error type",
            [
                "",
                "Correct",
                "Wrong molecule (completely)",
                "Similar scaffold, wrong substituents",
                "Missing parts in extracted image",
                "Extra artifacts in extracted image",
                "Name correct, structure wrong",
                "Structure correct, name wrong",
                "Low image quality / OCR issue",
                "Other",
            ],
            key="error_type_mol",
        )

        free_text_m = st.text_area(
            "Notes",
            value=current_annotation_m if current_annotation_m not in ("", "Correct") else "",
            height=100,
            key="notes_mol",
        )

        if st.button("Save annotation for this record", key="save_annotation_mol"):
            st.session_state["annotations_mol"][record_key_m] = (
                free_text_m or error_type_m or ""
            )
            st.success(f"Annotation saved for record {record_key_m}.")

        if st.checkbox("Show all annotations (Molecules)", key="show_annotations_mol"):
            ann_items_m = [
                {"_idx": int(k), "annotation": v}
                for k, v in st.session_state["annotations_mol"].items()
            ]
            if ann_items_m:
                ann_df_m = pd.DataFrame(ann_items_m).sort_values("_idx")
                st.table(ann_df_m)
            else:
                st.info("No annotations yet.")
