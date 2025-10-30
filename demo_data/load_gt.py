import pandas as pd

def get_groundtruth_ms(gt_fname):
    gt_df = pd.read_csv(gt_fname)
    overall_gt_stats = _compute_overall_gt_stats(gt_df)
    gt_dict, inner_stats_df = _process_files(gt_df)
    overall_gt_stats = _update_overall_stats(overall_gt_stats, inner_stats_df)
    return gt_dict, overall_gt_stats

def _get_df_stats(gt_df):
    value_count = gt_df['test_type'].value_counts().to_dict()
    return value_count

def _compute_overall_gt_stats(gt_df):
    stats = _get_df_stats(gt_df)
    stats = {'total_' + k: v for k, v in stats.items()}
    stats['total_number_of_tests'] = gt_df.shape[0]
    stats['num_of_files'] = gt_df['f_name'].nunique()
    return stats

def _process_files(gt_df):
    fname_groupby = gt_df.groupby('f_name')
    gt_dict, inner_stats = {}, []

    for f_name, fname_df in fname_groupby:
        groundtruth_ms_dictlist = _process_file_group(fname_df)
        gt_dict[f_name + '.pdf'] = groundtruth_ms_dictlist

        per_file_stats = _get_df_stats(fname_df)
        per_file_stats['num_of_molecules'] = fname_df['molecule_name'].nunique()
        inner_stats.append(per_file_stats)

    index = [f_name + '.pdf' for f_name, _ in fname_groupby]
    inner_stats_df = pd.DataFrame(inner_stats, index=index)
    inner_stats_df = _reorder_and_clean_inner_stats(inner_stats_df)
    return gt_dict, inner_stats_df


def _process_file_group(fname_df):
    names_groupby = fname_df.groupby('molecule_name')
    file_molecules = []

    for _, mol_df in names_groupby:
        mol_dict_list = _build_molecule_dict_list(mol_df)
        file_molecules.append(mol_dict_list)
    return file_molecules


def _build_molecule_dict_list(mol_df):
    mol_dict = mol_df[['molecule_name', 'test_type', 'test_text']].T.to_dict()
    return [
        {**line_dict, 'line_idx': idx}
        for idx, line_dict in mol_dict.items()
    ]


def _reorder_and_clean_inner_stats(inner_stats_df):
    cols = ['num_of_molecules'] + [
        c for c in inner_stats_df.columns if c != 'num_of_molecules'
    ]
    return inner_stats_df[cols].fillna(0)


def _update_overall_stats(overall_gt_stats, inner_stats_df):
    avg_row = inner_stats_df.select_dtypes(include='number').mean().to_dict()
    avg_row = {'mean_' + k: v for k, v in avg_row.items()}
    overall_gt_stats.update(avg_row)
    overall_gt_stats['inner_stats'] = inner_stats_df
    return overall_gt_stats

