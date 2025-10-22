# ontology_xml_to_csv_lxml.py
from lxml import etree
import pandas as pd
from pathlib import Path

xml_path = Path("C:/KG+RAG/desc2025_clean.xml")
output_csv = Path("data/ontology/mesh_terms.csv")
output_csv.parent.mkdir(parents=True, exist_ok=True)

parser = etree.XMLParser(recover=True, encoding="utf-8")
tree = etree.parse(str(xml_path), parser)
root = tree.getroot()

records = []
for desc in root.findall("DescriptorRecord"):
    concept_id = desc.findtext("DescriptorUI")
    name = desc.findtext("DescriptorName/String")
    tree_number = desc.findtext("TreeNumberList/TreeNumber")
    parent_id = ".".join(tree_number.split(".")[:-1]) if tree_number and "." in tree_number else None
    records.append((concept_id, name, parent_id))

df = pd.DataFrame(records, columns=["concept_id", "term", "parent_id"])
df.to_csv(output_csv, index=False)
print(f"[INFO] Parsed and saved {len(df)} MeSH terms to {output_csv}")
