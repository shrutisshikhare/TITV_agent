# Target Prioritisation Report

**Query:** non-small cell lung cancer
**Generated:** 2026-05-25T15:03:33.498915Z
**Targets evaluated:** 3

## Scoring Weights

- Genetic Association: 35%
- Clinical Precedent: 30%
- String Hub Score: 20%
- Pubmed Recency: 15%

## Ranked Targets

### 1. EGFR
****

**Composite Score:** 0.89 | **Druggability:** high

**Evidence Breakdown:**
| Dimension | Score |
|---|---|
| Genetic association (OT) | 0.93 |
| Clinical precedent (OT) | 0.00 |
| Network hub score (STRING) | 1.00 |
| Literature recency (PubMed) | 1.00 |
| Recent publications | 26606 |

**Clinical precedent:** Approved: osimertinib, erlotinib, gefitinib
**Localisation:** Cell membrane
**Protein class:** membrane protein, kinase

**Reasoning:**
EGFR ranks first due to its high genetic association score, high string hub score, and high pubmed recency score, indicating strong biological validation and recent research interest.

---
### 2. KRAS [NOVELTY FLAG]
****

**Composite Score:** 0.84 | **Druggability:** medium

**Evidence Breakdown:**
| Dimension | Score |
|---|---|
| Genetic association (OT) | 0.00 |
| Clinical precedent (OT) | 0.00 |
| Network hub score (STRING) | 1.00 |
| Literature recency (PubMed) | 1.00 |
| Recent publications | 7937 |

**Clinical precedent:** None
**Localisation:** Cytoplasm
**Protein class:** kinase

**Reasoning:**
KRAS ranks second due to its high string hub score and high pubmed recency score, indicating its importance in the protein-protein interaction network and recent research interest.

---
### 3. TP53 [NOVELTY FLAG]
****

**Composite Score:** 0.78 | **Druggability:** low

**Evidence Breakdown:**
| Dimension | Score |
|---|---|
| Genetic association (OT) | 0.00 |
| Clinical precedent (OT) | 0.00 |
| Network hub score (STRING) | 1.00 |
| Literature recency (PubMed) | 1.00 |
| Recent publications | 10306 |

**Clinical precedent:** None
**Localisation:** Nucleus

**Reasoning:**
TP53 ranks third due to its high string hub score and high pubmed recency score, indicating its importance in the protein-protein interaction network and recent research interest.

---

## Agent Trace (15 tool calls)

- Step 0: `opentargets_associations` — input: `{'disease_name': 'non-small cell lung cancer', 'top_n': 20}`
- Step 0: `uniprot_protein_info` — input: `{'gene_symbol': 'EGFR'}`
- Step 0: `uniprot_protein_info` — input: `{'gene_symbol': 'KRAS'}`
- Step 0: `uniprot_protein_info` — input: `{'gene_symbol': 'TP53'}`
- Step 0: `uniprot_protein_info` — input: `{'gene_symbol': 'PIK3CA'}`
- Step 0: `uniprot_protein_info` — input: `{'gene_symbol': 'BRAF'}`
- Step 0: `uniprot_protein_info` — input: `{'gene_symbol': 'KEAP1'}`
- Step 1: `string_network` — input: `{'confidence_threshold': 0.4, 'gene_symbol': 'EGFR'}`
- Step 2: `string_network` — input: `{'confidence_threshold': 0.4, 'gene_symbol': 'KRAS'}`
- Step 2: `string_network` — input: `{'confidence_threshold': 0.4, 'gene_symbol': 'TP53'}`
- Step 2: `string_network` — input: `{'confidence_threshold': 0.4, 'gene_symbol': 'PIK3CA'}`
- Step 2: `string_network` — input: `{'confidence_threshold': 0.4, 'gene_symbol': 'BRAF'}`
- Step 2: `pubmed_literature` — input: `{'gene_symbol': 'EGFR', 'max_abstracts': 5}`
- Step 2: `pubmed_literature` — input: `{'gene_symbol': 'KRAS', 'max_abstracts': 5}`
- Step 2: `pubmed_literature` — input: `{'gene_symbol': 'TP53', 'max_abstracts': 5}`