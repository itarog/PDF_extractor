#!/usr/bin/env python3
"""
View the contents of a pickle file showing data organized by page.

Usage:
    python view_pkl.py path/to/file.pkl
"""

import sys
import os
from collections import defaultdict
from storeage_obj import load_pickle_by_filename


def format_text(text, max_length=100):
    """Truncate text if too long."""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def display_molecule_segment(segment, segment_idx):
    """Display details of a molecule segment."""
    print(f"\n{'='*80}")
    print(f"  Molecule Segment #{segment_idx + 1}")
    print(f"  {'='*80}")
    print(f"  Name: {segment.molecule_name}")
    print(f"  Pages: {segment.start_page} to {segment.end_page}")
    print(f"  Lines: {segment.start_line} to {segment.end_line}")
    
    # Display segment lines
    if segment.segment_lines:
        print(f"\n  Segment Text ({len(segment.segment_lines)} lines):")
        for multi_idx, line_text, bbox in segment.segment_lines[:5]:  # Show first 5 lines
            print(f"    [{multi_idx}] {format_text(line_text, 80)}")
        if len(segment.segment_lines) > 5:
            print(f"    ... and {len(segment.segment_lines) - 5} more lines")
    
    # Display test data
    if segment.has_test_text_sequence:
        print(f"\n  Chemical Tests ({len(segment.test_text_sequence.test_text_lines)} tests):")
        for test_line in segment.test_text_sequence.test_text_lines:
            print(f"    • {test_line.test_type}")
            print(f"      Text: {format_text(test_line.text, 70)}")
            print(f"      Location: Page {test_line.start_page}, line {test_line.start_line} to {test_line.end_line}")
    
    # Display molecule images with bounding boxes
    if segment.mol_pics:
        print(f"\n  Molecular Image of Segment #{segment_idx + 1}:")
        for idx, mol_pic in enumerate(segment.mol_pics, 1):
            print(f"      Page: {mol_pic.page_num}")
            print(f"      Bounding boxes (y0, x0, y1, x1): {mol_pic.bbox}")



def display_by_page(data, page_num):
    """Display all data for a specific page."""
    print(f"\n{'#'*80}")
    print(f"# PAGE {page_num}")
    print(f"{'#'*80}")
    
    # Find all molecule segments on this page
    page_segments = []
    for seg_idx, segment in enumerate(data.molecule_segments):
        # Check if segment spans this page
        if segment.start_page <= page_num <= segment.end_page:
            page_segments.append((seg_idx, segment))
    
    if not page_segments:
        print(f"\nNo molecule segments found on page {page_num}")
        return
    
    print(f"\nFound {len(page_segments)} molecule segment(s) on this page:")
    
    for seg_idx, segment in page_segments:
        display_molecule_segment(segment, seg_idx)


def display_summary(data):
    """Display summary of the pickle file contents."""
    print("\n" + "="*80)
    print("PICKLE FILE SUMMARY")
    print("="*80)
    print(f"File: {data.file_name}")
    
    if data.metadata:
        print(f"\nMetadata:")
        for key, value in data.metadata.items():
            print(f"  {key}: {value}")
    
    print(f"\nTotal molecule segments: {len(data.molecule_segments)}")
    
    if data.mol_pic_clusters:
        print(f"Total molecule image clusters: {len(data.mol_pic_clusters)}")
    
    # Count test types
    test_type_counts = defaultdict(int)
    for segment in data.molecule_segments:
        if segment.has_test_text_sequence:
            for test_type in segment.test_text_sequence.test_type_list:
                test_type_counts[test_type] += 1
    
    if test_type_counts:
        print(f"\nTest type distribution:")
        for test_type, count in sorted(test_type_counts.items()):
            print(f"  {test_type}: {count}")
    
    # Count image data
    segments_with_images = sum(1 for seg in data.molecule_segments if seg.mol_pics)
    total_image_clusters = sum(len(seg.mol_pics) for seg in data.molecule_segments if seg.mol_pics)
    
    if segments_with_images > 0:
        print(f"\nImage data:")
        print(f"  Segments with images: {segments_with_images}")
        print(f"  Total image clusters: {total_image_clusters}")
        if data.mol_pic_clusters:
            total_bboxes = sum(len(cluster.bbox_list) for cluster in data.mol_pic_clusters)
            print(f"  Total bounding boxes: {total_bboxes}")
    
    # Page distribution
    pages = set()
    for segment in data.molecule_segments:
        for page in range(segment.start_page, segment.end_page + 1):
            pages.add(page)
    
    print(f"\nPages with molecule data: {sorted(pages)}")
    print(f"  Page range: {min(pages) if pages else 'N/A'} to {max(pages) if pages else 'N/A'}")


def display_all_content(data):
    """Display all content organized by page."""
    print("\n" + "="*80)
    print(f"CONTENTS OF: {data.file_name}")
    print("="*80)
    
    # Get all pages with molecule segments
    pages = set()
    for segment in data.molecule_segments:
        for page in range(segment.start_page, segment.end_page + 1):
            pages.add(page)
    
    if not pages:
        print("\nNo molecule segments found in this file.")
        return
    
    # Display each page
    for page_num in sorted(pages):
        display_by_page(data, page_num)


def display_by_molecule(data):
    """Display all molecule segments sequentially."""
    print("\n" + "="*80)
    print(f"CONTENTS OF: {data.file_name}")
    print("="*80)
    print(f"\nFound {len(data.molecule_segments)} molecule segment(s):")
    
    for seg_idx, segment in enumerate(data.molecule_segments):
        display_molecule_segment(segment, seg_idx)


def main():
    if len(sys.argv) < 2:
        print("Usage: python view_pkl.py <pkl_file_path> [options]")
        print("\nOptions:")
        print("  --summary    Show summary only")
        print("  --by-molecule  Display all molecules (default)")
        print("  --by-page    Display organized by page")
        print("  --page N     Display specific page only")
        sys.exit(1)
    
    pkl_path = sys.argv[1]
    
    if not os.path.exists(pkl_path):
        print(f"Error: File not found: {pkl_path}")
        sys.exit(1)
    
    # Load the pickle file
    print(f"Loading: {pkl_path}")
    try:
        data = load_pickle_by_filename(pkl_path)
    except Exception as e:
        print(f"Error loading pickle file: {e}")
        sys.exit(1)
    
    # Parse options
    options = sys.argv[2:]
    
    if '--summary' in options:
        display_summary(data)
    elif '--by-page' in options:
        display_all_content(data)
    elif '--by-molecule' in options:
        # Default: show by molecule
        display_summary(data)
        display_by_molecule(data)
    
    # Check if specific page requested
    if '--page' in options:
        try:
            page_idx = options.index('--page')
            page_num = int(options[page_idx + 1])
            # display_summary(data)
            display_by_page(data, page_num)
        except (ValueError, IndexError):
            print("Error: --page requires a page number (e.g., --page 3)")


if __name__ == "__main__":
    main()

