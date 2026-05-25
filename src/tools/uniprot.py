import requests
from typing import Any
from src.tools.base import BaseTool

UNIPROT_API = "https://rest.uniprot.org/uniprotkb/search"


class UniProtTool(BaseTool):
    name = "uniprot_protein_info"
    description = (
        "Queries UniProt for protein-level information given a gene symbol. "
        "Returns subcellular localisation, function summary, and druggability "
        "annotations (membrane topology, active sites, post-translational modifications)."
    )

    def run(self, gene_symbol: str, organism: str = "human") -> dict[str, Any]:
        params = {
            "query": f"gene:{gene_symbol} AND organism_id:9606 AND reviewed:true",
            "format": "json",
            "fields": "id,gene_names,protein_name,organism_name,subcellular_location,"
                      "function,go,keyword,feature",
            "size": 1,
        }
        resp = requests.get(UNIPROT_API, params=params, timeout=15)
        resp.raise_for_status()
        results = resp.json().get("results", [])

        if not results:
            return {"error": f"No reviewed UniProt entry found for {gene_symbol}"}

        entry = results[0]
        return {
            "gene_symbol": gene_symbol,
            "uniprot_id": entry.get("primaryAccession"),
            # "protein_name": self._extract_protein_name(entry),
            # "function": self._extract_function(entry),
            "subcellular_locations": self._extract_localisation(entry),
            # "keywords": self._extract_keywords(entry),
            "druggability_signals": self._extract_druggability(entry),
        }

    def _extract_protein_name(self, entry: dict) -> str:
        try:
            return entry["proteinDescription"]["recommendedName"]["fullName"]["value"]
        except (KeyError, TypeError):
            return "Unknown"

    def _extract_function(self, entry: dict) -> str:
        try:
            comments = entry.get("comments", [])
            for c in comments:
                if c.get("commentType") == "FUNCTION":
                    return c["texts"][0]["value"]
        except (KeyError, IndexError):
            pass
        return ""

    def _extract_localisation(self, entry: dict) -> list[str]:
        locations = []
        try:
            for comment in entry.get("comments", []):
                if comment.get("commentType") == "SUBCELLULAR LOCATION":
                    for loc in comment.get("subcellularLocations", []):
                        loc_val = loc.get("location", {}).get("value", "")
                        if loc_val:
                            locations.append(loc_val)
        except (KeyError, TypeError):
            pass
        return locations

    def _extract_keywords(self, entry: dict) -> list[str]:
        try:
            return [kw["name"] for kw in entry.get("keywords", [])]
        except (KeyError, TypeError):
            return []

    def _extract_druggability(self, entry: dict) -> dict:
        """
        Signals that indicate potential druggability:
        - Membrane protein (surface accessible)
        - Kinase / enzyme activity
        - Presence of binding sites / active sites
        """
        keywords = self._extract_keywords(entry)
        signals = {
            "is_membrane_protein": any(
                kw in keywords for kw in ["Membrane", "Transmembrane", "Cell membrane"]
            ),
            "is_kinase": "Kinase" in keywords,
            "is_enzyme": "Enzyme" in keywords,
            "has_disease_association": "Disease variant" in keywords,
        }
        return signals

    def to_tool_spec(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "gene_symbol": {
                            "type": "string",
                            "description": "HGNC gene symbol (e.g. 'EGFR', 'KRAS')",
                        }
                    },
                    "required": ["gene_symbol"],
                },
            },
        }
