import json
import typer
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.agent.orchestrator import TargetPrioritisationAgent
from src.utils.formatting import render_markdown_report

app = typer.Typer()


@app.command()
def run(
    disease: str = typer.Option(None, "--disease", "-d", help="Disease name to query"),
    genes: str = typer.Option(None, "--genes", "-g", help="Comma-separated gene list"),
    top_n: int = typer.Option(10, "--top-n", "-n", help="Number of top targets to return"),
    output_dir: str = typer.Option("examples/outputs", "--output-dir", "-o"),
):
    if not disease and not genes:
        typer.echo("Provide --disease or --genes (or both).")
        raise typer.Exit(1)

    gene_list = [g.strip() for g in genes.split(",")] if genes else None
    query_label = disease or "gene_list"

    agent = TargetPrioritisationAgent(top_n=top_n)
    report = agent.run(disease=disease or "provided gene list", gene_list=gene_list)

    # Save outputs
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    slug = query_label.lower().replace(" ", "_")[:40]
    json_path = out / f"{slug}_target_report.json"
    md_path = out / f"{slug}_target_report.md"

    json_path.write_text(report.model_dump_json(indent=2))
    md_path.write_text(render_markdown_report(report))

    typer.echo(f"\nReport saved:")
    typer.echo(f"  JSON: {json_path}")
    typer.echo(f"  Markdown: {md_path}")


if __name__ == "__main__":
    app()
