# extract/ontology_matcher.py
from ontology.ontology_lookup import OntologyLookup

class OntologyMatcher:
    def __init__(self, ontology_csv: str = "data/ontology/umls_terms.csv"):
        self.lookup = OntologyLookup(ontology_csv)

    def normalize_entities(self, entities):
        """
        entities: list of dicts or objects with .name field
        returns: list of dicts with concept_id added
        """
        def _get(obj, attr, default=None):
            # Support pydantic models / objects with attributes and plain dicts
            if hasattr(obj, attr):
                try:
                    return getattr(obj, attr)
                except AttributeError:
                    pass
            if isinstance(obj, dict):
                return obj.get(attr, default)
            return default

        normalized = []
        for entity in entities:
            name = _get(entity, "name")
            concept_id = self.lookup.get_concept_id(name)
            parent_id = None
            if concept_id:
                parent_id = self.lookup.get_parent_id(concept_id)

            normalized.append({
                "name": name,
                "concept_id": concept_id,
                "parent_id": parent_id,
                "type": _get(entity, "type"),
                "relation": _get(entity, "relation")
            })
        return normalized
