# extract/ontology_matcher.py
import re
from difflib import get_close_matches

class OntologyMatcher:
    def __init__(self, ontology_dict: dict[str, str], fuzzy: bool = True):
        """
        ontology_dict: {"fever": "UMLS:C0015967", "aspirin": "UMLS:C0004057"}
        fuzzy: enable fuzzy matching for unseen terms
        """
        self.ontology = {k.lower(): v for k, v in ontology_dict.items()}
        self.fuzzy = fuzzy

    def _normalize_text(self, text: str) -> str:
        return re.sub(r'[^a-z0-9 ]+', '', text.lower().strip())

    def match(self, text: str) -> str | None:
        """Return ontology ID if found, else None."""
        normalized = self._normalize_text(text)
        if normalized in self.ontology:
            return self.ontology[normalized]

        if self.fuzzy:
            candidates = get_close_matches(normalized, self.ontology.keys(), n=1, cutoff=0.85)
            if candidates:
                return self.ontology[candidates[0]]
        return None
