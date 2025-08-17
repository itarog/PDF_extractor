import os
import pickle
from collections import defaultdict

class ProccessedPdf:
    def __init__(self, file_name, metadata=None, molecule_segments=None, mol_pic_clusters=None):
        self.file_name = file_name
        self.metadata = metadata   
        self.molecule_segments = molecule_segments if molecule_segments else []   
        self.mol_pic_clusters = mol_pic_clusters if mol_pic_clusters else []
        
    def __repr__(self):
        return f'File: {self.file_name}, Number of molecule segments: {len(self.molecule_segments)}, Number of pictures: {len(self.mol_pics)}'

class ProccessedMoleculeSegments:
    def __init__(self, file_name, metadata=None, molecule_segments=[]):
        self.file_name = file_name
        self.metadata = metadata
        self.molecule_segments = molecule_segments

class ProccessedPdfPictures:
    def __init__(self, file_name, metadata=None, mol_pic_clusters=[]):
        self.file_name = file_name
        self.metadata = metadata
        self.mol_pic_clusters = mol_pic_clusters

def save_object(obj, filename):
    with open(filename, 'wb') as outp:  # Overwrites any existing file.
        pickle.dump(obj, outp, pickle.HIGHEST_PROTOCOL)

def pickle_loader(filename):
    try:
        import pickle5 as pickle
    except:
        import pickle
    """ Deserialize a file of pickled objects. """
    with open(filename, "rb") as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break

def get_serial_from_pickle_name(pickle_name):
    return pickle_name.split('_')[-2]

def organize_pkl_files(pickle_files):
    organized_files = defaultdict(list)
    for pickle_file in pickle_files:
        serial = get_serial_from_pickle_name(pickle_file)
        organized_files[serial].append(pickle_file)
    return organized_files

def load_pickle_by_filename(pkl_filename):
    loaded_data = list(pickle_loader(pkl_filename))[0]
    return loaded_data

def load_pickle_by_dir(pkl_dir):
    pkl_files = [os.path.join(pkl_dir ,f) for f in os.listdir(pkl_dir) if f.endswith('pkl')]
    loaded_obj_list = [load_pickle_by_filename(f) for f in pkl_files]
    return loaded_obj_list

def load_mol_pic_clusters_dict(pkl_dir):
    loaded_data = load_pickle_by_dir(pkl_dir)
    loaded_dict = {obj.file_name: obj.mol_pic_clusters for obj in loaded_data}
    return loaded_dict

def load_molecule_segments_dict(pkl_dir):
    loaded_data = load_pickle_by_dir(pkl_dir)
    loaded_dict = {obj.file_name: obj.molecule_segments for obj in loaded_data}
    return loaded_dict


# def load_pickle_data_by_serial(pickle_dict, serial):
#     data = {'file_name': None, 'metadata': None, 'molecule_segments': None, 'mol_pics': None}
#     file_names = pickle_dict[serial]
#     for pickle_file in file_names:
#         if 'pics' in pickle_file:
#             loaded_data = load_pickle_by_filename(pickle_file)
#             data.update(loaded_data.__dict__)
#         elif 'text' in pickle_file:
#             loaded_data = load_pickle_by_filename(pickle_file)
#             data.update(loaded_data.__dict__)
#     proccessed_pdf = ProccessedPdf(data['file_name'], data['metadata'], data['molecule_segments'], data['mol_pics'])
#     return proccessed_pdf

# def load_pickle_data_by_dir(pics_pickle_dir=None, text_pickle_dir=None):
#     loaded_data = None
#     if not pics_pickle_dir and not text_pickle_dir:
#         print('error - need at least one folder')
#     pics_pickle_files, text_pickle_files = [], []
#     if pics_pickle_dir:
#         pics_pickle_files = [os.path.join(pics_pickle_dir, file) for file in os.listdir(pics_pickle_dir) if file.endswith('pkl')]
#     if text_pickle_dir:
#         text_pickle_files = [os.path.join(text_pickle_dir, file) for file in os.listdir(text_pickle_dir) if file.endswith('pkl')]
#     pickle_files = pics_pickle_files + text_pickle_files
#     if pickle_files:
#         organized_pickle_files = organize_pkl_files(pickle_files)
#         loaded_data = [load_pickle_data_by_serial(organized_pickle_files, key) for key in organized_pickle_files.keys()]
#     return loaded_data