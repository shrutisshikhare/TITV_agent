import requests
from typing import Any, Optional
from src.tools.base import BaseTool

OPENTARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"


class OpenTargetsTool(BaseTool):
    name = "opentargets_associations"
    description = (
        "Queries the OpenTargets Platform for disease-target associations. "
        "Returns association scores, genetic evidence counts, and clinical precedent "
        "for the top targets associated with a given disease."
    )

    def run(self, disease_name: str, top_n: int = 20) -> dict[str, Any]:
        # Step 1: resolve disease name to EFO ID
        efo_id = self._resolve_disease(disease_name)
        if not efo_id:
            return {"error": f"Could not resolve disease: {disease_name}"}

        # Step 2: fetch associated targets
        targets = self._fetch_associations(efo_id, top_n)
        return {
            "disease": disease_name,
            "efo_id": efo_id,
            "targets": targets,
        }

    def _resolve_disease(self, disease_name: str) -> Optional[str]:
        query = """
        query SearchDisease($query: String!) {
          search(queryString: $query, entityNames: ["disease"], page: {index: 0, size: 1}) {
            hits {
              id
              name
            }
          }
        }
        """
        resp = requests.post(
            OPENTARGETS_API,
            json={"query": query, "variables": {"query": disease_name}},
            timeout=15,
        )
        resp.raise_for_status()
        hits = resp.json()["data"]["search"]["hits"]
        return hits[0]["id"] if hits else None

    def _fetch_associations(self, efo_id: str, top_n: int) -> list[dict]:
        query = """
        query DiseaseAssociations($efoId: String!, $size: Int!) {
          disease(efoId: $efoId) {
            associatedTargets(page: {index: 0, size: $size}) {
              rows {
                target {
                  id
                  approvedSymbol
                  approvedName
                  biotype
                }
                score
                datatypeScores {
                  id
                  score
                }
              }
            }
          }
        }
        """
        resp = requests.post(
            OPENTARGETS_API,
            json={"query": query, "variables": {"efoId": efo_id, "size": top_n}},
            timeout=15,
        )
        resp.raise_for_status()
        rows = resp.json()["data"]["disease"]["associatedTargets"]["rows"]

        results = []
        for row in rows:
            datatype_scores = {d["id"]: d["score"] for d in row["datatypeScores"]}
            results.append(
                {
                    "ensembl_id": row["target"]["id"],
                    "gene_symbol": row["target"]["approvedSymbol"],
                    "gene_name": row["target"]["approvedName"],
                    "biotype": row["target"]["biotype"],
                    "overall_score": row["score"],
                    "genetic_association_score": datatype_scores.get(
                        "genetic_association", 0
                    ),
                    "known_drug_score": datatype_scores.get("known_drug", 0),
                    "literature_score": datatype_scores.get("literature", 0),
                    "rna_expression_score": datatype_scores.get(
                        "rna_expression", 0
                    ),
                }
            )
        return results

    def to_tool_spec(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "disease_name": {
                            "type": "string",
                            "description": "The disease to query (e.g. 'non-small cell lung cancer')",
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "Number of top targets to return (default 20)",
                        },
                    },
                    "required": ["disease_name"],
                },
            },
        }
