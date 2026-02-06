from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def __lt__(self, other: Severity) -> bool:
        order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        return order.index(self) < order.index(other)

    @property
    def emoji(self) -> str:
        return {
            Severity.LOW: "💡",
            Severity.MEDIUM: "⚠️",
            Severity.HIGH: "🔴",
            Severity.CRITICAL: "🚨",
        }[self]

    @property
    def color(self) -> str:
        return {
            Severity.LOW: "\033[94m",
            Severity.MEDIUM: "\033[93m",
            Severity.HIGH: "\033[91m",
            Severity.CRITICAL: "\033[95m",
        }[self]


class IssueType(Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"
    BEST_PRACTICE = "best_practice"
    TYPE_ERROR = "type_error"

    @property
    def emoji(self) -> str:
        return {
            IssueType.BUG: "🐛",
            IssueType.SECURITY: "🔒",
            IssueType.PERFORMANCE: "⚡",
            IssueType.STYLE: "🎨",
            IssueType.MAINTAINABILITY: "🔧",
            IssueType.DOCUMENTATION: "📝",
            IssueType.BEST_PRACTICE: "✨",
            IssueType.TYPE_ERROR: "🔤",
        }[self]


class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class Issue:
    type: IssueType
    severity: Severity
    line: int
    message: str
    suggestion: str | None = None
    code_suggestion: str | None = None
    end_line: int | None = None
    column: int | None = None
    rule_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Issue:
        return cls(
            type=IssueType(data.get("type", "bug")),
            severity=Severity(data.get("severity", "medium")),
            line=data.get("line", 1),
            end_line=data.get("end_line"),
            column=data.get("column"),
            message=data.get("message", ""),
            suggestion=data.get("suggestion"),
            code_suggestion=data.get("code_suggestion"),
            rule_id=data.get("rule_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "line": self.line,
            "end_line": self.end_line,
            "column": self.column,
            "message": self.message,
            "suggestion": self.suggestion,
            "code_suggestion": self.code_suggestion,
            "rule_id": self.rule_id,
        }

    def format(self, show_colors: bool = True) -> str:
        reset = "\033[0m" if show_colors else ""
        color = self.severity.color if show_colors else ""

        lines = [
            f"{color}{self.severity.emoji} {self.type.value.upper()} (Line {self.line}){reset}",
            f"   {self.message}",
        ]

        if self.suggestion:
            lines.append(f"\n   💡 Suggestion: {self.suggestion}")

        if self.code_suggestion:
            lines.append(f"\n   ```\n   {self.code_suggestion}\n   ```")

        return "\n".join(lines)


@dataclass
class ReviewSummary:
    total_issues: int
    bugs: int = 0
    security_issues: int = 0
    performance_issues: int = 0
    style_issues: int = 0
    quality_score: float = 0.0
    raw_feedback: str | None = None

    @classmethod
    def from_issues(cls, issues: list[Issue]) -> ReviewSummary:
        type_counts = dict.fromkeys(IssueType, 0)
        for issue in issues:
            type_counts[issue.type] += 1

        weights = {
            Severity.CRITICAL: 3.0,
            Severity.HIGH: 2.0,
            Severity.MEDIUM: 1.0,
            Severity.LOW: 0.5,
        }
        penalty = sum(weights[i.severity] for i in issues)
        quality_score = max(0, min(10, 10 - penalty))

        return cls(
            total_issues=len(issues),
            bugs=type_counts[IssueType.BUG],
            security_issues=type_counts[IssueType.SECURITY],
            performance_issues=type_counts[IssueType.PERFORMANCE],
            style_issues=type_counts[IssueType.STYLE],
            quality_score=round(quality_score, 1),
        )


@dataclass
class ReviewResult:
    code: str
    language: str
    issues: list[Issue]
    summary: ReviewSummary
    positive_feedback: list[str] = field(default_factory=list)
    file_path: str | None = None

    @classmethod
    def from_dict(
            cls,
            data: dict[str, Any],
            code: str,
            language: str,
    ) -> ReviewResult:
        issues = [Issue.from_dict(i) for i in data.get("issues", [])]

        return cls(
            code=code,
            language=language,
            issues=issues,
            summary=ReviewSummary.from_issues(issues),
            positive_feedback=data.get("positive_feedback", []),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "issues": [i.to_dict() for i in self.issues],
            "summary": {
                "total_issues": self.summary.total_issues,
                "bugs": self.summary.bugs,
                "security_issues": self.summary.security_issues,
                "performance_issues": self.summary.performance_issues,
                "style_issues": self.summary.style_issues,
                "quality_score": self.summary.quality_score,
            },
            "positive_feedback": self.positive_feedback,
            "file_path": self.file_path,
        }

    def filter_by_severity(self, min_severity: Severity) -> list[Issue]:
        return [i for i in self.issues if not (i.severity < min_severity)]

    def filter_by_type(self, issue_type: IssueType) -> list[Issue]:
        return [i for i in self.issues if i.type == issue_type]

    def __str__(self) -> str:
        lines = [
            "🔍 Code Review Results",
            "━" * 50,
            "",
        ]

        if self.file_path:
            lines.append(f"📁 File: {self.file_path}")
            lines.append("")

        if not self.issues:
            lines.append("✅ No issues found! Great code!")
        else:
            for issue in self.issues:
                lines.append(issue.format())
                lines.append("")

        if self.positive_feedback:
            lines.append("✨ Positive Feedback:")
            for fb in self.positive_feedback:
                lines.append(f"   • {fb}")
            lines.append("")

        lines.append("━" * 50)
        lines.append(
            f"Summary: {self.summary.bugs} bugs, "
            f"{self.summary.security_issues} security, "
            f"{self.summary.style_issues} style | "
            f"Quality Score: {self.summary.quality_score}/10"
        )

        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"ReviewResult(issues={len(self.issues)}, "
            f"score={self.summary.quality_score})"
        )
