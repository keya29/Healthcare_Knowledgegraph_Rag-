# ingest/embedding_ingestor.py
from langchain_community.vectorstores import Neo4jVector

class EmbeddingIngestor:
    def __init__(self, embedding_model, uri, user, password):
        self.store = Neo4jVector.from_existing_graph(
            embedding=embedding_model,
            url=uri,
            username=user,
            password=password,
            index_name="chunk_embeddings",
            node_label="Chunk",
            text_node_property="text",
            embedding_node_property="embedding",
            text_node_properties=["text"]  # Added required parameter
        )

    def add_chunks(self, chunks):
        texts = [c.page_content for c in chunks]
        metadatas = [c.metadata for c in chunks]
        self.store.add_texts(texts=texts, metadatas=metadatas)

    def add_entities(self, entities):
        texts = [e["name"] for e in entities]
        metadatas = [{"type": e["type"], "id": e["id"]} for e in entities]
        self.store.add_texts(texts=texts, metadatas=metadatas)
