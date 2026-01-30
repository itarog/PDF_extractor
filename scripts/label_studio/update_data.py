import os
import sys
import json
import pickle
from pathlib import Path

project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)
sys.path.insert(0, project_root)

import src.chemsie.legacy.storage as storage_obj
from experiments.label_studio_wrappers.data_retrival import process_changes

def update_pkl_from_label_studio(pkl_folder, label_studio_config, pdf_dir=None, ls_url=None, project_mapping_file=None, verbose=True):
    pkl_path = Path(pkl_folder)
    if not pkl_path.exists():
        raise ValueError(f"PKL folder does not exist: {pkl_folder}")
    
    if pdf_dir is None:
        pdf_dir = pkl_folder
    
    pdf_path = Path(pdf_dir)
    if not pdf_path.exists():
        raise ValueError(f"PDF folder does not exist: {pdf_dir}")
    
    if project_mapping_file is None:
        project_mapping_file = os.path.join(pkl_folder, 'label_studio_projects.json')
    
    if not os.path.exists(project_mapping_file):
        if verbose:
            print(f"Warning: Project mapping file not found: {project_mapping_file}")
            print("Attempting to find projects by name...")
        project_mapping = {}
    else:
        with open(project_mapping_file, 'r') as f:
            project_mapping = json.load(f)
    
    pkl_files = list(pkl_path.glob("*.pkl"))
    if not pkl_files:
        raise ValueError(f"No pkl files found in: {pkl_folder}")
    
    updated_count = 0
    
    backup_dir = pkl_path / "original_pkl_backups"
    backup_dir.mkdir(exist_ok=True)
    
    for pkl_file in pkl_files:
        if verbose:
            print(f"Processing: {pkl_file.name}")
        
        try:
            loaded_obj = storeage_obj.load_pickle_by_filename(str(pkl_file))
        except (ValueError, EOFError, pickle.UnpicklingError) as e:
            if verbose:
                print(f"  Error loading {pkl_file.name}: {e}")
            continue
        
        if not hasattr(loaded_obj, 'molecule_segments') or not loaded_obj.molecule_segments:
            if verbose:
                print(f"  Skipping: No molecule segments found")
            continue
        
        pdf_file = loaded_obj.file_name
        pdf_file_path = pdf_path / pdf_file
        
        if not pdf_file_path.exists():
            if verbose:
                print(f"  Warning: PDF file not found: {pdf_file_path}")
            continue
        
        project_id = None
        if pdf_file in project_mapping:
            project_id = project_mapping[pdf_file]['project_id']
        else:
            from label_studio_wrappers.ls_setup import ls_login
            ls = ls_login(label_studio_config['api_key'], ls_url)
            projects = ls.projects.list()
            clean_filename = pdf_file.replace('.pdf', '')
            for p in projects:
                if p.title == clean_filename:
                    project_id = p.id
                    break
        
        if project_id is None:
            if verbose:
                print(f"  Warning: Label Studio project for '{pdf_file}' not found. Skipping.")
            continue
        
        # Determine label studio output directory where page images are stored
        clean_filename = pdf_file.replace('.pdf', '')
        
        try:
            updated_segments = process_changes(
                label_studio_config['api_key'],
                project_id,
                loaded_obj.molecule_segments,
                ls_url=ls_url
            )
            
            loaded_obj.molecule_segments = updated_segments
            
            backup_path = backup_dir / pkl_file.name
            if pkl_file.exists() and not backup_path.exists():
                import shutil
                shutil.copy2(pkl_file, backup_path)
            elif verbose and backup_path.exists():
                print(f"  Backup already exists, skipping backup: {backup_path.name}")
            
            storeage_obj.save_object(loaded_obj, str(pkl_file))
            
            if verbose:
                print(f"  Updated: {pkl_file.name}")
            updated_count += 1
            
        except Exception as e:
            if verbose:
                print(f"  Error updating {pkl_file.name}: {e}")
            continue
    
    if verbose:
        print(f"\nUpdate complete. Updated {updated_count}/{len(pkl_files)} pkl files.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Update pkl files from Label Studio annotations")
    parser.add_argument("--pkl-folder", required=True, help="Folder containing pkl files to update")
    parser.add_argument("--pdf-dir", help="Folder containing original PDF files (default: same as pkl-folder)")
    parser.add_argument("--api-key", required=True, help="Label Studio API key")
    parser.add_argument("--ls-url", default="http://localhost:8080", help="Label Studio URL")
    parser.add_argument("--project-mapping", help="Path to project mapping JSON file (default: pkl-folder/label_studio_projects.json)")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    
    args = parser.parse_args()
    
    label_studio_config = {
        'api_key': args.api_key,
    }
    
    update_pkl_from_label_studio(
        args.pkl_folder,
        label_studio_config,
        pdf_dir=args.pdf_dir,
        ls_url=args.ls_url,
        project_mapping_file=args.project_mapping,
        verbose=not args.quiet
    )

