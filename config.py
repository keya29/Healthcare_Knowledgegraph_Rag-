# config.py
from langchain.embeddings import HuggingFaceEmbeddings

# AuraDB connection details
NEO4J_URI = ""  # Added port number
NEO4J_DB = "neo4j"  # Default database name
NEO4J_USER = "neo4j"
NEO4J_PASS = ""

EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
