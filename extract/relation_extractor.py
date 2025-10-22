# extract/relation_extractor.py
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from typing import List
from langchain_ollama import ChatOllama  # or ChatOpenAI if cloud model


class Relation(BaseModel):
    entity1: str
    entity2: str
    relation_type: str
    confidence: float | None = None


class RelationList(BaseModel):
    relations: List[Relation]


class RelationExtractor:
    def __init__(self, model_name="mistral", temperature=0):
        self.llm = ChatOllama(model=model_name, temperature=temperature)
        self.parser = PydanticOutputParser(pydantic_object=RelationList)
        self.prompt = ChatPromptTemplate.from_template(
            """Extract all entity-entity relationships from the given text chunk.
               Return a JSON object with key 'relations' containing a list of objects with fields: entity1, entity2, relation_type, confidence (optional).
               Example:
               {{
                 "relations": [
                   {"entity1": "aspirin", "relation_type": "treats", "entity2": "fever", "confidence": 0.9}
                 ]
               }}
               Text: {chunk_text}
            """
        )

    def extract(self, chunk_text: str):
        chain = self.prompt | self.llm | self.parser
        res = chain.invoke({"chunk_text": chunk_text})
        return res.relations
