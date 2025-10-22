# ingest/neo4j_ingestor.py
from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable
import pandas as pd
import time


class Neo4jIngestor:
    def __init__(self, uri, user, password):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print("[INFO] Connected to Neo4j")
        except AuthError as e:
            raise AuthError(f"Neo4j authentication failed: {e}")
        except ServiceUnavailable as e:
            raise ConnectionError(f"Neo4j service unavailable: {e}")

    def _run_with_retry(self, session, query, params=None, retries=3, backoff=1.0):
        attempt = 0
        params = params or {}
        while True:
            try:
                return session.run(query, params)
            except ServiceUnavailable:
                attempt += 1
                if attempt > retries:
                    raise
                time.sleep(backoff * (2 ** (attempt - 1)))

    # ------------------------------
    # 1. Chunk ingestion
    # ------------------------------
    def insert_chunks(self, chunks):
        with self.driver.session() as session:
            for i, chunk in enumerate(chunks):
                self._run_with_retry(
                    session,
                    """
                    MERGE (c:Chunk {id: $id})
                    SET c.text = $text,
                        c.source = $source
                    """,
                    {
                        "id": f"chunk_{i}",
                        "text": chunk.page_content,
                        "source": chunk.metadata.get("source", "unknown"),
                    },
                )

    # ------------------------------
    # 2. Entity ingestion + ontology mapping
    # ------------------------------
    def insert_entity_and_relation(
        self, chunk_id=None, chunk_text=None, entity_name=None, entity_id=None, entity_type=None, concept_id=None, relation=None
    ):
        """Insert an entity node and attach it to the chunk.

        Prefer using chunk_id (safer). The function keeps chunk_text fallback for
        backwards compatibility. Optionally map the entity to an ontology concept
        and create a relation node connected to the entity.
        """
        with self.driver.session() as session:
            # Choose matching by id if provided, otherwise fall back to text
            if chunk_id is not None:
                match_clause = "MATCH (c:Chunk {id: $chunk_key})"
                match_params = {"chunk_key": chunk_id}
            else:
                match_clause = "MATCH (c:Chunk {text: $chunk_key})"
                match_params = {"chunk_key": chunk_text}

            params = {
                **match_params,
                "entity_id": entity_id,
                "entity_name": entity_name,
                "entity_type": entity_type,
            }

            # Create entity and relationship to chunk
            self._run_with_retry(
                session,
                f"""
                {match_clause}
                MERGE (e:Entity {{id: $entity_id}})
                SET e.name = $entity_name,
                    e.type = $entity_type
                MERGE (c)-[:CONTAINS]->(e)
                """,
                params,
            )

            # Optional ontology mapping
            if concept_id:
                self._run_with_retry(
                    session,
                    """
                    MATCH (e:Entity {id: $entity_id})
                    MATCH (o:Concept {concept_id: $concept_id})
                    MERGE (e)-[:MAPS_TO]->(o)
                    """,
                    {"entity_id": entity_id, "concept_id": concept_id},
                )

            # Optional relation node attached to this entity
            if relation:
                self._run_with_retry(
                    session,
                    """
                    MATCH (e:Entity {id: $entity_id})
                    MERGE (r:Relation {type: $relation})
                    MERGE (e)-[:HAS_RELATION]->(r)
                    """,
                    {"entity_id": entity_id, "relation": relation},
                )

    # ------------------------------
    # 3. Ontology ingestion
    # ------------------------------
    def ingest_ontology(self, csv_path):
        df = pd.read_csv(csv_path)
        with self.driver.session() as session:
            for _, row in df.iterrows():
                self._run_with_retry(
                    session,
                    """
                    MERGE (c:Concept {concept_id: $concept_id})
                    SET c.term = $term
                    WITH c
                    CALL {
                        WITH c
                        MATCH (p:Concept {concept_id: $parent_id})
                        MERGE (p)-[:PARENT_OF]->(c)
                    }
                    """,
                    {
                        "concept_id": row["concept_id"],
                        "term": row["term"],
                        "parent_id": row.get("parent_id"),
                    },
                )

    def insert_relation_between_entities(self, e1_id, e2_id, relation_type, confidence=None):
        """Create a relation node and connect two existing entities by id."""
        with self.driver.session() as session:
            params = {"e1_id": e1_id, "e2_id": e2_id, "relation_type": relation_type}
            if confidence is not None:
                params["confidence"] = confidence

            query = """
            MATCH (a:Entity {id: $e1_id}), (b:Entity {id: $e2_id})
            MERGE (r:Relation {type: $relation_type})
            SET r.confidence = coalesce($confidence, r.confidence)
            MERGE (a)-[:RELATES_TO]->(r)-[:RELATES_TO]->(b)
            RETURN r
            """
            self._run_with_retry(session, query, params)

    def close(self):
        self.driver.close()
        print("[INFO] Neo4j connection closed")
