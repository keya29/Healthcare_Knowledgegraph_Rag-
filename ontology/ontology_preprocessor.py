# ontology/ontology_preprocessor.py
import pandas as pd
from pathlib import Path

class OntologyPreprocessor:
    def __init__(self, raw_path: str, output_dir: str = "data/ontology"):
        self.raw_path = Path(raw_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def preprocess(self):
        df = pd.read_csv(self.raw_path)
        df = df[["concept_id", "term", "parent_id"]].drop_duplicates()
        csv_path = self.output_dir / "mesh_terms.csv"
        df.to_csv(csv_path, index=False)
        print(f"[INFO] Ontology saved at {csv_path}")
