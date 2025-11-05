#!/usr/bin/env python3
"""
Export molecule images from pickle files to PNG files.

Usage:
    python export_images.py path/to/file.pkl --output images/
    python export_images.py results/*.pkl --output images/  # All PKL files
"""

import os
import sys
import glob
from storeage_obj import load_pickle_by_filename
from mol_pic import export_mol_pic


def export_images_from_pkl(pkl_path, output_dir):
    """Export all molecule images from a PKL file to PNG files."""
    print(f"\nProcessing: {pkl_path}")
    
    # Load the PKL file
    try:
        data = load_pickle_by_filename(pkl_path)
    except Exception as e:
        print(f"  ✗ Error loading file: {e}")
        return 0
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get base filename without extension
    base_name = os.path.splitext(os.path.basename(pkl_path))[0]
    
    # Export images from molecule segments
    exported_count = 0
    for seg_idx, segment in enumerate(data.molecule_segments):
        if not segment.mol_pics:
            continue
        
        # Create subdirectory for this PDF
        pdf_output_dir = os.path.join(output_dir, base_name)
        os.makedirs(pdf_output_dir, exist_ok=True)
        
        # Export each image cluster
        for cluster_idx, mol_pic_cluster in enumerate(segment.mol_pics):
            if mol_pic_cluster.leading_pic:
                # Use molecule name if available, otherwise use index
                if segment.molecule_name:
                    # Sanitize molecule name for filename
                    safe_name = "".join(c for c in segment.molecule_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    safe_name = safe_name.replace(' ', '_')
                    filename = f"{safe_name}_p{mol_pic_cluster.page_num}_c{cluster_idx}.png"
                else:
                    filename = f"molecule_seg{seg_idx}_p{mol_pic_cluster.page_num}_c{cluster_idx}.png"
                
                try:
                    export_path = export_mol_pic(
                        mol_pic_cluster.leading_pic,
                        pdf_output_dir,
                        molecule_name=None  # We're using custom filename
                    )
                    # Rename to our custom filename
                    old_path = export_path
                    new_path = os.path.join(pdf_output_dir, filename)
                    os.rename(old_path, new_path)
                    exported_count += 1
                    print(f"  ✓ Exported: {os.path.basename(new_path)}")
                except Exception as e:
                    print(f"  ✗ Error exporting image: {e}")
    
    print(f"  Total exported: {exported_count} image(s)")
    return exported_count


def main():
    if len(sys.argv) < 3:
        print("Usage: python export_images.py <pkl_file(s)> --output <output_dir>")
        print("\nExamples:")
        print("  python export_images.py results/file.pkl --output images/")
        print("  python export_images.py results/*.pkl --output images/")
        sys.exit(1)
    
    # Parse arguments
    args = sys.argv[1:]
    
    # Find --output flag
    try:
        output_idx = args.index('--output')
        output_dir = args[output_idx + 1]
        pkl_files = [arg for arg in args[:output_idx] if not arg.startswith('--')]
    except (ValueError, IndexError):
        print("Error: --output flag required (e.g., --output images/)")
        sys.exit(1)
    
    if not pkl_files:
        print("Error: No pickle files specified")
        sys.exit(1)
    
    # Expand glob patterns
    all_files = []
    for pattern in pkl_files:
        expanded = glob.glob(pattern)
        if expanded:
            all_files.extend(expanded)
        elif os.path.exists(pattern):
            all_files.append(pattern)
    
    if not all_files:
        print(f"Error: No matching files found")
        sys.exit(1)
    
    print(f"Found {len(all_files)} pickle file(s)")
    print(f"Output directory: {output_dir}")
    
    # Export images from each file
    total_exported = 0
    for pkl_file in all_files:
        exported = export_images_from_pkl(pkl_file, output_dir)
        total_exported += exported
    
    print(f"\n{'='*60}")
    print(f"Export complete!")
    print(f"Total images exported: {total_exported}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()



