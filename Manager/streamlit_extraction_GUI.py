import streamlit as st
import time
import sys

sys.path.append(r"C:\Users\itaro\OneDrive\Documents\GitHub\PDF_extractor")
from full_process import process_doc_pics_first

st.title("File Processor")

# Drag-and-drop uploader
uploaded_files = st.file_uploader(
    "Drag and drop files here",
    accept_multiple_files=True
)

def process_file(file, progress_callback, backend='yode'):
    final_molecule_segments, mol_pic_clusters = process_doc_pics_first(file, backend=backend)
    # # Example: simulate processing
    # for i in range(100):
    #     time.sleep(0.02)
    #     progress_callback(i + 1)  # update progress

    # # Return dummy output
    return f"Processed {file.name}"

if uploaded_files:

    if st.button("Run processing"):
        results = []

        # Streamlit progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, file in enumerate(uploaded_files):
            status_text.write(f"Processing: {file.name}")

            def cb(p):
                # p is 1–100, convert to global progress
                overall = int((idx + p/100) / len(uploaded_files) * 100)
                progress_bar.progress(overall)

            result = process_file(file, cb)
            results.append(result)

        status_text.write("Done!")
        st.success("All files processed.")
        st.write(results)
