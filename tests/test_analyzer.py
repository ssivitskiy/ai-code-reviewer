"""
Tests for the AI Code Reviewer analyzer module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from ai_code_reviewer.analyzer import CodeReviewer, ReviewConfig, ReviewMode
from ai_code_reviewer.models import (
    Issue,
    IssueType,
    LLMProvider,
    ReviewResult,
    ReviewSummary,
    Severity,
)


class TestReviewConfig:
    """Tests for ReviewConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ReviewConfig()
        
        assert config.provider == LLMProvider.OPENAI
        assert config.model == "gpt-4"
        assert config.temperature == 0.1
        assert config.severity_threshold == Severity.LOW
        assert config.max_issues == 20
        assert config.include_positive_feedback is True
        assert config.mode == ReviewMode.STANDARD
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = ReviewConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-opus",
            mode=ReviewMode.DEEP,
        )
        
        assert config.provider == LLMProvider.ANTHROPIC
        assert config.model == "claude-3-opus"
        assert config.mode == ReviewMode.DEEP
    
    def test_config_from_file(self, tmp_path):
        """Test loading config from YAML file."""
        config_content = """
model:
  provider: "anthropic"
  name: "claude-3-sonnet"
  temperature: 0.2
review:
  severity_threshold: "high"
  max_comments: 5
  include_positive: false
rules:
  python:
    check_types: true
"""
        config_file = tmp_path / ".ai-review.yml"
        config_file.write_text(config_content)
        
        config = ReviewConfig.from_file(config_file)
        
        assert config.provider == LLMProvider.ANTHROPIC
        assert config.model == "claude-3-sonnet"
        assert config.temperature == 0.2
        assert config.severity_threshold == Severity.HIGH
        assert config.max_issues == 5
        assert config.include_positive_feedback is False


class TestCodeReviewer:
    """Tests for CodeReviewer."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        with patch("openai.OpenAI") as mock:
            client = MagicMock()
            mock.return_value = client
            
            # Mock response
            response = MagicMock()
            response.choices = [MagicMock()]
            response.choices[0].message.content = '''
{
    "issues": [
        {
            "type": "bug",
            "severity": "high",
            "line": 5,
            "message": "Potential division by zero",
            "suggestion": "Add a check for empty list"
        }
    ],
    "positive_feedback": ["Good function naming"]
}
'''
            client.chat.completions.create.return_value = response
            
            yield client
    
    def test_init_default(self):
        """Test default initialization."""
        reviewer = CodeReviewer()
        
        assert reviewer.config.provider == LLMProvider.OPENAI
        assert reviewer.config.model == "gpt-4"
    
    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = ReviewConfig(model="gpt-3.5-turbo")
        reviewer = CodeReviewer(config)
        
        assert reviewer.config.model == "gpt-3.5-turbo"
    
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_api_key_from_env(self):
        """Test API key is read from environment."""
        reviewer = CodeReviewer()
        assert reviewer.api_key == "test-key"
    
    def test_review_basic(self, mock_openai_client):
        """Test basic code review."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            reviewer = CodeReviewer()
            
            code = """
def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)
"""
            
            result = reviewer.review(code, language="python")
            
            assert isinstance(result, ReviewResult)
            assert len(result.issues) == 1
            assert result.issues[0].type == IssueType.BUG
            assert result.issues[0].severity == Severity.HIGH
    
    def test_review_file(self, mock_openai_client, tmp_path):
        """Test reviewing a file."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            # Create a test file
            test_file = tmp_path / "test.py"
            test_file.write_text("def foo(): pass")
            
            reviewer = CodeReviewer()
            result = reviewer.review_file(test_file)
            
            assert isinstance(result, ReviewResult)
    
    def test_review_file_not_found(self):
        """Test error when file not found."""
        reviewer = CodeReviewer()
        
        with pytest.raises(FileNotFoundError):
            reviewer.review_file("/nonexistent/file.py")
    
    def test_repr(self):
        """Test string representation."""
        reviewer = CodeReviewer()
        repr_str = repr(reviewer)
        
        assert "CodeReviewer" in repr_str
        assert "openai" in repr_str
        assert "gpt-4" in repr_str


class TestIssue:
    """Tests for Issue model."""
    
    def test_issue_creation(self):
        """Test creating an Issue."""
        issue = Issue(
            type=IssueType.BUG,
            severity=Severity.HIGH,
            line=10,
            message="Test issue",
            suggestion="Fix it",
        )
        
        assert issue.type == IssueType.BUG
        assert issue.severity == Severity.HIGH
        assert issue.line == 10
        assert issue.message == "Test issue"
    
    def test_issue_from_dict(self):
        """Test creating Issue from dictionary."""
        data = {
            "type": "security",
            "severity": "critical",
            "line": 5,
            "message": "SQL injection vulnerability",
            "suggestion": "Use parameterized queries",
        }
        
        issue = Issue.from_dict(data)
        
        assert issue.type == IssueType.SECURITY
        assert issue.severity == Severity.CRITICAL
    
    def test_issue_to_dict(self):
        """Test converting Issue to dictionary."""
        issue = Issue(
            type=IssueType.PERFORMANCE,
            severity=Severity.MEDIUM,
            line=20,
            message="Inefficient loop",
        )
        
        data = issue.to_dict()
        
        assert data["type"] == "performance"
        assert data["severity"] == "medium"
        assert data["line"] == 20
    
    def test_severity_comparison(self):
        """Test severity comparison."""
        assert Severity.LOW < Severity.MEDIUM
        assert Severity.MEDIUM < Severity.HIGH
        assert Severity.HIGH < Severity.CRITICAL
    
    def test_issue_format(self):
        """Test issue formatting."""
        issue = Issue(
            type=IssueType.BUG,
            severity=Severity.HIGH,
            line=10,
            message="Null pointer",
            suggestion="Add null check",
        )
        
        formatted = issue.format(show_colors=False)
        
        assert "BUG" in formatted
        assert "Line 10" in formatted
        assert "Null pointer" in formatted


class TestReviewResult:
    """Tests for ReviewResult model."""
    
    def test_result_creation(self):
        """Test creating a ReviewResult."""
        issues = [
            Issue(IssueType.BUG, Severity.HIGH, 1, "Bug 1"),
            Issue(IssueType.STYLE, Severity.LOW, 2, "Style 1"),
        ]
        
        result = ReviewResult(
            code="test code",
            language="python",
            issues=issues,
            summary=ReviewSummary.from_issues(issues),
        )
        
        assert len(result.issues) == 2
        assert result.language == "python"
    
    def test_filter_by_severity(self):
        """Test filtering issues by severity."""
        issues = [
            Issue(IssueType.BUG, Severity.LOW, 1, "Low"),
            Issue(IssueType.BUG, Severity.HIGH, 2, "High"),
            Issue(IssueType.BUG, Severity.CRITICAL, 3, "Critical"),
        ]
        
        result = ReviewResult(
            code="",
            language="python",
            issues=issues,
            summary=ReviewSummary.from_issues(issues),
        )
        
        high_and_above = result.filter_by_severity(Severity.HIGH)
        
        assert len(high_and_above) == 2
    
    def test_filter_by_type(self):
        """Test filtering issues by type."""
        issues = [
            Issue(IssueType.BUG, Severity.HIGH, 1, "Bug"),
            Issue(IssueType.SECURITY, Severity.HIGH, 2, "Security"),
            Issue(IssueType.BUG, Severity.LOW, 3, "Bug 2"),
        ]
        
        result = ReviewResult(
            code="",
            language="python",
            issues=issues,
            summary=ReviewSummary.from_issues(issues),
        )
        
        bugs = result.filter_by_type(IssueType.BUG)
        
        assert len(bugs) == 2
    
    def test_str_representation(self):
        """Test string representation of result."""
        result = ReviewResult(
            code="test",
            language="python",
            issues=[],
            summary=ReviewSummary(total_issues=0, quality_score=10),
        )
        
        str_repr = str(result)
        
        assert "Code Review Results" in str_repr
        assert "No issues found" in str_repr


class TestReviewSummary:
    """Tests for ReviewSummary."""
    
    def test_summary_from_issues(self):
        """Test creating summary from issues."""
        issues = [
            Issue(IssueType.BUG, Severity.HIGH, 1, "Bug"),
            Issue(IssueType.BUG, Severity.LOW, 2, "Bug 2"),
            Issue(IssueType.SECURITY, Severity.CRITICAL, 3, "Security"),
            Issue(IssueType.STYLE, Severity.LOW, 4, "Style"),
        ]
        
        summary = ReviewSummary.from_issues(issues)
        
        assert summary.total_issues == 4
        assert summary.bugs == 2
        assert summary.security_issues == 1
        assert summary.style_issues == 1
        assert summary.quality_score <= 10
        assert summary.quality_score >= 0
