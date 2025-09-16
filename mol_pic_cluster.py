class MolPicCluster:
    def __init__(self, mol_pics):
        self.page_num = mol_pics[0].page_num
        self.mol_pics = mol_pics
        self.bbox_list = [mol_pic.bbox for mol_pic in mol_pics]
        self.cluster_size = len(mol_pics)
        self.get_leading_pic()
        
    def __repr__(self):
        return f'Page: {self.page_num, self.bbox_list}'

    def __str__(self):
        return f'Page: {self.page_num, self.bbox_list}'

    def get_leading_pic(self):
        current_x = 0
        self.leading_pic = None
        for mol_pic in self.mol_pics:
            if mol_pic.bbox[1]>current_x:
                self.leading_pic = mol_pic
                current_x = mol_pic.bbox[1]

def check_matching_of_mol_pics(mol_pic_1, mol_pic_2):
    ATOL = 10
    if mol_pic_1.page_num==mol_pic_2.page_num:
        if abs(mol_pic_1.y0 - mol_pic_2.y0)<=ATOL:
            return True
    return False

def sort_mol_pics_to_clusters(mol_pics):
    clusters = []
    current_cluster = []   
    for idx, mol_pic in enumerate(mol_pics):
        if idx==0:
            current_cluster = [mol_pic]
        else:
            match_flag = check_matching_of_mol_pics(current_cluster[-1], mol_pic)
            if match_flag:
                current_cluster.append(mol_pic)
            else:
                clusters.append(MolPicCluster(current_cluster))
                current_cluster = [mol_pic]
    clusters.append(MolPicCluster(current_cluster))
    return clusters