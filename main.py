import os
from dotenv import load_dotenv
from ingest.chunk_loader import load_chunks
from extract.entity_extractor import EntityExtractor
from extract.ontology_matcher import OntologyMatcher
from extract.relation_extractor import RelationExtractor
from ingest.neo4j_ingestor import Neo4jIngestor

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")

entity_extractor = EntityExtractor(model_name="mistral")
ontology_matcher = OntologyMatcher(r"C:\KG+RAG\data\ontology\mesh_terms.csv")
relation_extractor = RelationExtractor(model_name="mistral")
neo4j_ingestor = Neo4jIngestor(NEO4J_URI, NEO4J_USER, NEO4J_PASS)

# Auto-detect where PDFs live. Common places: input/, data/pdfs/, data/
possible_paths = ["input/", os.path.join("data", "pdfs"), "data/"]
pdf_path = None
for p in possible_paths:
    if os.path.isdir(p):
        # quick check for any PDF files inside
        files = [f for f in os.listdir(p) if f.lower().endswith(".pdf")]
        if files:
            pdf_path = p
            break

if pdf_path is None:
    # fallback to data/ (may be empty)
    pdf_path = "data/"

print(f"[INFO] Using pdf path: {pdf_path}")
chunks = load_chunks(pdf_path)
print(f"[INFO] Loaded {len(chunks)} chunks from {pdf_path}")

print("[INFO] Ingesting ontology concepts into Neo4j...")
neo4j_ingestor.ingest_ontology(r"C:\KG+RAG\data\ontology\mesh_terms.csv")

print("[INFO] Ingesting chunks...")
neo4j_ingestor.insert_chunks(chunks)

# If TEST_NO_LLM is set, skip LLM extraction and relations to quickly validate chunk
# ingestion and Neo4j connectivity in environments without LLM access.
if os.getenv("TEST_NO_LLM", "0") == "1":
    print("[INFO] TEST_NO_LLM=1 set — skipping LLM extraction and relation linking.")
    neo4j_ingestor.close()
    print("[INFO] Exiting early after chunk ingestion (TEST_NO_LLM).")
    raise SystemExit(0)

# Quick test mode: mock extractor to verify entity+relation ingestion without calling an LLM.
if os.getenv("TEST_MOCK_EXTRACTOR", "0") == "1":
    max_chunks = int(os.getenv("MAX_CHUNKS", "5"))
    print(f"[INFO] TEST_MOCK_EXTRACTOR=1 set — creating mock entities/relations for up to {max_chunks} chunks")
    for idx, chunk in enumerate(chunks):
        if max_chunks and idx >= max_chunks:
            break
        chunk_id = None
        try:
            chunk_id = chunk.metadata.get("chunk_id")
        except Exception:
            pass

        # create two mock entities per chunk and a relation between them
        e1_id = f"mock_{idx}_a"
        e2_id = f"mock_{idx}_b"
        neo4j_ingestor.insert_entity_and_relation(
            chunk_id=chunk_id,
            chunk_text=chunk.page_content,
            entity_name=f"MockEntity_{idx}_A",
            entity_id=e1_id,
            entity_type="Mock",
        )
        neo4j_ingestor.insert_entity_and_relation(
            chunk_id=chunk_id,
            chunk_text=chunk.page_content,
            entity_name=f"MockEntity_{idx}_B",
            entity_id=e2_id,
            entity_type="Mock",
        )

        neo4j_ingestor.insert_relation_between_entities(e1_id, e2_id, "mock_relation", confidence=0.95)

    neo4j_ingestor.close()
    print("[INFO] Mock ingestion finished — closed connection.")
    raise SystemExit(0)

print("[INFO] Extracting and linking entities...")
max_chunks = int(os.getenv("MAX_CHUNKS", "0"))
for i, chunk in enumerate(chunks):
    if max_chunks and i >= max_chunks:
        break
    extracted_entities = entity_extractor.extract(chunk.page_content)
    normalized_entities = ontology_matcher.normalize_entities(extracted_entities)

    # DEBUG: show first few extracted/normalized entities for this chunk
    print("--- Chunk preview ---")
    print("Raw extracted (first 5):", extracted_entities[:5] if hasattr(extracted_entities, '__iter__') else extracted_entities)
    print("Normalized (first 5):", normalized_entities[:5])

    for ent in normalized_entities:
        # prefer using chunk_id (more reliable) when available
        chunk_id = None
        try:
            chunk_id = chunk.metadata.get("chunk_id")
        except Exception:
            pass

        neo4j_ingestor.insert_entity_and_relation(
            chunk_id=chunk_id,
            chunk_text=chunk.page_content,
            entity_name=ent["name"],
            entity_id=(ent.get("concept_id") or ent.get("id") or ent["name"]),
            entity_type=ent.get("type", "Unknown"),
            relation=ent.get("relation")
        )

    # After entities are created for this chunk, extract relations and link them
    relations = relation_extractor.extract(chunk.page_content)
    print("Extracted relations:", relations)

    # Build a lookup from entity name to id for resolution
    name_to_id = {e["name"]: (e.get("concept_id") or e.get("id") or e["name"]) for e in normalized_entities}
    for rel in relations:
        e1_name = rel.entity1
        e2_name = rel.entity2
        e1_id = name_to_id.get(e1_name) or e1_name.lower().replace(" ", "_")
        e2_id = name_to_id.get(e2_name) or e2_name.lower().replace(" ", "_")
        neo4j_ingestor.insert_relation_between_entities(e1_id, e2_id, rel.relation_type, rel.confidence)

neo4j_ingestor.close()
print("[INFO] Knowledge Graph creation completed successfully.")
