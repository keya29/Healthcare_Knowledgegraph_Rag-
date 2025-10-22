import os
import sys
from neo4j import GraphDatabase

# Ensure repo root is on sys.path so imports like `config` work when running from tools/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from config import NEO4J_URI, NEO4J_USER, NEO4J_PASS
except Exception as e:
    print("Failed to import config.py from project root:", e)
    print("Falling back to environment variables NEO4J_URI / NEO4J_USER / NEO4J_PASS")
    # Load .env if present
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass

    NEO4J_URI = os.environ.get("NEO4J_URI")
    NEO4J_USER = os.environ.get("NEO4J_USER")
    NEO4J_PASS = os.environ.get("NEO4J_PASS")
    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASS]):
        raise RuntimeError("NEO4J credentials not found in config.py or environment variables (.env)")

def run_query(driver, cypher):
    with driver.session() as session:
        return [record for record in session.run(cypher)]

def main():
    print(f"Connecting to {NEO4J_URI} as {NEO4J_USER}")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

    try:
        driver.verify_connectivity()
    except Exception as e:
        print("Connectivity check failed:", e)
        return

    # Total relationships in DB
    q_rel_count = "MATCH ()-[r]->() RETURN count(r) AS rel_count"
    rel_count = run_query(driver, q_rel_count)[0]["rel_count"]
    print(f"Total relationships (all types): {rel_count}")

    # Labels and counts
    try:
        q_labels = "CALL db.labels() YIELD label, count RETURN label, count ORDER BY count DESC"
        labels = run_query(driver, q_labels)
        print("Labels in DB and counts:")
        for rec in labels:
            print(f"  {rec['label']}: {rec['count']}")
    except Exception:
        # fallback: sample labels via scanning small set
        print("Could not run CALL db.labels(); proceeding without label summary")

    # Count relation nodes
    q_relation_nodes = "MATCH (r:Relation) RETURN count(r) AS relation_nodes"
    relation_nodes = run_query(driver, q_relation_nodes)[0]["relation_nodes"]
    print(f"Relation nodes (label Relation): {relation_nodes}")

    # Top relationship types by count
    q_types = "MATCH ()-[r]->() RETURN type(r) AS rel_type, count(*) AS cnt ORDER BY cnt DESC LIMIT 50"
    types = run_query(driver, q_types)
    print("Top relationship types and counts:")
    for rec in types:
        print(f"  {rec['rel_type']}: {rec['cnt']}")

    # Sample relation node connections (both HAS_RELATION and RELATES_TO patterns)
    q_sample1 = (
        "MATCH (e:Entity)-[hr:HAS_RELATION]->(r:Relation) RETURN e.name AS entity, r.type AS rel_type LIMIT 20"
    )
    s1 = run_query(driver, q_sample1)
    print("Sample HAS_RELATION edges (entity -> relation.type):")
    for rec in s1:
        print(f"  {rec['entity']} -> {rec['rel_type']}")

    # Sample some nodes by label
    print("\nSample nodes by label:")
    try:
        sample_chunk = run_query(driver, "MATCH (c:Chunk) RETURN c.id AS id, c.source AS source, substring(c.text,0,120) AS text LIMIT 10")
        print("Chunks (sample):")
        for r in sample_chunk:
            print(f"  id={r['id']}, source={r['source']}")
    except Exception:
        print("No Chunk nodes or query failed")

    try:
        sample_entity = run_query(driver, "MATCH (e:Entity) RETURN e.id AS id, e.name AS name, e.type AS type LIMIT 10")
        print("Entities (sample):")
        for r in sample_entity:
            print(f"  id={r['id']}, name={r['name']}, type={r['type']}")
    except Exception:
        print("No Entity nodes or query failed")

    try:
        sample_concept = run_query(driver, "MATCH (o:Concept) RETURN o.concept_id AS id, o.term AS term LIMIT 10")
        print("Concepts (sample):")
        for r in sample_concept:
            print(f"  id={r['id']}, term={r['term']}")
    except Exception:
        print("No Concept nodes or query failed")

    q_sample2 = (
        "MATCH (a:Entity)-[:RELATES_TO]->(r:Relation)-[:RELATES_TO]->(b:Entity) RETURN a.name AS a, r.type AS rel_type, b.name AS b LIMIT 20"
    )
    s2 = run_query(driver, q_sample2)
    print("Sample RELATES_TO chain edges (entity -rel-> relation -rel-> entity):")
    for rec in s2:
        print(f"  {rec['a']} -[{rec['rel_type']}]- {rec['b']}")

    driver.close()

if __name__ == '__main__':
    main()
