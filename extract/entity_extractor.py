# extract/entity_extractor.py

from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from langchain_ollama import ChatOllama

class Entity(BaseModel):
    name: str
    type: str
    relation: str | None = None

class EntityList(BaseModel):
    entities: List[Entity]

class EntityExtractor:
    def __init__(self, model_name="mistral"):
        self.llm = ChatOllama(model=model_name, temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=EntityList)
        self.prompt = ChatPromptTemplate.from_template(
            """Extract all domain-relevant entities and relationships from this text.
               Format the response as a JSON object with a single key 'entities' containing
               a list of entity objects. Each entity object should have fields: name, type, relation.
               
               Example format:
               {{
                   "entities": [
                       {{"name": "HIV", "type": "Disease", "relation": null}},
                       {{"name": "Treatment", "type": "Process", "relation": "Related to HIV"}}
                   ]
               }}
               
               Text: {chunk_text}"""
        )

    def extract(self, chunk_text):
        chain = self.prompt | self.llm | self.parser
        result = chain.invoke({"chunk_text": chunk_text})
        return result.entities  # Return the list of entities
