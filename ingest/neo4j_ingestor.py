# neo4j_ingestor.py
from neo4j import GraphDatabase

class Neo4jIngestor:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def insert_chunks(self, chunks):
        with self.driver.session() as session:
            for i, chunk in enumerate(chunks):
                session.run(
                    """
                    MERGE (c:Chunk {id: $id})
                    SET c.text = $text,
                        c.source = $source
                    """,
                    {"id": f"chunk_{i}", "text": chunk.page_content, "source": chunk.metadata.get("source", "unknown")}
                )

    def insert_entity_and_relation(self, chunk_text, entity_name, entity_id, entity_type, relation=None):
        with self.driver.session() as session:
            # Create entity and relationship to chunk
            session.run(
                """
                MATCH (c:Chunk {text: $chunk_text})
                MERGE (e:Entity {id: $entity_id})
                SET e.name = $entity_name,
                    e.type = $entity_type
                MERGE (c)-[:CONTAINS]->(e)
                """,
                {
                    "chunk_text": chunk_text,
                    "entity_id": entity_id,
                    "entity_name": entity_name,
                    "entity_type": entity_type
                }
            )
            
            # If there's a relation specified, create a relationship node
            if relation:
                session.run(
                    """
                    MATCH (e:Entity {id: $entity_id})
                    MERGE (r:Relation {type: $relation})
                    MERGE (e)-[:HAS_RELATION]->(r)
                    """,
                    {
                        "entity_id": entity_id,
                        "relation": relation
                    }
                )
