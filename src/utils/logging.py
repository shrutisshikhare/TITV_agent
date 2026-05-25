from rich.console import Console
from rich.panel import Panel

console = Console()


class AgentLogger:
    def start(self, query: str):
        console.print(Panel(f"[bold green]Target Prioritisation Agent[/bold green]\nQuery: [cyan]{query}[/cyan]"))

    def step(self, step: int, response):
        message = response.choices[0].message
        tool_calls = [tc.function.name for tc in (message.tool_calls or [])]
        if tool_calls:
            console.print(f"  [dim]Step {step + 1}:[/dim] [yellow]{', '.join(tool_calls)}[/yellow]")
        else:
            console.print(f"  [dim]Step {step + 1}:[/dim] [green]Reasoning...[/green]")

    def done(self, message: str):
        console.print(f"\n[bold green]{message}[/bold green]")
