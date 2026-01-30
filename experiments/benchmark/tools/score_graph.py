import json
import networkx as nx
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass

@dataclass
class EvaluationMetrics:
    entity_f1: float
    relation_accuracy: float
    provenance_iou: float

class ChemSIEGraph:
    def __init__(self, data: Dict[str, Any]):
        self.graph = nx.DiGraph()
        self.load_from_json(data)

    def load_from_json(self, data: Dict[str, Any]):
        # Add Molecules
        for mol in data.get('molecules', []):
            self.graph.add_node(mol['id'], type='molecule', inchi=mol.get('inchi'), smiles=mol.get('smiles'))
        
        # Add Spectra
        for spec in data.get('spectra', []):
            spec_id = f"spec_{spec.get('type')}_{spec.get('molecule_id')}" # Generate stable ID if missing
            self.graph.add_node(spec_id, type='spectrum', spectrum_type=spec.get('type'))
            if spec.get('molecule_id'):
                self.graph.add_edge(spec.get('molecule_id'), spec_id, type='has_spectrum')

    def get_molecules(self):
        return [n for n, attr in self.graph.nodes(data=True) if attr['type'] == 'molecule']

    def get_spectra(self):
        return [n for n, attr in self.graph.nodes(data=True) if attr['type'] == 'spectrum']

def calculate_iou(box1, box2):
    # Simplified IoU calculation for now
    # box: {x0, y0, x1, y1}
    x_left = max(box1['x0'], box2['x0'])
    y_top = max(box1['y0'], box2['y0'])
    x_right = min(box1['x1'], box2['x1'])
    y_bottom = min(box1['y1'], box2['y1'])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    box1_area = (box1['x1'] - box1['x0']) * (box1['y1'] - box1['y0'])
    box2_area = (box2['x1'] - box2['x0']) * (box2['y1'] - box2['y0'])

    return intersection_area / float(box1_area + box2_area - intersection_area)

def evaluate_extraction(pred_path: Path, gt_path: Path) -> EvaluationMetrics:
    with open(pred_path) as f:
        pred_data = json.load(f)
    with open(gt_path) as f:
        gt_data = json.load(f)

    pred_graph = ChemSIEGraph(pred_data)
    gt_graph = ChemSIEGraph(gt_data)

    # 1. Entity Matching (Simplified: Exact InChI Match)
    pred_mols = {attr.get('inchi') for n, attr in pred_graph.graph.nodes(data=True) if attr['type'] == 'molecule' and attr.get('inchi')}
    gt_mols = {attr.get('inchi') for n, attr in gt_graph.graph.nodes(data=True) if attr['type'] == 'molecule' and attr.get('inchi')}
    
    tp = len(pred_mols.intersection(gt_mols))
    fp = len(pred_mols - gt_mols)
    fn = len(gt_mols - pred_mols)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # 2. Relation Accuracy (Placeholder - needs aligned nodes)
    relation_acc = 0.0 # TODO: Implement graph alignment for edge scoring

    # 3. Provenance IoU (Placeholder)
    iou = 0.0 # TODO: Implement aligned bbox comparison

    return EvaluationMetrics(entity_f1=f1, relation_accuracy=relation_acc, provenance_iou=iou)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python score_graph.py <pred.json> <gt.json>")
        sys.exit(1)
    
    metrics = evaluate_extraction(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"Entity F1: {metrics.entity_f1:.4f}")
    print(f"Relation Accuracy: {metrics.relation_accuracy:.4f}")
    print(f"Provenance IoU: {metrics.provenance_iou:.4f}")
