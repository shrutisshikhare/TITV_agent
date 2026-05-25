import json
import os
from datetime import datetime
from typing import Any, List, Optional

from openai import OpenAI

from src.tools.opentargets import OpenTargetsTool
from src.tools.uniprot import UniProtTool
from src.tools.string_db import StringTool
from src.tools.pubmed import PubMedTool
from src.models.report import TargetReport, RankedTarget, EvidenceScores
from src.agent.prompts import SYSTEM_PROMPT
from src.utils.logging import AgentLogger


class TargetPrioritisationAgent:
    """
    ReAct-style agent that autonomously queries biological databases
    to prioritise drug targets for a given disease.
    """

    def __init__(self, max_steps: int = 20, top_n: int = 10):
        self.client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        )
        self.max_steps = max_steps
        self.top_n = top_n
        self.logger = AgentLogger()

        self.tools = [
            OpenTargetsTool(),
            UniProtTool(),
            StringTool(),
            PubMedTool(),
        ]
        self.tool_map = {t.name: t for t in self.tools}
        self.tool_specs = [t.to_tool_spec() for t in self.tools]

    def run(self, disease: str, gene_list: Optional[List[str]] = None) -> TargetReport:
        self.logger.start(disease)
        messages = self._build_initial_messages(disease, gene_list)
        trace = []

        for step in range(self.max_steps):
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=2048,
                tools=self.tool_specs,
                messages=messages,
            )

            self.logger.step(step, response)

            choice = response.choices[0]
            message = choice.message
            finish_reason = choice.finish_reason

            # Append assistant turn to history
            messages.append(message)

            if finish_reason == "stop":
                self.logger.done("Agent completed reasoning.")
                break

            if finish_reason == "tool_calls" and message.tool_calls:
                tool_results = []
                for tc in message.tool_calls:
                    inputs = json.loads(tc.function.arguments)
                    result = self._call_tool(tc.function.name, inputs)
                    trace.append(
                        {
                            "step": step,
                            "tool": tc.function.name,
                            "input": inputs,
                            "output_summary": str(result)[:300],
                        }
                    )
                    tool_results.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps(result),
                        }
                    )

                messages.extend(tool_results)

        final_text = self._extract_final_text(messages)
        report = self._parse_report(final_text, disease, trace)
        return report

    def _build_initial_messages(
        self, disease: str, gene_list: Optional[List[str]]
    ) -> List[dict]:
        if gene_list:
            user_content = (
                f"Prioritise drug targets for the following context:\n"
                f"Disease: {disease}\n"
                f"Candidate genes: {', '.join(gene_list)}\n\n"
                f"Return the top {self.top_n} ranked targets with composite scores and reasoning."
            )
        else:
            user_content = (
                f"Prioritise drug targets for: {disease}\n\n"
                f"Start by querying OpenTargets to identify the top candidate genes, "
                f"then gather evidence from UniProt, STRING, and PubMed for the top candidates. "
                f"Return the top {self.top_n} ranked targets with composite scores and reasoning.\n\n"
                f"Output your final answer as a JSON object matching this schema:\n"
                f"{{'targets': [{{'rank': int, 'gene_symbol': str, 'composite_score': float, "
                f"'evidence': {{'genetic_association': float, 'known_drug': float, "
                f"'string_hub_score': float, 'pubmed_recency': float, "
                f"'clinical_precedent': str, 'subcellular_locations': [str], "
                f"'is_membrane_protein': bool, 'is_kinase': bool, "
                f"'recent_publications': [{{'pmid': str, 'title': str, 'year': str}}]}}, "
                f"'reasoning': str, 'novelty_flag': bool, 'druggability': str}}]}}"
            )
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _call_tool(self, name: str, inputs: dict) -> dict:
        tool = self.tool_map.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}
        try:
            return tool.run(**inputs)
        except Exception as e:
            return {"error": str(e)}

    def _extract_final_text(self, messages: list) -> str:
        for msg in reversed(messages):
            # OpenAI SDK returns ChatCompletionMessage objects; we also accept dicts
            role = msg.role if hasattr(msg, "role") else msg.get("role")
            if role == "assistant":
                content = msg.content if hasattr(msg, "content") else msg.get("content", "")
                if content:
                    return content
        return ""

    def _parse_report(self, text: str, disease: str, trace: list) -> TargetReport:
        targets = []
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                for t in data.get("targets", []):
                    ev = t.get("evidence", {})
                    evidence = EvidenceScores(
                        opentargets_overall=ev.get("opentargets_overall", 0),
                        genetic_association=ev.get("genetic_association", 0),
                        known_drug=ev.get("known_drug", 0),
                        string_hub_score=ev.get("string_hub_score", 0),
                        pubmed_recency=ev.get("pubmed_recency", 0),
                        total_publications=ev.get("total_publications", 0),
                        clinical_precedent=ev.get("clinical_precedent", ""),
                        subcellular_locations=ev.get("subcellular_locations", []),
                        is_membrane_protein=ev.get("is_membrane_protein", False),
                        is_kinase=ev.get("is_kinase", False),
                        recent_publications=ev.get("recent_publications", []),
                    )
                    targets.append(
                        RankedTarget(
                            rank=t.get("rank", 0),
                            gene_symbol=t.get("gene_symbol", ""),
                            gene_name=t.get("gene_name", ""),
                            composite_score=t.get("composite_score", 0),
                            evidence=evidence,
                            reasoning=t.get("reasoning", ""),
                            novelty_flag=t.get("novelty_flag", False),
                            druggability=t.get("druggability", "unknown"),
                        )
                    )
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        return TargetReport(
            query=disease,
            run_timestamp=datetime.utcnow().isoformat() + "Z",
            num_targets_evaluated=len(targets),
            targets=targets,
            agent_trace=trace,
        )
