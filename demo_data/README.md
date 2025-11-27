# Benchmark data
While the reader can use any aproriate pdf document, benchmark data is prodived here.

## Benchmark 2111

File dir: '.\demo_data\' (24 files) <br>
Details regarding the files can be found at 'file_description.xlsx' (filename, description, first author, title, notes) <br>
The manually extracted data can be found at 'ground_truth.csv' (filename, molecule name, test type, test text, opsin smiles, notes) <br>

## Reproducing results and figures

### Loading ground truth

All of the experimental data found in the PDF of the experimental data have been manually collected and used to evaluate this tool. This data is stored in csv file with four columns ..

The file can be loaded using ...

```
from .demo_data.load_gt import get_groundtruth_ms

ground_truth_fname = "ground_truth.csv"
gt_dict, overall_gt_stats = get_groundtruth_ms(ground_truth_fname) 

```
In gt_dict the keys are .. and the values are ..
In overall_gt_stats the keys are .. and the values are ..


### Converting molecule name to SMILES

The name of the molecule can be transformed into SMILES using OPsin (IUPAC names) or PubChem (generic names). This requires internet connection  


```
from .demo_data.molname_to_SMILES import opsin_query, pubchem_name_to_smiles

ground_truth_fname = "ground_truth.csv"
gt_df = pd.read_csv(ground_truth_fname)
molecule_names = gt_df.molecule_name.unique()
smiles_dict = dict()
for nm in molecule_names:
    try:
        info = opsin_query(nm)
        smiles = info.get('smiles')
    except Exception as e:
        smiles = ''
    if smiles == '':
        smiles = pubchem_name_to_smiles(nm)
    smiles_dict[nm] = smiles
```
