from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class LineType(Enum):
    CONTEXT = "context"
    ADDITION = "addition"
    DELETION = "deletion"


@dataclass
class DiffLine:
    content: str
    line_type: LineType
    old_line_number: Optional[int] = None
    new_line_number: Optional[int] = None
    
    @property
    def is_changed(self) -> bool:
        return self.line_type in (LineType.ADDITION, LineType.DELETION)


@dataclass
class DiffHunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[DiffLine] = field(default_factory=list)
    header: str = ""
    
    @property
    def additions(self) -> list[DiffLine]:
        return [l for l in self.lines if l.line_type == LineType.ADDITION]
    
    @property
    def deletions(self) -> list[DiffLine]:
        return [l for l in self.lines if l.line_type == LineType.DELETION]
    
    @property
    def changed_new_lines(self) -> list[int]:
        return [l.new_line_number for l in self.additions if l.new_line_number]
    
    def get_context(self, lines: int = 3) -> str:
        result = []
        for line in self.lines:
            prefix = {
                LineType.CONTEXT: " ",
                LineType.ADDITION: "+",
                LineType.DELETION: "-",
            }[line.line_type]
            result.append(f"{prefix}{line.content}")
        return "\n".join(result)


@dataclass
class FileDiff:
    file_path: str
    old_path: Optional[str] = None
    hunks: list[DiffHunk] = field(default_factory=list)
    is_new_file: bool = False
    is_deleted_file: bool = False
    is_renamed: bool = False
    
    @property
    def old_content(self) -> str:
        lines = []
        for hunk in self.hunks:
            for line in hunk.lines:
                if line.line_type != LineType.ADDITION:
                    lines.append(line.content)
        return "\n".join(lines)
    
    @property
    def new_content(self) -> str:
        lines = []
        for hunk in self.hunks:
            for line in hunk.lines:
                if line.line_type != LineType.DELETION:
                    lines.append(line.content)
        return "\n".join(lines)
    
    @property
    def total_additions(self) -> int:
        return sum(len(h.additions) for h in self.hunks)
    
    @property
    def total_deletions(self) -> int:
        return sum(len(h.deletions) for h in self.hunks)


class DiffParser:
    FILE_HEADER_PATTERN = re.compile(r'^diff --git a/(.*) b/(.*)$')
    OLD_FILE_PATTERN = re.compile(r'^--- (?:a/)?(.*)$')
    NEW_FILE_PATTERN = re.compile(r'^\+\+\+ (?:b/)?(.*)$')
    HUNK_HEADER_PATTERN = re.compile(
        r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$'
    )
    
    def parse(self, diff: str) -> list[FileDiff]:
        lines = diff.split('\n')
        file_diffs: list[FileDiff] = []
        current_file: Optional[FileDiff] = None
        current_hunk: Optional[DiffHunk] = None
        old_line = 0
        new_line = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]

            file_match = self.FILE_HEADER_PATTERN.match(line)
            if file_match:
                if current_file:
                    file_diffs.append(current_file)
                current_file = FileDiff(
                    file_path=file_match.group(2),
                    old_path=file_match.group(1),
                )
                current_hunk = None
                i += 1
                continue

            if line.startswith('new file mode'):
                if current_file:
                    current_file.is_new_file = True
                i += 1
                continue

            if line.startswith('deleted file mode'):
                if current_file:
                    current_file.is_deleted_file = True
                i += 1
                continue

            if line.startswith('rename from') or line.startswith('rename to'):
                if current_file:
                    current_file.is_renamed = True
                i += 1
                continue

            old_match = self.OLD_FILE_PATTERN.match(line)
            if old_match:
                if not current_file:
                    current_file = FileDiff(file_path="")
                i += 1
                continue

            new_match = self.NEW_FILE_PATTERN.match(line)
            if new_match:
                if current_file and not current_file.file_path:
                    path = new_match.group(1)
                    if path != '/dev/null':
                        current_file.file_path = path
                i += 1
                continue

            hunk_match = self.HUNK_HEADER_PATTERN.match(line)
            if hunk_match:
                if current_hunk and current_file:
                    current_file.hunks.append(current_hunk)
                
                old_start = int(hunk_match.group(1))
                old_count = int(hunk_match.group(2) or 1)
                new_start = int(hunk_match.group(3))
                new_count = int(hunk_match.group(4) or 1)
                
                current_hunk = DiffHunk(
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                    header=hunk_match.group(5).strip(),
                )
                old_line = old_start
                new_line = new_start
                i += 1
                continue

            if current_hunk is not None:
                if line.startswith('+') and not line.startswith('+++'):
                    current_hunk.lines.append(DiffLine(
                        content=line[1:],
                        line_type=LineType.ADDITION,
                        new_line_number=new_line,
                    ))
                    new_line += 1
                elif line.startswith('-') and not line.startswith('---'):
                    current_hunk.lines.append(DiffLine(
                        content=line[1:],
                        line_type=LineType.DELETION,
                        old_line_number=old_line,
                    ))
                    old_line += 1
                elif line.startswith(' ') or line == '':
                    content = line[1:] if line.startswith(' ') else line
                    current_hunk.lines.append(DiffLine(
                        content=content,
                        line_type=LineType.CONTEXT,
                        old_line_number=old_line,
                        new_line_number=new_line,
                    ))
                    old_line += 1
                    new_line += 1
            
            i += 1

        if current_hunk and current_file:
            current_file.hunks.append(current_hunk)
        if current_file:
            file_diffs.append(current_file)
        
        return file_diffs
    
    def parse_file(self, file_path: str) -> list[FileDiff]:
        with open(file_path) as f:
            return self.parse(f.read())
