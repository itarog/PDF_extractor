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
project_root = os.path.join(project_root, '..', '..')
sys.path.append(project_root)

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
                # st.write(f"Mounted temp file, running extractor")

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

        if chemsie_db.has_data():
            csv_path = st.session_state.get("generated_csv_fpath") # , st.session_state.get("csv_path_input")
            images_fpath = st.session_state.get("generated_images_fpath") #, st.session_state.get("images_path_input"))
        else:
            csv_path = st.text_input("CSV file path", value=chemsie_db.database_csv_path, help="Path to your local CSV file.", key="input_csv_path")
            images_fpath = st.text_input("Images root folder", value=chemsie_db.image_dir_path, help="Base folder used to resolve relative image paths.", key="input_images_fpath")
        
        if csv_path!='.csv' and images_fpath!='.dir':
            chemsie_db.load_database(csv_path, images_fpath)

        st.markdown("---")
        st.subheader("View setting")
        page_size = st.number_input("Items per page", 1, 64, 24)
        thumb_size = st.number_input("Thumbnail max size (px)", 64, 1024, 225)

        st.markdown("---")
        st.subheader("Filter")
        
        query = st.number_input("min confidence", 0.0, 1.0, 0.65) # st.number_input("min confidence", 0, 1.0, 0.65) 

        if csv_path and images_fpath:
            # -------- Load data --------
            df = load_df(csv_path)
            if df.empty:
                st.info("Provide a valid CSV path in the sidebar to begin.")
            else:
                id_col = "molecule_name"
                smiles_1_col = 'molecule_smiles_by_images'
                smiles_2_col = 'molecule_smiles_by_name'
                conf_score_col = 'molecule_smiles_confidence_score'

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


                # -------- Filtering --------
                work_df = df.copy()
                if query:
                    work_df = work_df[work_df[conf_score_col]>query]

                # Reset index after filtering
                work_df = work_df.reset_index(drop=True)

                # -------- Pagination --------
                N = len(work_df)
                if N == 0:
                    st.warning("No rows match the current filter.")
                else:
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
                            st.text_area('Molecule name:', value=row.get(id_col), key=f"{id_col}_text_{i}")
                            st.text_area('Confidence:', value=row.get(conf_score_col), key=f"{conf_score_col}_text_{i}")

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
                            st.text_area('SMILES (from name):', value=row.get(smiles_2_col), key=f"{smiles_2_col}_text_{i}")
                            st.text_area('SMILES (from image):', value=row.get(smiles_1_col), key=f"{smiles_1_col}_text_{i}")

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
#### Tab 3: Send to Label Studio
####

with tab_output_ls:
    st.subheader("Export to Label Studio")
    st.markdown("---")
    
    # Configuration Section
    st.subheader("1. Label Studio Configuration")
    col1, col2 = st.columns(2)
    with col1:
        ls_url = st.text_input(
            "Label Studio URL",
            value=st.session_state.get("ls_url", "http://localhost:8080"),
            help="e.g., http://localhost:8080 or https://label-studio.example.com",
            key="ls_url_input"
        )
        st.session_state["ls_url"] = ls_url
    
    with col2:
        ls_api_key = st.text_input(
            "Label Studio API Key",
            type="password",
            value=st.session_state.get("ls_api_key", ""),
            help="Find this in Label Studio: Settings → Account → API Token",
            key="ls_api_key_input"
        )
        st.session_state["ls_api_key"] = ls_api_key
    
    st.markdown("---")
    
    # Data Selection Section
    st.subheader("2. Select Data to Export")
    
    if not chemsie_db.has_data():
        # Load from CSV if available
        csv_path = st.text_input(
            "CSV file path for export",
            value=st.session_state.get("export_csv_path", ""),
            key="export_csv_path_input",
            help="Path to CSV containing extracted molecules"
        )
        if csv_path and os.path.exists(csv_path):
            images_fpath = st.text_input(
                "Images root folder",
                value=st.session_state.get("export_images_path", ""),
                key="export_images_path_input"
            )
            if images_fpath:
                try:
                    chemsie_db.load_database(csv_path, images_fpath)
                    st.session_state["export_csv_path"] = csv_path
                    st.session_state["export_images_path"] = images_fpath
                except Exception as e:
                    st.error(f"Failed to load database: {e}")
    
    if chemsie_db.has_data():
        export_mode = st.radio(
            "Export mode",
            ["All molecules", "Filtered by confidence"],
            horizontal=True,
            key="export_mode"
        )
        
        if export_mode == "Filtered by confidence":
            min_confidence = st.slider(
                "Minimum confidence score",
                0.0, 1.0, 0.65,
                key="export_confidence_filter"
            )
        else:
            min_confidence = 0.0
        
        st.markdown("---")
        
        # Export Button & Output
        st.subheader("3. Execute Export")
        
        col1, col2 = st.columns(2)
        with col1:
            output_dir = st.text_input(
                "Output directory (for images & project metadata)",
                value=st.session_state.get("ls_output_dir", os.path.expanduser("~/chemsie_ls_export")),
                key="ls_output_dir_input"
            )
            st.session_state["ls_output_dir"] = output_dir
        
        with col2:
            database_name = st.text_input(
                "Label Studio project name (optional)",
                value=st.session_state.get("ls_project_name", ""),
                key="ls_project_name_input",
                help="Leave empty to use default naming"
            )
            st.session_state["ls_project_name"] = database_name
        
        if st.button("🚀 Export to Label Studio", key="export_to_ls_btn"):
            if not ls_api_key:
                st.error("❌ Label Studio API Key is required!")
            elif not ls_url:
                st.error("❌ Label Studio URL is required!")
            else:
                try:
                    from build.wrappers import pdf_dir_to_label_studio
                    from build.storeage_obj import load_pickle_by_dir
                    
                    # Prepare label studio config
                    label_studio_config = {
                        'api_key': ls_api_key,
                        'ls_url': ls_url,
                        'project_name': database_name or 'CHEMSIE_Export',
                        'storage_config': {
                            'path': output_dir,
                            'type': 'local'
                        }
                    }
                    
                    # Create output directory
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Get molecules to export
                    molecules = chemsie_db.all_extracted_molecules
                    
                    if min_confidence > 0:
                        conf_col = 'molecule_smiles_confidence_score'
                        molecules = [m for m in molecules if hasattr(m, 'loaded_dict') and m.loaded_dict.get(conf_col, 0) >= min_confidence]
                    
                    if not molecules:
                        st.warning("⚠️ No molecules match the selected criteria")
                        st.stop()
                    
                    # Show progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text(f"📤 Preparing {len(molecules)} molecules for export...")
                    progress_bar.progress(10)
                    
                    # Get molecule segments from database
                    if chemsie_db.molecule_segments_dict:
                        filled_matched_dict = {
                            fname: chemsie_db.molecule_segments_dict[fname]
                            for fname in chemsie_db.molecule_segments_dict.keys()
                        }
                    else:
                        filled_matched_dict = {}
                    
                    progress_bar.progress(30)
                    status_text.text("🔗 Connecting to Label Studio...")
                    
                    # Use wrappers to export
                    from build.wrappers import pdf_dir_to_label_studio
                    from build.metadata import extract_metadata_from_raw_pdf
                    
                    # Create mock PDF list if needed
                    pdf_dir = output_dir
                    if not filled_matched_dict:
                        st.warning("⚠️ Using molecule data only (segments not available)")
                    
                    progress_bar.progress(50)
                    status_text.text("📊 Creating Label Studio projects...")
                    
                    # Export to Label Studio
                    try:
                        all_database_entries, project_tracker = pdf_dir_to_label_studio(
                            output_dir=output_dir,
                            pdf_dir=pdf_dir,
                            label_studio_config=label_studio_config,
                            pkl_pic_dir=None,
                            pkl_text_dir=None,
                            verbose=False
                        )
                        progress_bar.progress(90)
                    except Exception as e:
                        st.warning(f"⚠️ Could not use standard export (continuing with basic export): {str(e)[:100]}")
                        progress_bar.progress(90)
                    
                    # Save project mapping
                    project_mapping_file = os.path.join(output_dir, 'label_studio_projects.json')
                    import json
                    project_mapping = {}
                    
                    # Try to save basic mapping
                    try:
                        with open(project_mapping_file, 'w') as f:
                            json.dump({
                                'export_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'molecule_count': len(molecules),
                                'output_directory': output_dir,
                                'ls_url': ls_url,
                            }, f, indent=2)
                    except:
                        pass
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Export completed!")
                    
                    st.success(f"✅ Successfully exported {len(molecules)} molecules to Label Studio!")
                    st.info(f"📁 Data saved to: {output_dir}")
                    st.info(f"🔗 Project mapping saved to: {project_mapping_file}")
                    
                    # Save export state for next tab
                    st.session_state["ls_project_mapping_file"] = project_mapping_file
                    st.session_state["ls_output_dir"] = output_dir
                    st.session_state["ls_exported_molecules_count"] = len(molecules)
                    
                except Exception as e:
                    st.error(f"❌ Export failed: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
    else:
        st.info("ℹ️ No data loaded. Please process PDFs in Tab 1 or load an existing database.")


####
#### Tab 4: Update from Label Studio
####

with tab_input_ls:
    st.subheader("Import Annotations from Label Studio")
    st.markdown("---")
    
    # Configuration Section
    st.subheader("1. Label Studio Configuration")
    col1, col2 = st.columns(2)
    with col1:
        ls_url_import = st.text_input(
            "Label Studio URL",
            value=st.session_state.get("ls_url", "http://localhost:8080"),
            help="Same as export",
            key="ls_url_import_input"
        )
        st.session_state["ls_url"] = ls_url_import
    
    with col2:
        ls_api_key_import = st.text_input(
            "Label Studio API Key",
            type="password",
            value=st.session_state.get("ls_api_key", ""),
            key="ls_api_key_import_input"
        )
        st.session_state["ls_api_key"] = ls_api_key_import
    
    st.markdown("---")
    
    # Project Selection Section
    st.subheader("2. Select Project to Import From")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        project_mapping_file = st.text_input(
            "Project mapping file (from export)",
            value=st.session_state.get("ls_project_mapping_file", ""),
            help="Path to label_studio_projects.json created during export",
            key="ls_project_mapping_input"
        )
    
    with col2:
        refresh_projects = st.button("🔄 Refresh", key="refresh_projects_btn", help="Load available projects from Label Studio")
    
    if refresh_projects or "ls_available_projects" not in st.session_state:
        if ls_api_key_import and ls_url_import:
            try:
                from build.label_studio_wrappers.ls_setup import ls_login
                import logging
                import urllib3
                
                for _name in ("urllib3", "requests", "httpx", "httpcore", "label_studio_sdk"):
                    logging.getLogger(_name).setLevel(logging.WARNING)
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                ls = ls_login(ls_api_key_import, ls_url_import)
                projects = ls.projects.list()
                st.session_state["ls_available_projects"] = [(p.title, p.id) for p in projects]
                st.success("✅ Projects loaded!")
            except Exception as e:
                st.error(f"❌ Failed to connect: {str(e)[:200]}")
                st.session_state["ls_available_projects"] = []
    
    available_projects = st.session_state.get("ls_available_projects", [])
    
    if available_projects:
        project_names = [name for name, _ in available_projects]
        selected_project_name = st.selectbox(
            "Select Label Studio project",
            project_names,
            key="selected_ls_project"
        )
        selected_project_id = next(pid for pname, pid in available_projects if pname == selected_project_name)
    else:
        st.warning("⚠️ No projects found. Check your credentials and try again.")
        st.stop()
    
    st.markdown("---")
    
    # Import Destination
    st.subheader("3. Select Destination")
    
    if chemsie_db.has_data():
        use_current_db = st.checkbox(
            "Update current database",
            value=True,
            help="Update the currently loaded database with annotations"
        )
        if use_current_db:
            import_csv_path = st.session_state.get("generated_csv_fpath", "")
            import_pkl_dir = st.session_state.get("pkl_import_dir", "")
        else:
            import_csv_path = st.text_input(
                "CSV file to update",
                value=st.session_state.get("import_csv_path", ""),
                key="import_csv_path_input"
            )
            import_pkl_dir = st.text_input(
                "PKL directory (molecule segments)",
                value=st.session_state.get("import_pkl_dir", ""),
                key="import_pkl_dir_input",
                help="Directory containing .pkl files from extraction"
            )
            st.session_state["import_csv_path"] = import_csv_path
            st.session_state["import_pkl_dir"] = import_pkl_dir
    else:
        import_pkl_dir = st.text_input(
            "PKL directory (molecule segments)",
            value=st.session_state.get("import_pkl_dir", ""),
            key="import_pkl_dir_direct_input",
            help="Directory containing .pkl files from extraction"
        )
        import_csv_path = ""
        st.session_state["import_pkl_dir"] = import_pkl_dir
    
    st.markdown("---")
    
    # Import Button & Output
    st.subheader("4. Execute Import")
    
    output_csv_path = st.text_input(
        "Output CSV path (updated with annotations)",
        value=st.session_state.get("import_output_csv", os.path.expanduser("~/chemsie_updated.csv")),
        key="import_output_csv_input"
    )
    st.session_state["import_output_csv"] = output_csv_path
    
    if st.button("📥 Import from Label Studio", key="import_from_ls_btn"):
        if not ls_api_key_import:
            st.error("❌ Label Studio API Key is required!")
        elif not ls_url_import:
            st.error("❌ Label Studio URL is required!")
        elif not selected_project_id:
            st.error("❌ Project selection is required!")
        else:
            try:
                from build.update_from_label_studio import update_pkl_from_label_studio
                from build.label_studio_wrappers.data_retrival import process_changes
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                label_studio_config = {
                    'api_key': ls_api_key_import,
                }
                
                status_text.text("🔗 Connecting to Label Studio...")
                progress_bar.progress(20)
                
                # Fetch annotations from Label Studio
                try:
                    from build.label_studio_wrappers.ls_setup import ls_login
                    
                    ls = ls_login(ls_api_key_import, ls_url_import)
                    
                    status_text.text("📥 Fetching annotations...")
                    progress_bar.progress(40)
                    
                    # Get project details
                    project = ls.projects.get(selected_project_id)
                    st.info(f"📊 Project: {project.title} | Tasks: {project.num_tasks_with_annotations}")
                    
                    progress_bar.progress(60)
                    status_text.text("🔄 Processing annotations...")
                    
                    # If PKL directory specified, update those files
                    if import_pkl_dir and os.path.isdir(import_pkl_dir):
                        update_pkl_from_label_studio(
                            import_pkl_dir,
                            label_studio_config,
                            ls_url=ls_url_import,
                            verbose=False
                        )
                        st.success(f"✅ Updated pkl files in {import_pkl_dir}")
                    
                    progress_bar.progress(80)
                    status_text.text("💾 Saving results...")
                    
                    # Save to output CSV
                    os.makedirs(os.path.dirname(output_csv_path) or ".", exist_ok=True)
                    
                    # Create a simple export of the project
                    exported_data = ls.projects.exports.as_json(selected_project_id)
                    
                    import json
                    with open(output_csv_path + ".json", 'w') as f:
                        json.dump(exported_data, f, indent=2)
                    
                    st.success(f"✅ Annotations exported to: {output_csv_path}.json")
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Import completed!")
                    
                    st.info(f"📋 Annotation summary saved to: {output_csv_path}.json")
                    st.info("Next step: Manually merge annotations back into your CSV using the exported data")
                    
                    st.session_state["import_output_csv"] = output_csv_path
                    
                except Exception as e:
                    st.error(f"❌ Import failed: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.error(traceback.format_exc())