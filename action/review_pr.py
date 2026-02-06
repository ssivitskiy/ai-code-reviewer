from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests


def get_pr_diff() -> str:
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH not set")

    with open(event_path) as f:
        event = json.load(f)

    pr_number = event.get("pull_request", {}).get("number")
    if not pr_number:
        raise RuntimeError("Could not determine PR number")

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff",
    }

    response = requests.get(
        f"https://api.github.com/repos/{repo}/pulls/{pr_number}",
        headers=headers,
    )
    response.raise_for_status()

    return response.text


def post_review_comment(
    file_path: str,
    line: int,
    body: str,
    commit_sha: str,
) -> None:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")

    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    with open(event_path) as f:
        event = json.load(f)

    pr_number = event.get("pull_request", {}).get("number")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    data = {
        "body": body,
        "commit_id": commit_sha,
        "path": file_path,
        "line": line,
        "side": "RIGHT",
    }

    response = requests.post(
        f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments",
        headers=headers,
        json=data,
    )

    if response.status_code != 201:
        print(f"Warning: Failed to post comment: {response.text}")


def post_summary_comment(summary: str) -> None:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")

    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    with open(event_path) as f:
        event = json.load(f)

    pr_number = event.get("pull_request", {}).get("number")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    data = {"body": summary}

    response = requests.post(
        f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
        headers=headers,
        json=data,
    )

    if response.status_code != 201:
        print(f"Warning: Failed to post summary: {response.text}")


def add_labels(labels: list[str]) -> None:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")

    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    with open(event_path) as f:
        event = json.load(f)

    pr_number = event.get("pull_request", {}).get("number")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.post(
        f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels",
        headers=headers,
        json={"labels": labels},
    )

    if response.status_code not in (200, 201):
        print(f"Warning: Failed to add labels: {response.text}")


def format_issue_comment(issue: dict) -> str:
    severity_emoji = {
        "critical": "🚨",
        "high": "🔴",
        "medium": "⚠️",
        "low": "💡",
    }

    type_emoji = {
        "bug": "🐛",
        "security": "🔒",
        "performance": "⚡",
        "style": "🎨",
        "maintainability": "🔧",
        "documentation": "📝",
    }

    emoji = severity_emoji.get(issue["severity"], "📌")
    type_em = type_emoji.get(issue["type"], "")

    comment = f"**{emoji} {type_em} {issue['type'].title()}** ({issue['severity']})\n\n"
    comment += f"{issue['message']}\n"

    if issue.get("suggestion"):
        comment += f"\n💡 **Suggestion:** {issue['suggestion']}\n"

    if issue.get("code_suggestion"):
        comment += f"\n```suggestion\n{issue['code_suggestion']}\n```\n"

    return comment


def format_summary(results: list[dict], include_positive: bool) -> str:
    total_issues = sum(len(r["issues"]) for r in results)
    total_bugs = sum(r["summary"]["bugs"] for r in results)
    total_security = sum(r["summary"]["security_issues"] for r in results)
    avg_score = sum(r["summary"]["quality_score"] for r in results) / len(results) if results else 0

    summary = "## 🔍 AI Code Review Summary\n\n"

    if total_issues == 0:
        summary += "✅ **No issues found!** Great code!\n\n"
    else:
        summary += f"Found **{total_issues}** issues across **{len(results)}** files.\n\n"

    summary += "| Metric | Value |\n"
    summary += "|--------|-------|\n"
    summary += f"| 🐛 Bugs | {total_bugs} |\n"
    summary += f"| 🔒 Security Issues | {total_security} |\n"
    summary += f"| 📊 Quality Score | {avg_score:.1f}/10 |\n"
    summary += f"| 📁 Files Reviewed | {len(results)} |\n\n"

    if results:
        summary += "### Files Reviewed\n\n"
        for r in results:
            file_emoji = "✅" if not r["issues"] else "⚠️"
            summary += f"- {file_emoji} `{r['file_path']}` - {len(r['issues'])} issues (Score: {r['summary']['quality_score']}/10)\n"

    if include_positive:
        all_positive = []
        for r in results:
            all_positive.extend(r.get("positive_feedback", []))

        if all_positive:
            summary += "\n### ✨ Positive Observations\n\n"
            for fb in all_positive[:5]:  # Limit to 5
                summary += f"- {fb}\n"

    summary += "\n---\n*Reviewed by [AI Code Reviewer](https://github.com/techn4r/ai-code-reviewer)*"

    return summary


def main():
    parser = argparse.ArgumentParser(description="AI Code Reviewer GitHub Action")
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default="gpt-4")
    parser.add_argument("--severity", default="medium")
    parser.add_argument("--max-comments", type=int, default=10)
    parser.add_argument("--include-positive", default="true")
    parser.add_argument("--config", default=".ai-review.yml")
    parser.add_argument("--changed-files", default="")

    args = parser.parse_args()

    changed_files = [f for f in args.changed_files.split() if f.strip()]

    if not changed_files:
        print("No files to review.")
        return

    print(f"Reviewing {len(changed_files)} files...")

    from ai_code_reviewer import CodeReviewer
    from ai_code_reviewer.analyzer import ReviewConfig
    from ai_code_reviewer.models import LLMProvider, Severity

    config_path = Path(args.config)
    if config_path.exists():
        config = ReviewConfig.from_file(config_path)
    else:
        config = ReviewConfig()

    config.provider = LLMProvider(args.provider)
    config.model = args.model
    config.severity_threshold = Severity(args.severity)
    config.max_issues = args.max_comments

    reviewer = CodeReviewer(config)

    sha = os.environ.get("GITHUB_SHA", "")

    results = []
    comments_posted = 0

    for file_path in changed_files:
        if not Path(file_path).exists():
            continue

        print(f"Reviewing: {file_path}")

        try:
            result = reviewer.review_file(file_path)
            result_dict = result.to_dict()
            result_dict["file_path"] = file_path
            results.append(result_dict)

            for issue in result.filter_by_severity(config.severity_threshold):
                if comments_posted >= args.max_comments:
                    break

                comment = format_issue_comment(issue.to_dict())
                post_review_comment(file_path, issue.line, comment, sha)
                comments_posted += 1

        except Exception as e:
            print(f"Error reviewing {file_path}: {e}")

    include_positive = args.include_positive.lower() == "true"
    summary = format_summary(results, include_positive)
    post_summary_comment(summary)

    labels = []
    total_issues = sum(len(r["issues"]) for r in results)

    if total_issues == 0:
        labels.append("ai-review:clean")
    elif any(r["summary"]["security_issues"] > 0 for r in results):
        labels.append("ai-review:security")
    elif any(r["summary"]["bugs"] > 0 for r in results):
        labels.append("ai-review:bugs")
    else:
        labels.append("ai-review:suggestions")

    add_labels(labels)

    avg_score = sum(r["summary"]["quality_score"] for r in results) / len(results) if results else 10

    with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
        f.write(f"issues-found={total_issues}\n")
        f.write(f"quality-score={avg_score:.1f}\n")
        f.write(f"review-summary=Reviewed {len(results)} files, found {total_issues} issues\n")

    print(f"\n✅ Review complete! Found {total_issues} issues across {len(results)} files.")
    print(f"📊 Average quality score: {avg_score:.1f}/10")


if __name__ == "__main__":
    main()
