from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..analyzer import ReviewMode
    from ..parsers.diff_parser import DiffHunk


class PromptBuilder:
    @property
    def system_prompt(self) -> str:
        return """You are an expert code reviewer with deep knowledge of software engineering best practices, security, performance optimization, and clean code principles.

Your role is to:
1. Identify bugs, security vulnerabilities, and potential runtime errors
2. Suggest performance improvements
3. Point out code style and maintainability issues
4. Recommend best practices and design patterns
5. Provide constructive, actionable feedback

Guidelines:
- Be specific: reference exact line numbers and variable names
- Be constructive: explain WHY something is an issue
- Be helpful: provide code examples for fixes
- Be balanced: acknowledge good code, not just problems
- Be prioritized: focus on important issues first

Always respond in valid JSON format with the following structure:
{
    "issues": [
        {
            "type": "bug|security|performance|style|maintainability|documentation|best_practice|type_error",
            "severity": "low|medium|high|critical",
            "line": <line_number>,
            "end_line": <optional_end_line>,
            "message": "Clear description of the issue",
            "suggestion": "How to fix it",
            "code_suggestion": "Optional code snippet showing the fix"
        }
    ],
    "positive_feedback": [
        "Things done well in the code"
    ],
    "summary": "Brief overall assessment"
}"""

    def build_review_prompt(
        self,
        code: str,
        language: str,
        context: str | None = None,
        mode: ReviewMode = None,
        rules: dict | None = None,
    ) -> str:
        numbered_code = self._add_line_numbers(code)

        prompt_parts = [
            f"Please review the following {language} code:\n",
            "```" + language,
            numbered_code,
            "```\n",
        ]

        if context:
            prompt_parts.append(f"\nContext: {context}\n")

        if rules:
            prompt_parts.append("\nAdditional rules to check:")
            for rule, enabled in rules.items():
                if enabled:
                    prompt_parts.append(f"- {self._format_rule(rule)}")
            prompt_parts.append("")

        if mode:
            prompt_parts.append(self._get_mode_instructions(mode))

        prompt_parts.append(
            "\nProvide your review in JSON format as specified in the system prompt."
        )

        return "\n".join(prompt_parts)

    def build_diff_review_prompt(
        self,
        file_path: str,
        hunks: list[DiffHunk],
        context: str | None = None,
        mode: ReviewMode = None,
    ) -> str:
        prompt_parts = [
            f"Please review the following changes to `{file_path}`:\n",
        ]

        for i, hunk in enumerate(hunks):
            prompt_parts.append(f"\n### Change {i + 1} (lines {hunk.new_start}-{hunk.new_start + hunk.new_count}):")
            if hunk.header:
                prompt_parts.append(f"Function/Class: {hunk.header}")
            prompt_parts.append("```diff")
            prompt_parts.append(hunk.get_context())
            prompt_parts.append("```")

        if context:
            prompt_parts.append("\n### Full File Context:")
            prompt_parts.append("```")
            prompt_parts.append(context[:2000])
            if len(context) > 2000:
                prompt_parts.append("... (truncated)")
            prompt_parts.append("```")

        prompt_parts.append(
            "\nFocus on the ADDED lines (+ prefix). "
            "Report line numbers from the NEW file version."
        )

        if mode:
            prompt_parts.append(self._get_mode_instructions(mode))

        prompt_parts.append(
            "\nProvide your review in JSON format as specified in the system prompt."
        )

        return "\n".join(prompt_parts)

    def _add_line_numbers(self, code: str) -> str:
        lines = code.split('\n')
        width = len(str(len(lines)))
        numbered = []
        for i, line in enumerate(lines, 1):
            numbered.append(f"{i:>{width}} | {line}")
        return '\n'.join(numbered)

    def _format_rule(self, rule: str) -> str:
        rule_descriptions = {
            "check_types": "Verify type hints are correct and complete",
            "docstring_required": "All public functions must have docstrings",
            "max_complexity": "Flag functions with high cyclomatic complexity",
            "prefer_const": "Prefer const over let for unchanging variables",
            "no_var": "Disallow var, use let/const instead",
            "no_any": "Avoid using 'any' type in TypeScript",
            "error_handling": "Ensure proper error handling",
            "null_safety": "Check for potential null/undefined issues",
        }
        return rule_descriptions.get(rule, rule.replace('_', ' ').title())

    def _get_mode_instructions(self, mode: ReviewMode) -> str:
        from ..analyzer import ReviewMode

        instructions = {
            ReviewMode.QUICK: (
                "\nMode: QUICK REVIEW\n"
                "Focus only on critical bugs and security issues. "
                "Skip minor style suggestions."
            ),
            ReviewMode.STANDARD: (
                "\nMode: STANDARD REVIEW\n"
                "Provide a balanced review covering bugs, security, "
                "performance, and important style issues."
            ),
            ReviewMode.DEEP: (
                "\nMode: DEEP REVIEW\n"
                "Perform a thorough analysis. Include:\n"
                "- All potential bugs and edge cases\n"
                "- Security vulnerabilities\n"
                "- Performance optimizations\n"
                "- Code style and maintainability\n"
                "- Design pattern suggestions\n"
                "- Test coverage recommendations"
            ),
        }
        return instructions.get(mode, "")


SECURITY_REVIEW_PROMPT = """
Focus specifically on security vulnerabilities:
- SQL injection
- XSS (Cross-Site Scripting)
- Command injection
- Path traversal
- Insecure deserialization
- Hardcoded secrets
- Improper authentication/authorization
- Sensitive data exposure
"""

PERFORMANCE_REVIEW_PROMPT = """
Focus specifically on performance issues:
- Algorithm complexity (Big O)
- Memory leaks
- Unnecessary allocations
- N+1 query problems
- Missing caching opportunities
- Blocking operations
- Inefficient data structures
"""

PYTHON_SPECIFIC_PROMPT = """
Python-specific checks:
- Type hint completeness and correctness
- PEP 8 style compliance
- Pythonic idioms (list comprehensions, context managers, etc.)
- Exception handling best practices
- Import organization
- Use of __slots__ for memory optimization
- Generator usage for large datasets
"""

JAVASCRIPT_SPECIFIC_PROMPT = """
JavaScript/TypeScript-specific checks:
- Type safety (TypeScript)
- Async/await error handling
- Memory leaks (event listeners, closures)
- Proper use of const/let
- Null/undefined checks
- Promise handling
- Module import/export patterns
"""
