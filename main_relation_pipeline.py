# main_relation_pipeline.py
from extract.relation_extractor import RelationExtractor
from ingest.relation_ingestor import RelationIngestor

def process_relations(chunks, entity_id_map):
    """
    chunks: list of chunk objects
    entity_id_map: dict mapping entity names → normalized ontology IDs
    """
    extractor = RelationExtractor(model_name="mistral")
    relation_ingestor = RelationIngestor("neo4j+s://<uri>", "neo4j", "<password>")

    for chunk in chunks:
        relations = extractor.extract(chunk.page_content)  # list of Relation objects
        for rel in relations:
            e1_id = entity_id_map.get(rel.entity1) or rel.entity1.lower().replace(" ", "_")
            e2_id = entity_id_map.get(rel.entity2) or rel.entity2.lower().replace(" ", "_")
            relation_ingestor.add_relation(e1_id, e2_id, rel.relation_type, rel.confidence)
