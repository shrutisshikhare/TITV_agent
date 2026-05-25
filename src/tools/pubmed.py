import os
import time
from typing import Any
from Bio import Entrez
from src.tools.base import BaseTool


class PubMedTool(BaseTool):
    name = "pubmed_literature"
    description = (
        "Queries PubMed for recent publications on a gene and disease context. "
        "Returns publication count, recent abstracts, and a recency score. "
        "Useful for assessing scientific momentum and emerging mechanistic evidence."
    )

    def __init__(self):
        Entrez.email = os.getenv("NCBI_EMAIL", "target.agent@example.com")
        Entrez.api_key = os.getenv("NCBI_API_KEY")  # Optional but increases rate limit

    def run(
        self,
        gene_symbol: str,
        disease_context: str = "",
        max_abstracts: int = 3,
        years_back: int = 3,
    ) -> dict[str, Any]:
        query = self._build_query(gene_symbol, disease_context, years_back)
        total_count, pmids = self._search(query)
        abstracts = self._fetch_abstracts(pmids[:max_abstracts])
        recency_score = self._compute_recency_score(total_count, years_back)

        return {
            "gene_symbol": gene_symbol,
            "query": query,
            "total_publications": total_count,
            "recency_score": recency_score,
            "recent_abstracts": abstracts,
        }

    def _build_query(
        self, gene_symbol: str, disease_context: str, years_back: int
    ) -> str:
        from datetime import datetime

        current_year = datetime.now().year
        start_year = current_year - years_back
        date_filter = f'("{start_year}"[PDAT] : "3000"[PDAT])'

        if disease_context:
            return f'("{gene_symbol}"[TIAB] AND "{disease_context}"[TIAB]) AND {date_filter}'
        return f'"{gene_symbol}"[TIAB] AND {date_filter}'

    def _search(self, query: str) -> tuple[int, list[str]]:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=20)
        record = Entrez.read(handle)
        handle.close()
        time.sleep(0.34)  # Respect rate limit (3 req/s without API key)
        return int(record["Count"]), record["IdList"]

    def _fetch_abstracts(self, pmids: list[str]) -> list[dict]:
        if not pmids:
            return []
        handle = Entrez.efetch(
            db="pubmed", id=",".join(pmids), rettype="abstract", retmode="xml"
        )
        records = Entrez.read(handle)
        handle.close()
        time.sleep(0.34)

        abstracts = []
        for article in records.get("PubmedArticle", []):
            try:
                medline = article["MedlineCitation"]
                art = medline["Article"]
                title = str(art.get("ArticleTitle", ""))
                abstract_texts = art.get("Abstract", {}).get("AbstractText", [])
                abstract = (
                    " ".join(str(t) for t in abstract_texts)
                    if isinstance(abstract_texts, list)
                    else str(abstract_texts)
                )
                pmid = str(medline["PMID"])
                year = str(
                    art.get("Journal", {})
                    .get("JournalIssue", {})
                    .get("PubDate", {})
                    .get("Year", "")
                )
                abstracts.append(
                    {
                        "pmid": pmid,
                        "title": title,
                        "abstract": abstract[:500] + "..." if len(abstract) > 500 else abstract,
                        "year": year,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    }
                )
            except (KeyError, TypeError):
                continue
        return abstracts

    def _compute_recency_score(self, total_count: int, years_back: int) -> float:
        """
        Normalised recency score based on publication volume in the time window.
        Saturates at 500+ publications (returns 1.0).
        """
        return min(total_count / 500, 1.0)

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
                            "description": "Gene symbol to search for",
                        },
                        "disease_context": {
                            "type": "string",
                            "description": "Optional disease to narrow the search (e.g. 'lung cancer')",
                        },
                        "max_abstracts": {
                            "type": "integer",
                            "description": "Number of recent abstracts to return (default 3)",
                        },
                    },
                    "required": ["gene_symbol"],
                },
            },
        }
