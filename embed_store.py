# embed_store.py
from langchain_community.vectorstores import Neo4jVector

class EmbeddingStore:
    def __init__(self, embedding_model, uri, user, password):
        self.embedding_model = embedding_model
        self.store = Neo4jVector.from_existing_graph(
            embedding=self.embedding_model,
            url=uri,
            username=user,
            password=password,
            index_name="chunk_embeddings",
            node_label="Chunk",
            text_node_property="text",
            embedding_node_property="embedding",
        )

    def add_chunks(self, chunks):
        texts = [c.page_content for c in chunks]
        metadatas = [c.metadata for c in chunks]
        self.store.add_texts(texts=texts, metadatas=metadatas)
