from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()


def print_banner():
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                  🔍 AI Code Reviewer                       ║
║           Intelligent code review powered by LLMs          ║
╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")


def format_severity_badge(severity: str) -> str:
    colors = {
        "low": "blue",
        "medium": "yellow",
        "high": "red",
        "critical": "bold red on white",
    }
    return f"[{colors.get(severity, 'white')}]{severity.upper()}[/]"


def print_issue(issue: dict, show_code: bool = True):
    severity = issue.get("severity", "medium")
    issue_type = issue.get("type", "issue")
    line = issue.get("line", "?")
    message = issue.get("message", "")
    suggestion = issue.get("suggestion", "")
    code_suggestion = issue.get("code_suggestion", "")

    console.print(
        f"\n{format_severity_badge(severity)} "
        f"[bold]{issue_type.upper()}[/] "
        f"[dim](Line {line})[/]"
    )

    console.print(f"   {message}")

    if suggestion:
        console.print(f"\n   💡 [italic]{suggestion}[/]")

    if code_suggestion and show_code:
        console.print()
        syntax = Syntax(
            code_suggestion,
            "python",
            theme="monokai",
            line_numbers=False,
            padding=1,
        )
        console.print(Panel(syntax, title="Suggested Fix", border_style="green"))


def print_summary(result: dict):
    summary = result.get("summary", {})

    table = Table(title="📊 Review Summary", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Total Issues", str(summary.get("total_issues", 0)))
    table.add_row("🐛 Bugs", str(summary.get("bugs", 0)))
    table.add_row("🔒 Security", str(summary.get("security_issues", 0)))
    table.add_row("⚡ Performance", str(summary.get("performance_issues", 0)))
    table.add_row("🎨 Style", str(summary.get("style_issues", 0)))

    score = summary.get("quality_score", 0)
    score_color = "green" if score >= 7 else "yellow" if score >= 4 else "red"
    table.add_row("Quality Score", f"[{score_color}]{score}/10[/]")

    console.print()
    console.print(table)

    positive = result.get("positive_feedback", [])
    if positive:
        console.print("\n✨ [bold green]Positive Feedback:[/]")
        for fb in positive:
            console.print(f"   • {fb}")


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--version', '-v', is_flag=True, help='Show version')
def cli(ctx, version):
    if version:
        from ai_code_reviewer import __version__
        console.print(f"AI Code Reviewer v{__version__}")
        return

    if ctx.invoked_subcommand is None:
        print_banner()
        console.print("Run [bold]ai-review --help[/] for usage information.")


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--model', '-m', default='gpt-4', help='Model to use')
@click.option('--provider', '-p', default='openai',
              type=click.Choice(['openai', 'anthropic', 'local']))
@click.option('--mode', default='standard',
              type=click.Choice(['quick', 'standard', 'deep']))
@click.option('--output', '-o', type=click.Choice(['text', 'json']), default='text')
@click.option('--no-color', is_flag=True, help='Disable colored output')
def review(file_path: str, model: str, provider: str, mode: str, output: str, no_color: bool):
    from ai_code_reviewer import CodeReviewer
    from ai_code_reviewer.analyzer import ReviewConfig, ReviewMode
    from ai_code_reviewer.models import LLMProvider

    if no_color:
        console.no_color = True

    print_banner()
    console.print(f"📁 Reviewing: [bold]{file_path}[/]\n")

    with console.status("[bold green]Analyzing code..."):
        config = ReviewConfig(
            provider=LLMProvider(provider),
            model=model,
            mode=ReviewMode(mode),
        )
        reviewer = CodeReviewer(config)

        try:
            result = reviewer.review_file(file_path)
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
            sys.exit(1)

    if output == 'json':
        import json
        console.print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.issues:
            console.print(f"Found [bold]{len(result.issues)}[/] issues:\n")
            console.print("─" * 60)
            for issue in result.issues:
                print_issue(issue.to_dict())
        else:
            console.print("[bold green]✅ No issues found! Great code![/]")

        print_summary(result.to_dict())


@cli.command()
@click.option('--model', '-m', default='gpt-4', help='Model to use')
@click.option('--provider', '-p', default='openai',
              type=click.Choice(['openai', 'anthropic', 'local']))
@click.option('--repo', '-r', default='.', help='Repository path')
def staged(model: str, provider: str, repo: str):
    from ai_code_reviewer import CodeReviewer
    from ai_code_reviewer.analyzer import ReviewConfig
    from ai_code_reviewer.models import LLMProvider

    print_banner()
    console.print("📝 Reviewing staged changes...\n")

    with console.status("[bold green]Analyzing changes..."):
        config = ReviewConfig(
            provider=LLMProvider(provider),
            model=model,
        )
        reviewer = CodeReviewer(config)

        try:
            results = reviewer.review_staged(repo)
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
            sys.exit(1)

    if not results:
        console.print("[yellow]No staged changes to review.[/]")
        return

    total_issues = sum(len(r.issues) for r in results)
    console.print(f"Reviewed [bold]{len(results)}[/] files, found [bold]{total_issues}[/] issues:\n")

    for result in results:
        console.print(f"\n📄 [bold]{result.file_path}[/]")
        console.print("─" * 60)

        if result.issues:
            for issue in result.issues:
                print_issue(issue.to_dict())
        else:
            console.print("[green]   ✅ No issues[/]")


@cli.command()
@click.argument('diff_file', type=click.Path(exists=True))
@click.option('--model', '-m', default='gpt-4', help='Model to use')
@click.option('--provider', '-p', default='openai',
              type=click.Choice(['openai', 'anthropic', 'local']))
def diff(diff_file: str, model: str, provider: str):
    from ai_code_reviewer import CodeReviewer
    from ai_code_reviewer.analyzer import ReviewConfig
    from ai_code_reviewer.models import LLMProvider

    print_banner()
    console.print(f"📋 Reviewing diff: [bold]{diff_file}[/]\n")

    with console.status("[bold green]Analyzing diff..."):
        config = ReviewConfig(
            provider=LLMProvider(provider),
            model=model,
        )
        reviewer = CodeReviewer(config)

        diff_content = Path(diff_file).read_text()

        try:
            results = reviewer.review_diff(diff_content)
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
            sys.exit(1)

    for result in results:
        console.print(f"\n📄 [bold]{result.file_path}[/]")
        console.print("─" * 60)

        if result.issues:
            for issue in result.issues:
                print_issue(issue.to_dict())
            print_summary(result.to_dict())
        else:
            console.print("[green]   ✅ No issues[/]")


@cli.command()
@click.option('--host', '-h', default='0.0.0.0', help='Host to bind')
@click.option('--port', '-p', default=8000, help='Port to bind')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def serve(host: str, port: int, reload: bool):
    import uvicorn

    print_banner()
    console.print(f"🚀 Starting API server on [bold]http://{host}:{port}[/]")
    console.print("   Press Ctrl+C to stop.\n")

    uvicorn.run(
        "ai_code_reviewer.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@cli.command()
def init():
    config_content = """\
# AI Code Reviewer Configuration
# https://github.com/techn4r/ai-code-reviewer

# Model settings
model:
  provider: "openai"  # openai, anthropic, local
  name: "gpt-4"
  temperature: 0.1

# Review settings
review:
  severity_threshold: "low"  # low, medium, high, critical
  max_comments: 20
  include_positive: true

# Language-specific rules
rules:
  python:
    check_types: true
    docstring_required: true
    max_complexity: 10

  javascript:
    prefer_const: true
    no_var: true

  typescript:
    no_any: true
    strict_null_checks: true

# Ignore patterns
ignore:
  - "*.test.js"
  - "*.test.ts"
  - "**/__pycache__/**"
  - "**/node_modules/**"
  - "vendor/**"
  - "dist/**"
  - "build/**"
"""

    config_path = Path(".ai-review.yml")

    if config_path.exists() and not click.confirm("Configuration file already exists. Overwrite?"):
            return

    config_path.write_text(config_content)
    console.print(f"[green]✅ Created configuration file: {config_path}[/]")


def main():
    cli()


if __name__ == "__main__":
    main()
