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


# ---------- Layout ----------

st.set_page_config(
    page_title="Error Analysis Viewer",
    layout="wide",
)

st.title("Error Analysis Viewer")

# Sidebar: load file
st.sidebar.header("Data")
data_file = st.sidebar.text_input("Path to results JSON", "results.json")

data = load_results(data_file)
if not data:
    st.stop()

df = pd.DataFrame(data)

# ---------- Summary section ----------

st.subheader("Overall Summary")

metric_cols = ["precision", "recall", "f1"]
count_cols = ["TP", "FN", "FP"]

summary_metrics = df[metric_cols].mean().to_frame("mean").T
summary_counts = df[count_cols].sum().to_frame("total").T

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Average metrics**")
    st.table(summary_metrics.style.format("{:.3f}"))

with col2:
    st.markdown("**Total counts**")
    st.table(summary_counts.astype(int))

st.markdown("---")

# ---------- Filters ----------

st.subheader("Filters")

cols = st.columns(4)
with cols[0]:
    min_sim = st.slider("Min similarity score", 0.0, 1.0, 0.0, 0.01)
with cols[1]:
    min_prec = st.slider("Min precision", 0.0, 1.0, 0.0, 0.01)
with cols[2]:
    min_rec = st.slider("Min recall", 0.0, 1.0, 0.0, 0.01)
with cols[3]:
    min_f1 = st.slider("Min F1", 0.0, 1.0, 0.0, 0.01)

perfect_only = st.checkbox("Show only perfect matches (precision=recall=F1=1)", value=False)

filtered_df = df.copy()

filtered_df = filtered_df[
    (filtered_df["sim_score"] >= min_sim)
    & (filtered_df["precision"] >= min_prec)
    & (filtered_df["recall"] >= min_rec)
    & (filtered_df["f1"] >= min_f1)
]

if perfect_only:
    filtered_df = filtered_df[
        (filtered_df["precision"] == 1.0)
        & (filtered_df["recall"] == 1.0)
        & (filtered_df["f1"] == 1.0)
    ]

st.caption(f"Showing {len(filtered_df)} / {len(df)} records after filtering.")

# ---------- Table view ----------

st.subheader("Table View")

show_cols = [
    "_idx",
    "sim_score",
    "precision",
    "recall",
    "f1",
    "TP",
    "FN",
    "FP",
]

st.dataframe(
    filtered_df[show_cols].sort_values("_idx").reset_index(drop=True),
    use_container_width=True,
)

st.markdown("---")

# ---------- Record browser ----------

st.subheader("Record Browser")

if len(filtered_df) == 0:
    st.warning("No records match the current filters.")
    st.stop()

# Choose record by index in filtered set
selected_idx = st.number_input(
    "Select row number (in filtered set)",
    min_value=0,
    max_value=len(filtered_df) - 1,
    value=0,
    step=1,
)

row = filtered_df.iloc[int(selected_idx)]

st.markdown(f"**Original index in data:** `{row['_idx']}`")

c1, c2 = st.columns(2)

with c1:
    st.markdown("### Ground Truth")
    st.code(str(row.get("gt_text", "")))
    st.markdown("**GT peaks:**")
    st.write(row.get("gt_peaks", []))

with c2:
    st.markdown("### Extracted")
    st.code(str(row.get("ext_text", "")))
    st.markdown("**Extracted peaks:**")
    st.write(row.get("extracted_peaks", []))

# Metrics for this record
st.markdown("### Metrics for this record")

c3, c4, c5, c6 = st.columns(4)
with c3:
    st.metric("sim_score", row["sim_score"])
with c4:
    st.metric("precision", f"{row['precision']:.3f}")
with c5:
    st.metric("recall", f"{row['recall']:.3f}")
with c6:
    st.metric("F1", f"{row['f1']:.3f}")

c7, c8, c9 = st.columns(3)
with c7:
    st.metric("TP", int(row["TP"]))
with c8:
    st.metric("FN", int(row["FN"]))
with c9:
    st.metric("FP", int(row["FP"]))

st.markdown("---")

# ---------- Optional manual annotation ----------

st.subheader("Manual Error Annotation (optional)")

# Use Streamlit session_state to store temporary annotations
if "annotations" not in st.session_state:
    st.session_state["annotations"] = {}

record_key = str(row["_idx"])

current_annotation = st.session_state["annotations"].get(record_key, "")

error_type = st.selectbox(
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
    index=0 if current_annotation == "" else 1,
)

free_text = st.text_area(
    "Notes",
    value=current_annotation if current_annotation not in ("", "Correct") else "",
    height=100,
)

if st.button("Save annotation for this record"):
    # Simple in-memory store, you can extend this to write to file if you want
    st.session_state["annotations"][record_key] = free_text or error_type or ""
    st.success(f"Annotation saved for record {record_key}.")

# Optional: show all annotations as a small table
if st.checkbox("Show all annotations"):
    ann_items = [
        {"_idx": int(k), "annotation": v}
        for k, v in st.session_state["annotations"].items()
    ]
    if ann_items:
        ann_df = pd.DataFrame(ann_items).sort_values("_idx")
        st.table(ann_df)
    else:
        st.info("No annotations yet.")
