from neo4j import GraphDatabase

class RelationIngestor:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def add_relation(self, entity1_id, entity2_id, relation_type, confidence=None):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (e1:Entity {id: $id1})
                MATCH (e2:Entity {id: $id2})
                MERGE (e1)-[r:REL {type: $rel_type}]->(e2)
                SET r.confidence = $conf
                """,
                {"id1": entity1_id, "id2": entity2_id, "rel_type": relation_type, "conf": confidence}
            )
