"""
Tests for the diff parser module.
"""

import pytest

from ai_code_reviewer.parsers.diff_parser import (
    DiffHunk,
    DiffLine,
    DiffParser,
    FileDiff,
    LineType,
)


class TestDiffLine:
    """Tests for DiffLine."""

    def test_context_line(self):
        """Test context line creation."""
        line = DiffLine(
            content="unchanged code",
            line_type=LineType.CONTEXT,
            old_line_number=5,
            new_line_number=5,
        )

        assert line.content == "unchanged code"
        assert line.line_type == LineType.CONTEXT
        assert not line.is_changed

    def test_addition_line(self):
        """Test addition line."""
        line = DiffLine(
            content="new code",
            line_type=LineType.ADDITION,
            new_line_number=10,
        )

        assert line.line_type == LineType.ADDITION
        assert line.is_changed

    def test_deletion_line(self):
        """Test deletion line."""
        line = DiffLine(
            content="old code",
            line_type=LineType.DELETION,
            old_line_number=10,
        )

        assert line.line_type == LineType.DELETION
        assert line.is_changed


class TestDiffHunk:
    """Tests for DiffHunk."""

    def test_hunk_creation(self):
        """Test hunk creation."""
        hunk = DiffHunk(
            old_start=10,
            old_count=5,
            new_start=10,
            new_count=7,
        )

        assert hunk.old_start == 10
        assert hunk.old_count == 5
        assert hunk.new_start == 10
        assert hunk.new_count == 7

    def test_hunk_additions(self):
        """Test getting additions from hunk."""
        hunk = DiffHunk(1, 3, 1, 4)
        hunk.lines = [
            DiffLine(" context", LineType.CONTEXT),
            DiffLine("+added", LineType.ADDITION, new_line_number=2),
            DiffLine("+added2", LineType.ADDITION, new_line_number=3),
            DiffLine(" context", LineType.CONTEXT),
        ]

        additions = hunk.additions

        assert len(additions) == 2
        assert all(line.line_type == LineType.ADDITION for line in additions)

    def test_hunk_deletions(self):
        """Test getting deletions from hunk."""
        hunk = DiffHunk(1, 3, 1, 2)
        hunk.lines = [
            DiffLine(" context", LineType.CONTEXT),
            DiffLine("-removed", LineType.DELETION, old_line_number=2),
            DiffLine(" context", LineType.CONTEXT),
        ]

        deletions = hunk.deletions

        assert len(deletions) == 1

    def test_changed_new_lines(self):
        """Test getting changed line numbers."""
        hunk = DiffHunk(1, 2, 1, 4)
        hunk.lines = [
            DiffLine("+line1", LineType.ADDITION, new_line_number=1),
            DiffLine("+line2", LineType.ADDITION, new_line_number=2),
            DiffLine(" ctx", LineType.CONTEXT, new_line_number=3),
            DiffLine("+line4", LineType.ADDITION, new_line_number=4),
        ]

        lines = hunk.changed_new_lines

        assert lines == [1, 2, 4]

    def test_get_context(self):
        """Test getting hunk context as string."""
        hunk = DiffHunk(1, 2, 1, 2)
        hunk.lines = [
            DiffLine("context", LineType.CONTEXT),
            DiffLine("added", LineType.ADDITION),
            DiffLine("removed", LineType.DELETION),
        ]

        context = hunk.get_context()

        assert " context" in context
        assert "+added" in context
        assert "-removed" in context


class TestFileDiff:
    """Tests for FileDiff."""

    def test_file_diff_creation(self):
        """Test file diff creation."""
        file_diff = FileDiff(
            file_path="src/main.py",
            old_path="src/main.py",
        )

        assert file_diff.file_path == "src/main.py"
        assert not file_diff.is_new_file
        assert not file_diff.is_deleted_file

    def test_total_additions(self):
        """Test counting total additions."""
        file_diff = FileDiff("test.py")

        hunk1 = DiffHunk(1, 2, 1, 4)
        hunk1.lines = [
            DiffLine("+a", LineType.ADDITION),
            DiffLine("+b", LineType.ADDITION),
        ]

        hunk2 = DiffHunk(10, 2, 12, 3)
        hunk2.lines = [
            DiffLine("+c", LineType.ADDITION),
        ]

        file_diff.hunks = [hunk1, hunk2]

        assert file_diff.total_additions == 3

    def test_total_deletions(self):
        """Test counting total deletions."""
        file_diff = FileDiff("test.py")

        hunk = DiffHunk(1, 3, 1, 1)
        hunk.lines = [
            DiffLine("-a", LineType.DELETION),
            DiffLine("-b", LineType.DELETION),
        ]

        file_diff.hunks = [hunk]

        assert file_diff.total_deletions == 2


class TestDiffParser:
    """Tests for DiffParser."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return DiffParser()

    @pytest.fixture
    def simple_diff(self):
        """Simple diff for testing."""
        return """diff --git a/example.py b/example.py
index 1234567..abcdefg 100644
--- a/example.py
+++ b/example.py
@@ -1,5 +1,7 @@
 def hello():
-    print("Hello")
+    print("Hello, World!")
+    return True

 def main():
     hello()
"""

    @pytest.fixture
    def multi_file_diff(self):
        """Multi-file diff for testing."""
        return """diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 def foo():
+    # Added comment
     pass
diff --git a/file2.py b/file2.py
--- a/file2.py
+++ b/file2.py
@@ -1,2 +1,3 @@
 def bar():
+    return 42
     pass
"""

    @pytest.fixture
    def new_file_diff(self):
        """New file diff for testing."""
        return """diff --git a/newfile.py b/newfile.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/newfile.py
@@ -0,0 +1,3 @@
+def new_function():
+    pass
+
"""

    def test_parse_simple_diff(self, parser, simple_diff):
        """Test parsing a simple diff."""
        result = parser.parse(simple_diff)

        assert len(result) == 1
        assert result[0].file_path == "example.py"
        assert len(result[0].hunks) == 1

    def test_parse_hunk_header(self, parser, simple_diff):
        """Test parsing hunk header."""
        result = parser.parse(simple_diff)
        hunk = result[0].hunks[0]

        assert hunk.old_start == 1
        assert hunk.old_count == 5
        assert hunk.new_start == 1
        assert hunk.new_count == 7

    def test_parse_additions(self, parser, simple_diff):
        """Test parsing additions."""
        result = parser.parse(simple_diff)
        hunk = result[0].hunks[0]

        additions = hunk.additions

        assert len(additions) == 2
        assert 'print("Hello, World!")' in additions[0].content

    def test_parse_deletions(self, parser, simple_diff):
        """Test parsing deletions."""
        result = parser.parse(simple_diff)
        hunk = result[0].hunks[0]

        deletions = hunk.deletions

        assert len(deletions) == 1
        assert 'print("Hello")' in deletions[0].content

    def test_parse_multi_file(self, parser, multi_file_diff):
        """Test parsing multi-file diff."""
        result = parser.parse(multi_file_diff)

        assert len(result) == 2
        assert result[0].file_path == "file1.py"
        assert result[1].file_path == "file2.py"

    def test_parse_new_file(self, parser, new_file_diff):
        """Test parsing new file diff."""
        result = parser.parse(new_file_diff)

        assert len(result) == 1
        assert result[0].file_path == "newfile.py"
        assert result[0].is_new_file

    def test_parse_empty_diff(self, parser):
        """Test parsing empty diff."""
        result = parser.parse("")

        assert len(result) == 0

    def test_line_numbers(self, parser, simple_diff):
        """Test line numbers are correctly assigned."""
        result = parser.parse(simple_diff)
        hunk = result[0].hunks[0]

        # Check that additions have new line numbers
        for line in hunk.additions:
            assert line.new_line_number is not None

        # Check that deletions have old line numbers
        for line in hunk.deletions:
            assert line.old_line_number is not None

    def test_parse_file(self, parser, tmp_path, simple_diff):
        """Test parsing from a file."""
        diff_file = tmp_path / "test.patch"
        diff_file.write_text(simple_diff)

        result = parser.parse_file(str(diff_file))

        assert len(result) == 1
        assert result[0].file_path == "example.py"
