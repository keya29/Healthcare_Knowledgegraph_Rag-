# extract/relation_extractor.py
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from langchain_ollama import ChatOllama  # or ChatOpenAI if cloud model

class Relation(BaseModel):
    entity1: str
    entity2: str
    relation_type: str
    confidence: float | None = None

class RelationExtractor:
    def __init__(self, model_name="mistral", temperature=0):
        self.llm = ChatOllama(model=model_name, temperature=temperature)
        self.parser = PydanticOutputParser(pydantic_object=Relation)
        self.prompt = ChatPromptTemplate.from_template(
            """Given a text chunk, extract all entity-entity relationships. 
               Return JSON list of objects with fields: entity1, entity2, relation_type, confidence.
               Text: {chunk_text}"""
        )

    def extract(self, chunk_text: str):
        chain = self.prompt | self.llm | self.parser
        return chain.invoke({"chunk_text": chunk_text})
