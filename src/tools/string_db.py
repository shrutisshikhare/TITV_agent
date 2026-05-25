import requests
from typing import Any, Optional
from src.tools.base import BaseTool

STRING_API = "https://string-db.org/api/json"
HUMAN_TAXID = 9606


class StringTool(BaseTool):
    name = "string_network"
    description = (
        "Queries the STRING protein-protein interaction database for a gene. "
        "Returns interaction partners, combined confidence scores, and a hub score "
        "reflecting network centrality. High-scoring hubs are often functionally critical "
        "and may indicate broader pathway relevance for therapeutic intervention."
    )

    def run(
        self, gene_symbol: str, confidence_threshold: float = 0.4, limit: int = 10
    ) -> dict[str, Any]:
        # Step 1: resolve gene to STRING ID
        string_id = self._resolve_identifier(gene_symbol)
        if not string_id:
            return {"error": f"Could not resolve {gene_symbol} in STRING"}

        # Step 2: fetch interactions
        interactions = self._fetch_interactions(string_id, confidence_threshold, limit)

        # Step 3: compute hub score (normalised degree by confidence)
        hub_score = self._compute_hub_score(interactions)

        return {
            "gene_symbol": gene_symbol,
            "string_id": string_id,
            "num_interactions": len(interactions),
            "hub_score": round(hub_score, 3),
            "top_interactors": interactions[:10],
        }

    def _resolve_identifier(self, gene_symbol: str) -> Optional[str]:
        url = f"{STRING_API}/resolve"
        params = {
            "identifier": gene_symbol,
            "species": HUMAN_TAXID,
            "limit": 1,
            "echo_query": 1,
            "caller_identity": "target_prioritisation_agent",
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        results = resp.json()
        return results[0]["stringId"] if results else None

    def _fetch_interactions(
        self, string_id: str, threshold: float, limit: int
    ) -> list[dict]:
        url = f"{STRING_API}/interaction_partners"
        params = {
            "identifiers": string_id,
            "species": HUMAN_TAXID,
            "required_score": int(threshold * 1000),
            "limit": limit,
            "caller_identity": "target_prioritisation_agent",
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        return [
            {
                "partner_symbol": row.get("preferredName_B", ""),
                "combined_score": round(row.get("score", 0), 3),
                "experimental_score": round(row.get("escore", 0), 3),
                "database_score": round(row.get("dscore", 0), 3),
                "textmining_score": round(row.get("tscore", 0), 3),
            }
            for row in data
        ]

    def _compute_hub_score(self, interactions: list[dict]) -> float:
        """
        Hub score = mean combined score across all interactions.
        Reflects both degree (number of partners) and confidence.
        Normalised to [0, 1].
        """
        if not interactions:
            return 0.0
        return sum(i["combined_score"] for i in interactions) / len(interactions)

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
                            "description": "HGNC gene symbol to query in STRING",
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "description": "Minimum interaction confidence score 0-1 (default 0.4)",
                        },
                    },
                    "required": ["gene_symbol"],
                },
            },
        }
