from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Any

from .models.reviewer_model import (
    LLMProvider,
    ReviewResult,
    ReviewSummary,
    Severity,
)
from .parsers.diff_parser import DiffParser
from .prompts.templates import PromptBuilder
from .utils.code_utils import detect_language, extract_code_context


class ReviewMode(Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


@dataclass
class ReviewConfig:
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = "gpt-4"
    temperature: float = 0.1
    severity_threshold: Severity = Severity.LOW
    max_issues: int = 20
    include_positive_feedback: bool = True
    mode: ReviewMode = ReviewMode.STANDARD
    language_rules: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str | Path) -> ReviewConfig:
        import yaml

        path = Path(path)
        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(
            provider=LLMProvider(data.get("model", {}).get("provider", "openai")),
            model=data.get("model", {}).get("name", "gpt-4"),
            temperature=data.get("model", {}).get("temperature", 0.1),
            severity_threshold=Severity(
                data.get("review", {}).get("severity_threshold", "low")
            ),
            max_issues=data.get("review", {}).get("max_comments", 20),
            include_positive_feedback=data.get("review", {}).get("include_positive", True),
            language_rules=data.get("rules", {}),
        )


class CodeReviewer:
    def __init__(
        self,
        config: ReviewConfig | None = None,
        api_key: str | None = None,
    ):
        self.config = config or ReviewConfig()
        self.api_key = api_key or self._get_api_key()
        self.prompt_builder = PromptBuilder()
        self.diff_parser = DiffParser()
        self._client = None

    def _get_api_key(self) -> str:
        env_vars = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.LOCAL: None,
        }

        env_var = env_vars.get(self.config.provider)
        if env_var:
            return os.environ.get(env_var, "")
        return ""

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> Any:
        if self.config.provider == LLMProvider.OPENAI:
            from openai import OpenAI
            return OpenAI(api_key=self.api_key)

        elif self.config.provider == LLMProvider.ANTHROPIC:
            from anthropic import Anthropic
            return Anthropic(api_key=self.api_key)

        elif self.config.provider == LLMProvider.LOCAL:
            from openai import OpenAI
            return OpenAI(
                base_url=os.environ.get("LOCAL_LLM_URL", "http://localhost:11434/v1"),
                api_key="not-needed",
            )

        raise ValueError(f"Unsupported provider: {self.config.provider}")

    def review(
        self,
        code: str,
        language: str | None = None,
        context: str | None = None,
        filename: str | None = None,
    ) -> ReviewResult:
        if language is None:
            language = detect_language(code, filename)

        prompt = self.prompt_builder.build_review_prompt(
            code=code,
            language=language,
            context=context,
            mode=self.config.mode,
            rules=self.config.language_rules.get(language, {}),
        )

        response = self._call_llm(prompt)

        return self._parse_review_response(response, code, language)

    def review_file(self, file_path: str | Path) -> ReviewResult:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        code = path.read_text()
        language = detect_language(code, str(path))

        return self.review(code, language=language, filename=str(path))

    def review_diff(
        self,
        diff: str,
        base_content: dict[str, str] | None = None,
    ) -> list[ReviewResult]:
        parsed = self.diff_parser.parse(diff)
        results = []

        for file_diff in parsed:
            file_context = None
            if base_content and file_diff.file_path in base_content:
                file_context = extract_code_context(
                    base_content[file_diff.file_path],
                    file_diff.hunks,
                )

            prompt = self.prompt_builder.build_diff_review_prompt(
                file_path=file_diff.file_path,
                hunks=file_diff.hunks,
                context=file_context,
                mode=self.config.mode,
            )

            response = self._call_llm(prompt)
            result = self._parse_review_response(
                response,
                file_diff.new_content,
                detect_language("", file_diff.file_path),
            )
            result.file_path = file_diff.file_path
            results.append(result)

        return results

    def review_staged(self, repo_path: str = ".") -> list[ReviewResult]:
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--staged"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Git error: {result.stderr}")

        if not result.stdout.strip():
            return []

        return self.review_diff(result.stdout)

    def _call_llm(self, prompt: str) -> str:
        if self.config.provider == LLMProvider.OPENAI:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.prompt_builder.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.config.temperature,
            )
            return response.choices[0].message.content

        elif self.config.provider == LLMProvider.ANTHROPIC:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=4096,
                system=self.prompt_builder.system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        elif self.config.provider == LLMProvider.LOCAL:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.prompt_builder.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.config.temperature,
            )
            return response.choices[0].message.content

        raise ValueError(f"Unsupported provider: {self.config.provider}")

    def _parse_review_response(
        self,
        response: str,
        code: str,
        language: str,
    ) -> ReviewResult:
        import json
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)

        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return ReviewResult.from_dict(data, code, language)
            except json.JSONDecodeError:
                pass

        try:
            data = json.loads(response)
            return ReviewResult.from_dict(data, code, language)
        except json.JSONDecodeError:
            pass

        return ReviewResult(
            code=code,
            language=language,
            issues=[],
            summary=ReviewSummary(
                total_issues=0,
                quality_score=5.0,
                raw_feedback=response,
            ),
            positive_feedback=[],
        )

    def __repr__(self) -> str:
        return (
            f"CodeReviewer(provider={self.config.provider.value}, "
            f"model={self.config.model})"
        )
