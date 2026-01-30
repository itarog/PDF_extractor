# Experimental Graph Benchmark Definition

## 1. Motivation
Standard benchmarks (e.g., CLEF, TREC) often focus on isolated tasks: OCR, Image-to-Structure (OCSR), or Named Entity Recognition (NER). ChemSIE's goal is *contextual* extraction. Therefore, we define a new benchmark task: **The Experimental Graph**.

## 2. The Experimental Graph (EG)

An Experimental Graph is a directed graph where:
*   **Nodes** are Chemical Entities (`Molecule`), Procedures (`Reaction`), and Data (`Spectrum`, `Property`).
*   **Edges** represent semantic relationships (`is_reactant`, `is_product`, `has_spectrum`, `has_yield`).

### Minimal Valid Graph
A minimally useful extraction must correctly identify:
1.  **Identity:** Structure (InChI/SMILES) + Label ("1a").
2.  **Role:** Whether it is a product, reactant, or solvent.
3.  **Data:** At least one characterization (NMR, Yield, MP) linked to the *correct* structure.

## 3. Dataset Specification ("ChemSIE-Bench-10")

We propose creating a gold-standard dataset of 10-50 high-quality PDFs with full manual annotation.

### Annotation Schema
The ground truth will be stored as `ExtractedData` JSON files (matching `src/chemsie/schemas.py`).

**Requirements for Ground Truth:**
*   **Complete Bounding Boxes:** Every annotated entity MUST have a bbox.
*   **Normalized Chemistry:** SMILES/InChI must be canonicalized (RDKit).
*   **Explicit Links:** IDs must be consistent.

## 4. Evaluation Metrics

We define three tiers of success:

### Tier 1: Entity Detection (F1-Score)
*   **Strict Match:** InChI matches exactly.
*   **Soft Match:** Tanimoto similarity > 0.99.
*   *Measure:* Precision, Recall, F1 for Molecules and Spectra.

### Tier 2: Relation Extraction (Edge Accuracy)
*   Given a correct Molecule and a correct Spectrum, is the link exists?
*   *Measure:* Accuracy of (Molecule -> Spectrum) links.
*   *Failure Mode:* Assigning the NMR of product 3b to reactant 1a.

### Tier 3: Provenance Quality (IoU)
*   Does the `Provenance.bbox` overlap with the ground truth region?
*   *Measure:* Mean Intersection over Union (IoU).
*   *Threshold:* IoU > 0.5 considered "Correct Location".

## 5. Scoring Script Specification

A future script `scripts/benchmark/score_graph.py` will:
1.  Load `pred.json` and `gt.json`.
2.  Align molecules (Hungarian algorithm on Tanimoto similarity).
3.  Check edges for aligned nodes.
4.  Report Tier 1, 2, and 3 scores.
