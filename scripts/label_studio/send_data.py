import os
import sys
import json
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, project_root)

from src.chemsie.internal.wrappers import pdf_dir_to_label_studio

def send_to_label_studio(pkl_folder, pdf_dir, label_studio_config, output_dir=None, ls_url=None, verbose=True):
    if output_dir is None:
        output_dir = os.path.join(pkl_folder, 'label_studio_output')
    
    pkl_path = Path(pkl_folder)
    pdf_path = Path(pdf_dir)
    
    if not pkl_path.exists():
        raise ValueError(f"PKL folder does not exist: {pkl_folder}")
    if not pdf_path.exists():
        raise ValueError(f"PDF folder does not exist: {pdf_dir}")
    
    if not os.environ.get('LOCAL_FILES_SERVING_ENABLED'):
        if verbose:
            print("="*60)
            print("WARNING: LOCAL_FILES_SERVING_ENABLED is not set!")
            print("="*60)
            print("\nLabel Studio requires this environment variable to serve local files.")
            print("\nTo fix this:")
            print("  1. Stop Label Studio if it's running")
            print("  2. Set the environment variable:")
            print("     PowerShell: $env:LOCAL_FILES_SERVING_ENABLED = 'true'")
            print("     CMD: set LOCAL_FILES_SERVING_ENABLED=true")
            print("  3. Restart Label Studio")
            print("="*60)
            print("\nAttempting to continue anyway...\n")
    
    output_dir_abs = os.path.abspath(output_dir)
    pdf_dir_abs = os.path.abspath(pdf_dir)
    pkl_dir_abs = os.path.abspath(pkl_folder)
    
    storage_config = label_studio_config.get('storage_config', {})
    storage_config.update({
        "title": "PDF extraction storage",
        "description": "Local image storage for PDF extraction",
        "project": 0,
        "path": '',
        "regex_filter": None,
        "use_blob_urls": False,
    })
    label_studio_config['storage_config'] = storage_config
    
    if verbose:
        print(f"Sending data to Label Studio...")
        print(f"  PKL folder: {pkl_folder}")
        print(f"  PDF folder: {pdf_dir}")
        print(f"  Output folder: {output_dir}")
    
    all_database_entries, original_data_tracker = pdf_dir_to_label_studio(
        output_dir=output_dir_abs,
        pdf_dir=pdf_dir_abs,
        label_studio_config=label_studio_config,
        pkl_text_dir=pkl_dir_abs,
        verbose=verbose
    )
    
    project_mapping_file = os.path.join(pkl_folder, 'label_studio_projects.json')
    project_mapping = {}
    for filename, (project_id, segments) in original_data_tracker.items():
        project_mapping[filename] = {
            'project_id': project_id,
            'pkl_file': filename.replace('.pdf', '.pkl')
        }
    
    with open(project_mapping_file, 'w') as f:
        json.dump(project_mapping, f, indent=2)
    
    if verbose:
        print(f"\nProject mapping saved to: {project_mapping_file}")
        print(f"Created {len(project_mapping)} Label Studio projects")
    
    return original_data_tracker, project_mapping_file

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Send pkl data to Label Studio for annotation")
    parser.add_argument("--pkl-folder", required=True, help="Folder containing pkl files")
    parser.add_argument("--pdf-dir", required=True, help="Folder containing original PDF files")
    parser.add_argument("--api-key", required=True, help="Label Studio API key")
    parser.add_argument("--output", help="Output folder for Label Studio files (default: pkl-folder/label_studio_output)")
    parser.add_argument("--ls-url", default="http://localhost:8080", help="Label Studio URL")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    
    args = parser.parse_args()
    
    label_studio_config = {
        'api_key': args.api_key,
    }
    
    send_to_label_studio(
        args.pkl_folder,
        args.pdf_dir,
        label_studio_config,
        output_dir=args.output,
        ls_url=args.ls_url,
        verbose=not args.quiet
    )

