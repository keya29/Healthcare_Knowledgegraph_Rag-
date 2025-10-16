# config.py
from langchain.embeddings import HuggingFaceEmbeddings

# AuraDB connection details
NEO4J_URI = "neo4j+ssc://09b008db.databases.neo4j.io:7687"  # Added port number
NEO4J_DB = "neo4j"  # Default database name
NEO4J_USER = "neo4j"
NEO4J_PASS = "Cm4lY_2AebAX3x8jidMhrPQDFqyqTJH6XOiBDAppLvg"

EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
