#!/usr/bin/env python3
"""
Main script for processing PDF files containing chemical analysis data.
Extracts text and images, then prepares data for Label Studio annotation.

Usage:
    python main.py --input input_folder --output output_folder
    python main.py --input input_folder --output output_folder --pics  # Also extract images
"""

import os
import sys
import argparse
from pathlib import Path

# Change to project directory to allow imports to work
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)
sys.path.insert(0, project_root)

# Now import modules - they use absolute imports after changing directory
import full_process
import metadata
import storeage_obj


def process_single_pdf(pdf_path, output_dir, process_pics=True, save_images=False, img_backend="decimer", verbose=True):
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory where results will be saved
            process_pics: Whether to extract images (requires DECIMER)
            verbose: Whether to print progress messages
        
        Returns:
            bool: True if successful, False otherwise
        """
    # try:
        pdf_file = os.path.basename(pdf_path)
        
        if verbose:
            print(f"Processing: {pdf_file}")
        
        # Extract metadata
        pdf_metadata = metadata.extract_metadata_from_raw_pdf(pdf_path)
        
        # Process document (text + optionally images)
        if process_pics:
            # try:
                # For image extraction, use the pics-first approach with optimization
                molecule_segments, mol_pic_clusters = full_process.process_doc_pics_first(
                    pdf_path,
                    save_pics=save_images,
                    save_dir=output_dir if save_images else '',
                    optimize_version='short',
                    backend=img_backend
                )
                
                # Check if we actually got any images
                if mol_pic_clusters is None or len(mol_pic_clusters) == 0:
                    if verbose:
                        print(f"  ⚠ No chemical structure images found (DECIMER not installed or no images in PDF)")
                        print(f"  Processing text only...")
                    # Re-process with text-only approach
                    molecule_segments, mol_pic_clusters = full_process.process_doc_text_first(
                        pdf_path, 
                        process_pics=False
                    )
                    
            # except Exception as e:
            #     if verbose:
            #         print(f"Image extraction failed for {pdf_file}: {e}")
            #         print("  Falling back to text-only processing")
            #     # Fall back to text-only
            #     molecule_segments, mol_pic_clusters = full_process.process_doc_text_first(
            #         pdf_path, 
            #         process_pics=False
            #    )
        else:
            molecule_segments, mol_pic_clusters = full_process.process_doc_text_first(
                pdf_path, 
                process_pics=False
            )
        
        # Save results
        final_obj = storeage_obj.ProccessedPdf(pdf_file, pdf_metadata, molecule_segments, mol_pic_clusters)
        pkl_filename = pdf_file.replace('.pdf', '.pkl')
        output_path = os.path.join(output_dir, pkl_filename)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        storeage_obj.save_object(final_obj, output_path)
        
        if verbose:
            print(f"✓ Success: {pdf_file}")
            print(f"  - Found {len(molecule_segments)} molecule segments")
            if mol_pic_clusters:
                print(f"  - Found {len(mol_pic_clusters)} molecule image clusters")
            print(f"  - Saved to: {output_path}")
        
        return True
        
    # except Exception as e:
    #     if verbose:
    #         print(f"✗ Failed to process {pdf_file}: {str(e)}")
    #     return False


def process_folder(input_folder, output_folder, process_pics=True, save_images=False, img_backend="decimer", verbose=True):
    """
    Process all PDF files in a folder.
    
    Args:
        input_folder: Path to folder containing PDF files
        output_folder: Path to folder where results will be saved
        process_pics: Whether to extract images (requires DECIMER)
        verbose: Whether to print progress messages
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    if not input_path.exists():
        print(f"Error: Input folder does not exist: {input_folder}")
        return
    
    # Find all PDF files
    pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in: {input_folder}")
        return
    
    print(f"\n{'='*60}")
    print(f"Processing {len(pdf_files)} PDF file(s)")
    print(f"Input folder:  {input_folder}")
    print(f"Output folder: {output_folder}")
    print(f"Extract images: {process_pics}")
    print(f"{'='*60}\n")
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Process each PDF
    successful = 0
    failed = 0
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        if verbose:
            print(f"[{idx}/{len(pdf_files)}]", end=" ")
        
        success = process_single_pdf(
            str(pdf_path), 
            str(output_path),
            process_pics=process_pics,
            save_images=save_images,
            img_backend = img_backend,
            verbose=verbose
        )
        
        if success:
            successful += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"Results saved to: {output_folder}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Extract chemical analysis text and molecule images from PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a folder of PDFs (text only)
  python main.py --input demo_data/Exdata_1 --output results
  
  # Process with image extraction (requires DECIMER)
  python main.py --input demo_data/Exdata_1 --output results --pics
  
  # Process a single PDF
  python main.py --input path/to/file.pdf --output results
        """
    )
    
    parser.add_argument(
        '--input',
        required=True,
        help='Input folder containing PDF files or path to a single PDF'
    )
    
    parser.add_argument(
        '--output',
        required=True,
        help='Output folder where results will be saved'
    )
    
    parser.add_argument(
        '--pics',
        action='store_true',
        help='Extract molecule images with bounding boxes (requires DECIMER library)'
    )
    
    parser.add_argument(
        '--save-images',
        action='store_true',
        help='[Not yet implemented] Images are stored in PKL files. Use export_images.py to save PNG files.'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )
    parser.add_argument(
        '--backend',
        choices=['decimer', 'yode'],
        default='decimer',
        help='Segmentation backend to use for images (default: decimer)'
    )
    
    args = parser.parse_args()
    
    process_folder(
        args.input,
        args.output,
        process_pics=args.pics,
        save_images=args.save_images,
        img_backend=args.backend,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()

