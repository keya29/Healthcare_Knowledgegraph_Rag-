# ontology/ontology_lookup.py
import pandas as pd

class OntologyLookup:
    def __init__(self, csv_path: str = "C:/KG+RAG/data/ontology/mesh_terms.csv"):
        self.csv_path = csv_path
        self.ontology_df = pd.read_csv(csv_path)
        # lowercase terms for fast lookup
        self.ontology_dict = dict(zip(self.ontology_df["term"].str.lower(), self.ontology_df["concept_id"]))

    def get_concept_id(self, term: str):
        return self.ontology_dict.get(term.lower().strip())

    def get_parent_id(self, concept_id: str):
        row = self.ontology_df[self.ontology_df["concept_id"] == concept_id]
        if not row.empty:
            return row.iloc[0]["parent_id"]
        return None
