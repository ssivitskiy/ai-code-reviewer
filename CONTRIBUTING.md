# Contributing to AI Code Reviewer

First off, thank you for considering contributing to AI Code Reviewer! 🎉

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- An API key for OpenAI or Anthropic (for testing)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR-USERNAME/ai-code-reviewer.git
cd ai-code-reviewer
```

3. Add the upstream remote:

```bash
git remote add upstream https://github.com/original-owner/ai-code-reviewer.git
```

## Development Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the package in development mode with all dependencies:

```bash
pip install -e ".[all]"
```

3. Install pre-commit hooks:

```bash
pre-commit install
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your API keys
```

## Making Changes

### Branch Naming

Create a new branch for your changes:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
# or
git checkout -b docs/documentation-update
```

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(analyzer): add support for Rust language
fix(parser): handle edge case in diff parsing
docs(readme): update installation instructions
```

## Submitting a Pull Request

1. Update your branch with the latest upstream changes:

```bash
git fetch upstream
git rebase upstream/main
```

2. Push your changes:

```bash
git push origin feature/your-feature-name
```

3. Open a Pull Request on GitHub

4. Fill out the PR template with:
   - Description of changes
   - Related issues
   - Screenshots (if applicable)
   - Testing done

5. Wait for review and address any feedback

## Style Guidelines

### Python Code Style

We use the following tools to maintain code quality:

- **Ruff** for linting and formatting
- **MyPy** for type checking

Run the linters:

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/ai_code_reviewer
```

### Key Style Points

1. **Type hints**: Use type hints for all function parameters and return values

```python
def review_code(code: str, language: str | None = None) -> ReviewResult:
    ...
```

2. **Docstrings**: Use Google-style docstrings

```python
def analyze(code: str) -> list[Issue]:
    """Analyze code for potential issues.
    
    Args:
        code: The source code to analyze.
        
    Returns:
        A list of Issue objects representing found problems.
        
    Raises:
        ValueError: If code is empty.
    """
```

3. **Imports**: Group imports in this order:
   - Standard library
   - Third-party packages
   - Local modules

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ai_code_reviewer --cov-report=html

# Run specific test file
pytest tests/test_analyzer.py

# Run tests matching a pattern
pytest -k "test_review"
```

### Writing Tests

1. Place tests in the `tests/` directory
2. Use descriptive test names
3. Test both success and failure cases
4. Mock external API calls

Example:

```python
def test_review_detects_division_by_zero():
    """Test that the reviewer catches potential division by zero."""
    reviewer = CodeReviewer()
    code = "def avg(nums): return sum(nums) / len(nums)"
    
    result = reviewer.review(code, language="python")
    
    assert any(
        "division" in issue.message.lower() 
        for issue in result.issues
    )
```

### Test Coverage

We aim for >80% test coverage. Please include tests for:

- New features
- Bug fixes
- Edge cases

## Questions?

Feel free to:
- Open an issue for questions
- Join our Discord community
- Email the maintainers

Thank you for contributing! 🚀
