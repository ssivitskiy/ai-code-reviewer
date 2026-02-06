from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parsers.diff_parser import DiffHunk


LANGUAGE_PATTERNS = {
    "python": [
        r'^\s*def\s+\w+\s*\(',
        r'^\s*class\s+\w+',
        r'^\s*import\s+\w+',
        r'^\s*from\s+\w+\s+import',
        r'if\s+__name__\s*==\s*["\']__main__["\']',
    ],
    "javascript": [
        r'^\s*const\s+\w+\s*=',
        r'^\s*let\s+\w+\s*=',
        r'^\s*function\s+\w+\s*\(',
        r'^\s*export\s+(default\s+)?',
        r'=>\s*{',
        r'require\s*\(["\']',
    ],
    "typescript": [
        r':\s*(string|number|boolean|any)\s*[;=)]',
        r'interface\s+\w+\s*{',
        r'type\s+\w+\s*=',
        r'<\w+>\s*\(',
    ],
    "java": [
        r'^\s*public\s+class\s+\w+',
        r'^\s*private\s+\w+\s+\w+',
        r'^\s*@\w+',
        r'System\.out\.println',
    ],
    "go": [
        r'^\s*package\s+\w+',
        r'^\s*func\s+\w+\s*\(',
        r'^\s*import\s+\(',
        r':=',
    ],
    "rust": [
        r'^\s*fn\s+\w+\s*\(',
        r'^\s*let\s+mut\s+',
        r'^\s*impl\s+',
        r'^\s*use\s+\w+::',
        r'->\s*\w+',
    ],
    "cpp": [
        r'#include\s*<',
        r'^\s*namespace\s+\w+',
        r'std::',
        r'^\s*template\s*<',
    ],
    "c": [
        r'#include\s*<',
        r'^\s*int\s+main\s*\(',
        r'malloc\s*\(',
        r'printf\s*\(',
    ],
    "ruby": [
        r'^\s*def\s+\w+',
        r'^\s*class\s+\w+\s*<',
        r'^\s*require\s+["\']',
        r'\.each\s+do\s*\|',
    ],
    "php": [
        r'<\?php',
        r'^\s*function\s+\w+\s*\(',
        r'\$\w+\s*=',
    ],
    "swift": [
        r'^\s*func\s+\w+\s*\(',
        r'^\s*var\s+\w+:',
        r'^\s*let\s+\w+:',
        r'guard\s+let',
    ],
    "kotlin": [
        r'^\s*fun\s+\w+\s*\(',
        r'^\s*val\s+\w+',
        r'^\s*var\s+\w+',
        r'^\s*data\s+class',
    ],
}

EXTENSION_MAP = {
    '.py': 'python',
    '.pyw': 'python',
    '.js': 'javascript',
    '.mjs': 'javascript',
    '.cjs': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.go': 'go',
    '.rs': 'rust',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.hpp': 'cpp',
    '.c': 'c',
    '.h': 'c',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.kts': 'kotlin',
    '.cs': 'csharp',
    '.scala': 'scala',
    '.sh': 'bash',
    '.bash': 'bash',
    '.zsh': 'bash',
    '.sql': 'sql',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.json': 'json',
    '.xml': 'xml',
    '.html': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.sass': 'sass',
    '.less': 'less',
    '.md': 'markdown',
    '.markdown': 'markdown',
}


def detect_language(code: str, filename: str | None = None) -> str:
    if filename:
        ext = Path(filename).suffix.lower()
        if ext in EXTENSION_MAP:
            return EXTENSION_MAP[ext]

    scores: dict[str, int] = dict.fromkeys(LANGUAGE_PATTERNS, 0)

    for lang, patterns in LANGUAGE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, code, re.MULTILINE):
                scores[lang] += 1

    if max(scores.values()) > 0:
        return max(scores, key=scores.get)

    return "code"


def extract_code_context(
    full_content: str,
    hunks: list[DiffHunk],
    context_lines: int = 10,
) -> str:
    lines = full_content.split('\n')
    relevant_ranges: list[tuple[int, int]] = []

    for hunk in hunks:
        start = max(0, hunk.new_start - context_lines - 1)
        end = min(len(lines), hunk.new_start + hunk.new_count + context_lines)
        relevant_ranges.append((start, end))

    merged = merge_ranges(relevant_ranges)

    context_parts = []
    for start, end in merged:
        context_parts.append(f"... (lines {start + 1}-{end}) ...")
        context_parts.extend(lines[start:end])

    return '\n'.join(context_parts)


def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []

    sorted_ranges = sorted(ranges, key=lambda x: x[0])
    merged = [sorted_ranges[0]]

    for start, end in sorted_ranges[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def count_complexity(code: str, language: str) -> int:
    complexity_keywords = {
        'python': ['if', 'elif', 'for', 'while', 'except', 'and', 'or'],
        'javascript': ['if', 'else if', 'for', 'while', 'catch', '&&', '||', '?'],
        'typescript': ['if', 'else if', 'for', 'while', 'catch', '&&', '||', '?'],
        'java': ['if', 'else if', 'for', 'while', 'catch', '&&', '||', '?', 'case'],
        'go': ['if', 'for', 'case', '&&', '||'],
        'rust': ['if', 'else if', 'for', 'while', 'match', '&&', '||'],
    }

    keywords = complexity_keywords.get(language, complexity_keywords['python'])
    complexity = 1

    for keyword in keywords:
        if keyword.isalpha():
            complexity += len(re.findall(rf'\b{keyword}\b', code))
        else:
            complexity += code.count(keyword)

    return complexity


def find_function_boundaries(code: str, language: str) -> list[dict]:
    patterns = {
        'python': r'^\s*def\s+(\w+)\s*\(',
        'javascript': r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))',
        'typescript': r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))',
        'java': r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(',
        'go': r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(',
        'rust': r'fn\s+(\w+)\s*[<(]',
    }

    pattern = patterns.get(language)
    if not pattern:
        return []

    functions = []
    lines = code.split('\n')

    for i, line in enumerate(lines):
        match = re.search(pattern, line)
        if match:
            name = next((g for g in match.groups() if g), "anonymous")
            functions.append({
                'name': name,
                'start_line': i + 1,
                'end_line': None,
            })

    return functions


def sanitize_code_for_display(code: str, max_length: int = 5000) -> str:
    sanitized = code.replace('\x00', '')

    if len(sanitized) > max_length:
        half = max_length // 2 - 50
        sanitized = (
            sanitized[:half] +
            f"\n\n... ({len(code) - max_length} characters truncated) ...\n\n" +
            sanitized[-half:]
        )

    return sanitized


def get_line_content(code: str, line_number: int) -> str:
    lines = code.split('\n')
    if 1 <= line_number <= len(lines):
        return lines[line_number - 1]
    return ""
