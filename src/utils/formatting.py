from src.models.report import TargetReport, RankedTarget


def render_markdown_report(report: TargetReport) -> str:
    lines = []
    lines.append(f"# Target Prioritisation Report")
    lines.append(f"\n**Query:** {report.query}")
    lines.append(f"**Generated:** {report.run_timestamp}")
    lines.append(f"**Targets evaluated:** {report.num_targets_evaluated}")

    weights = report.scoring_weights
    lines.append(f"\n## Scoring Weights\n")
    for dim, weight in weights.items():
        lines.append(f"- {dim.replace('_', ' ').title()}: {int(weight * 100)}%")

    lines.append(f"\n## Ranked Targets\n")

    for t in report.targets:
        novelty = " [NOVELTY FLAG]" if t.novelty_flag else ""
        lines.append(f"### {t.rank}. {t.gene_symbol}{novelty}")
        lines.append(f"**{t.gene_name}**")
        lines.append(f"\n**Composite Score:** {t.composite_score:.2f} | **Druggability:** {t.druggability}")

        lines.append(f"\n**Evidence Breakdown:**")
        ev = t.evidence
        lines.append(f"| Dimension | Score |")
        lines.append(f"|---|---|")
        lines.append(f"| Genetic association (OT) | {ev.genetic_association:.2f} |")
        lines.append(f"| Clinical precedent (OT) | {ev.known_drug:.2f} |")
        lines.append(f"| Network hub score (STRING) | {ev.string_hub_score:.2f} |")
        lines.append(f"| Literature recency (PubMed) | {ev.pubmed_recency:.2f} |")
        lines.append(f"| Recent publications | {ev.total_publications} |")

        if ev.clinical_precedent:
            lines.append(f"\n**Clinical precedent:** {ev.clinical_precedent}")
        if ev.subcellular_locations:
            lines.append(f"**Localisation:** {', '.join(ev.subcellular_locations)}")

        protein_flags = []
        if ev.is_membrane_protein:
            protein_flags.append("membrane protein")
        if ev.is_kinase:
            protein_flags.append("kinase")
        if protein_flags:
            lines.append(f"**Protein class:** {', '.join(protein_flags)}")

        if ev.recent_publications:
            lines.append(f"\n**Key Publications:**")
            for pub in ev.recent_publications:
                lines.append(
                    f"- [{pub.get('title', '')}]"
                    f"(https://pubmed.ncbi.nlm.nih.gov/{pub.get('pmid', '')}/)"
                    f" ({pub.get('year', '')})"
                )

        lines.append(f"\n**Reasoning:**\n{t.reasoning}")
        lines.append("\n---")

    lines.append(f"\n## Agent Trace ({len(report.agent_trace)} tool calls)\n")
    for step in report.agent_trace:
        lines.append(
            f"- Step {step['step']}: `{step['tool']}` — input: `{step['input']}`"
        )

    return "\n".join(lines)
