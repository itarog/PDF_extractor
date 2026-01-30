# ChemSIE Benchmark Tools

This directory contains the reference implementation for the **ChemSIE-Bench-10** evaluation protocol.

## Usage

```bash
python experiments/benchmark/tools/score_graph.py <prediction.json> <ground_truth.json>
```

## Metrics

1.  **Entity F1**: Measures how many chemical entities (identified by InChI) were correctly recovered.
2.  **Relation Accuracy**: Measures the correctness of links (e.g., Molecule -> Spectrum) given correctly identified entities.
3.  **Provenance IoU**: Measures the overlap between the predicted bounding box and the ground truth region.

## Input Format

Both prediction and ground truth files must adhere to the `ExtractedData` schema defined in `src/chemsie/schemas.py`.
