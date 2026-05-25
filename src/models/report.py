from pydantic import BaseModel, Field
from typing import Optional


class EvidenceScores(BaseModel):
    opentargets_overall: float = 0.0
    genetic_association: float = 0.0
    known_drug: float = 0.0
    string_hub_score: float = 0.0
    pubmed_recency: float = 0.0
    total_publications: int = 0
    clinical_precedent: str = ""
    subcellular_locations: list[str] = Field(default_factory=list)
    is_membrane_protein: bool = False
    is_kinase: bool = False
    recent_publications: list[dict] = Field(default_factory=list)


class RankedTarget(BaseModel):
    rank: int
    gene_symbol: str
    gene_name: str = ""
    ensembl_id: str = ""
    composite_score: float
    evidence: EvidenceScores
    reasoning: str = ""
    novelty_flag: bool = False
    druggability: str = "unknown"  # high / medium / low / unknown


class TargetReport(BaseModel):
    query: str
    run_timestamp: str
    num_targets_evaluated: int
    targets: list[RankedTarget]
    agent_trace: list[dict] = Field(default_factory=list)
    scoring_weights: dict = Field(
        default_factory=lambda: {
            "genetic_association": 0.35,
            "clinical_precedent": 0.30,
            "string_hub_score": 0.20,
            "pubmed_recency": 0.15,
        }
    )
