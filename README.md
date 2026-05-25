# Target Prioritisation Agent

An agentic AI system for computational drug target prioritisation. Given a disease name as input, the agent autonomously queries multiple public biological databases, synthesises evidence across data sources, and returns a ranked target report with explicit reasoning.

Built as a practical demonstration of agentic AI over biological data — tool-calling, multi-source retrieval, structured LLM reasoning, and reproducible output.

---

## What it does

1. Takes a **disease name or gene list** as input
2. Autonomously decides which biological databases to query and in what order
3. Calls tools against **OpenTargets, UniProt, STRING, and PubMed** APIs
4. Synthesises evidence across sources using an LLM reasoning step
5. Outputs a **ranked target report** with scores, evidence summaries, key publications, and reasoning traces

### Example

```bash
python run_agent.py --disease "non-small cell lung cancer" --top-n 10
```

Output: `examples/outputs/nsclc_target_report.json` + `nsclc_target_report.md`

---

## Architecture

```
Input (disease / gene list)
        |
        v
  OrchestratorAgent          ← ReAct loop: Reason → Act → Observe
        |
   _____|______________________________________________________
  |              |                  |                         |
  v              v                  v                         v
OpenTargets   UniProt           STRING                   PubMed
Tool          Tool              Tool                     Tool
(associations) (protein info)  (interaction network)   (recent abstracts)
  |              |                  |                         |
  |______________|__________________|_________________________|
                 |
                 v
        EvidenceSynthesiser       ← LLM step: score, rank, summarise
                 |
                 v
        TargetReport              ← JSON + Markdown output
```

### Agent loop

The orchestrator uses a **ReAct-style loop** (Reason, Act, Observe):
- At each step it reasons about what evidence is missing
- Calls the appropriate tool
- Observes the result and decides the next action
- Terminates when it has sufficient evidence or hits the step limit

Every tool call and reasoning step is logged to the output so you can audit the agent's decision-making.

---

## Data sources

| Source | API | What it provides |
|---|---|---|
| **OpenTargets Platform** | GraphQL | Disease-target associations, genetic evidence, clinical precedent |
| **UniProt** | REST | Subcellular localisation, druggability signals |
| **STRING** | REST | Protein-protein interaction network, hub score |
| **PubMed (via Entrez)** | E-utilities | Recent abstracts, publication momentum |

All APIs are free and open. PubMed optionally accepts an NCBI API key for higher rate limits.

---

## Project structure

```
TITV_agent/
├── run_agent.py                  # CLI entry point
├── requirements.txt
├── .env.example
│
├── src/
│   ├── agent/
│   │   ├── orchestrator.py       # ReAct agent loop
│   │   └── prompts.py            # System prompt
│   │
│   ├── tools/
│   │   ├── base.py               # BaseTool interface
│   │   ├── opentargets.py
│   │   ├── uniprot.py
│   │   ├── string_db.py
│   │   └── pubmed.py
│   │
│   ├── models/
│   │   └── report.py             # Pydantic models: TargetReport, RankedTarget, EvidenceScores
│   │
│   └── utils/
│       ├── formatting.py         # Markdown report renderer
│       └── logging.py            # Step-by-step trace logger
│
└── examples/
    ├── nsclc_example.py          # Worked NSCLC example (runnable)
    └── outputs/
        ├── nsclc_target_report.md
        └── nsclc_target_report.json
```

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/shrutisshikhare/TITV_agent
cd TITV_agent
pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
# Add your Groq API key (free at console.groq.com)
# Optionally add NCBI credentials for higher PubMed rate limits
```

### 3. Run the worked example

```bash
python examples/nsclc_example.py
```

### 4. Run on your own disease

```bash
python run_agent.py --disease "triple negative breast cancer" --top-n 10
```

Or with a gene list:

```bash
python run_agent.py --genes KRAS,TP53,EGFR,MET --disease-context "oncology"
```

---

## Output format

Each run produces two files:

**Markdown** (`target_report.md`) — human-readable report with evidence tables, key publications, and reasoning narrative per target.

**JSON** (`target_report.json`) — machine-readable, structured:
```json
{
  "query": "non-small cell lung cancer",
  "run_timestamp": "2025-05-01T14:32:00Z",
  "targets": [
    {
      "gene_symbol": "EGFR",
      "rank": 1,
      "composite_score": 0.91,
      "evidence": {
        "genetic_association": 0.88,
        "known_drug": 0.95,
        "string_hub_score": 0.74,
        "pubmed_recency": 0.90,
        "total_publications": 847,
        "clinical_precedent": "Approved: osimertinib, erlotinib, gefitinib",
        "subcellular_locations": ["Cell membrane"],
        "is_membrane_protein": true,
        "is_kinase": true,
        "recent_publications": [
          {"pmid": "38291040", "title": "Osimertinib resistance mechanisms...", "year": "2024"}
        ]
      },
      "reasoning": "EGFR ranks first due to...",
      "novelty_flag": false,
      "druggability": "high"
    }
  ],
  "agent_trace": [...]
}
```

---

## Scoring methodology

The composite score is a weighted sum across four evidence dimensions:

| Dimension | Weight | Source |
|---|---|---|
| Genetic association score | 35% | OpenTargets |
| Clinical / chemical precedent | 30% | OpenTargets |
| Network centrality (hub score) | 20% | STRING |
| Literature recency | 15% | PubMed |

**Novelty flag** is set when a target has genetic association > 0.5 but known drug score < 0.2 — surfacing biologically validated but therapeutically underexplored candidates.

**Druggability** is classified as high / medium / low / unknown based on UniProt membrane topology, kinase annotation, and interaction interface evidence.

---

## Design decisions

**Why a ReAct loop and not a fixed pipeline?**
A fixed pipeline queries all four sources for all candidates regardless of relevance. The agent adapts: if OpenTargets returns high-confidence approved targets, it prioritises depth (UniProt druggability, STRING network) over breadth. This mirrors how a computational biologist actually works.

**Why Groq + Llama 3.3 70B?**
The free Groq inference API is fast enough for a 15–20 step agentic loop (~60–90 seconds end-to-end). `llama-3.3-70b-versatile` has reliable tool-use and handles structured JSON output well. The OpenAI-compatible client means swapping in another provider is a two-line change in `orchestrator.py`.

**Why these four sources?**
This covers the three axes that matter for target prioritisation in industry: genetic validation (OpenTargets), protein-level tractability (UniProt), network biology (STRING), and literature recency (PubMed). Adding a new source follows the same `BaseTool` interface.

---

## Extending the agent

```python
# src/tools/your_source.py
from src.tools.base import BaseTool

class YourSourceTool(BaseTool):
    name = "your_source"
    description = "Queries YourSource for X data given a gene symbol"

    def run(self, gene_symbol: str) -> dict:
        # call your API
        return structured_result

    def to_tool_spec(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {"gene_symbol": {"type": "string"}},
                    "required": ["gene_symbol"],
                },
            },
        }

# Register in orchestrator.py
self.tools = [..., YourSourceTool()]
```

---

## Limitations

- OpenTargets coverage thins for less-studied indications
- STRING confidence scores vary by data type — results are filtered to human (taxid: 9606) and scores above 0.4
- PubMed queries use title/abstract only; full-text analysis is out of scope
- Composite scores are LLM-generated and may vary slightly between runs
- No access to proprietary or internal data sources by design

---

## Requirements

```
Python 3.9+

groq (via openai SDK)     # LLM backbone — free at console.groq.com
openai>=1.0.0             # OpenAI-compatible client
requests>=2.31.0
biopython>=1.83           # Entrez/PubMed wrapper
pydantic>=2.0
python-dotenv>=1.0
rich>=13.0                # Terminal output
typer>=0.9                # CLI
```

---

## Author

Shruti Shikhare — [GitHub](https://github.com/shrutisshikhare) | [LinkedIn](https://linkedin.com/in/shruti-shikhare)

Senior Research Data Scientist, Early Oncology R&D, AstraZeneca
