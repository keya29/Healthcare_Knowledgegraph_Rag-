# main.py
from extract import relation_extractor
from ingest.document_loader import DocumentLoader
from ingest.text_splitter import Chunker
from ingest.neo4j_ingestor import Neo4jIngestor
from ingest.embedding_ingestor import EmbeddingIngestor
from ingest.relation_ingestor import RelationIngestor
from extract.entity_extractor import EntityExtractor
from extract.ontology_matcher import OntologyMatcher
from extract.relation_extractor import RelationExtractor
from langchain_ollama import ChatOllama  # for local Mistral
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASS, EMBEDDING_MODEL

# 1. Load & chunk documents
loader = DocumentLoader()
docs = loader.load_pdf("C:\KG+RAG\input\HIV-AIDS Care and Treatment, FHI 360.pdf")
chunker = Chunker(chunk_size=800, chunk_overlap=100)
chunks = chunker.chunk(docs)

# 2. Insert chunk nodes into Neo4j
neo4j = Neo4jIngestor(NEO4J_URI, NEO4J_USER, NEO4J_PASS)
neo4j.insert_chunks(chunks)  # passing all chunks at once

# 3. Add embeddings for chunks
embedder = EmbeddingIngestor(EMBEDDING_MODEL, NEO4J_URI, NEO4J_USER, NEO4J_PASS)
embedder.add_chunks(chunks)

# 4. Extract entities & normalize
entity_extractor = EntityExtractor(model_name="mistral")
ontology_matcher = OntologyMatcher({
    "fever": "UMLS:C0015967",
    "aspirin": "UMLS:C0004057"
})

entity_id_map = {}  # name -> normalized id
for chunk in chunks:
    entities = entity_extractor.extract(chunk.page_content)
    for ent in entities:
        entity_id = ontology_matcher.match(ent.name) or ent.name.lower().replace(" ", "_")
        entity_id_map[ent.name] = entity_id
        neo4j.insert_entity_and_relation(
            chunk_text=chunk.page_content,
            entity_name=ent.name,
            entity_id=entity_id,
            entity_type=ent.type,
            relation=ent.relation
        )

# 5. Add embeddings for entities
# 5. Add embeddings for chunks
embedder = EmbeddingIngestor(EMBEDDING_MODEL, NEO4J_URI, NEO4J_USER, NEO4J_PASS)
embedder.add_chunks(chunks)

# 6. Add embeddings for entities and process relations
embedder.add_entities([{"name": k, "type": "unknown", "id": v} for k, v in entity_id_map.items()])

# Initialize relation ingestor
relation_ingestor = RelationIngestor(NEO4J_URI, NEO4J_USER, NEO4J_PASS)

# Process relations
for chunk in chunks:
    relations = relation_extractor.extract(chunk.page_content)
    for rel in relations:
        e1_id = entity_id_map.get(rel.entity1) or rel.entity1.lower().replace(" ", "_")
        e2_id = entity_id_map.get(rel.entity2) or rel.entity2.lower().replace(" ", "_")
        relation_ingestor.add_relation(e1_id, e2_id, rel.relation_type, rel.confidence)
