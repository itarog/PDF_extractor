# Using ChemSIE manager

## loading ground truth data

```
chemsie_db = CHEMSIE()
gt_fname = './demo_data/ground_truth.csv'
chemsie_db.process_gt_data(gt_fname)
```

## Extracting data from pdf dir

```
chemsie_db = CHEMSIE()
gt_fname = './demo_data/ground_truth.csv'
chemsie_db.process_gt_data(gt_fname)
chemsie_db.process_extracted_data(molecule_segments_dict=filled_matched_segments_dict)

```
