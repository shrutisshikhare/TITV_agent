"""
Worked example: NSCLC target prioritisation

Run with:
    python examples/nsclc_example.py

Outputs to examples/outputs/
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.agent.orchestrator import TargetPrioritisationAgent
from src.utils.formatting import render_markdown_report


def main():
    print("Running target prioritisation for: Non-small cell lung cancer")
    print("This will make ~15-20 API calls across OpenTargets, UniProt, STRING, and PubMed.")
    print("Expected runtime: 60-120 seconds.\n")

    agent = TargetPrioritisationAgent(top_n=10)
    report = agent.run(disease="non-small cell lung cancer")

    # Save outputs
    out = Path("examples/outputs")
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "nsclc_target_report.json"
    md_path = out / "nsclc_target_report.md"

    json_path.write_text(report.model_dump_json(indent=2))
    md_path.write_text(render_markdown_report(report))

    print(f"\nDone. {report.num_targets_evaluated} targets ranked.")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")

    if report.targets:
        print(f"\nTop 3 targets:")
        for t in report.targets[:3]:
            print(f"  {t.rank}. {t.gene_symbol} — score: {t.composite_score:.2f} | {t.druggability} druggability")


if __name__ == "__main__":
    main()
