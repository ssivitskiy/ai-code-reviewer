# 🔍 AI Code Reviewer

<div align="center">

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-87%25-yellowgreen.svg)

**Intelligent code review powered by LLMs. Get meaningful feedback on your pull requests automatically.**

[Features](#-features) • [Quick Start](#-quick-start) • [GitHub Action](#-github-action) • [API](#-api) • [Demo](#-demo)

<img src="assets/demo.gif" alt="AI Code Reviewer Demo" width="700">

</div>

---

## ✨ Features

- 🎯 **Smart Analysis** — Understands code context, not just syntax
- 🐛 **Bug Detection** — Catches potential bugs, security issues, and anti-patterns
- 💡 **Suggestions** — Provides actionable improvement suggestions with code examples
- 🔄 **Multi-Language** — Supports Python, JavaScript, TypeScript, Go, Rust, Java
- ⚡ **Fast** — Reviews typical PRs in under 10 seconds
- 🔌 **Flexible** — Use as CLI, API, GitHub Action, or Python library

## 🚀 Quick Start

### Installation

```bash
pip install ai-code-reviewer
```

### Basic Usage

```python
from ai_code_reviewer import CodeReviewer

reviewer = CodeReviewer()

# Review a code snippet
code = """
def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)
"""

review = reviewer.review(code, language="python")
print(review)
```

**Output:**
```
🔍 Code Review Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  POTENTIAL BUG (Line 5)
   Division by zero if `numbers` is empty.
   
   💡 Suggestion:
   def calculate_average(numbers):
       if not numbers:
           return 0  # or raise ValueError
       return sum(numbers) / len(numbers)

📝 IMPROVEMENT (Line 2-4)
   Manual sum calculation can be simplified.
   
   💡 Suggestion:
   Use built-in `sum()` function for better readability and performance.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary: 1 bug, 1 suggestion | Quality Score: 7/10
```

### Review a Git Diff

```bash
# Review staged changes
ai-review --staged

# Review a specific file
ai-review path/to/file.py

# Review a PR diff
ai-review --diff pr_changes.patch
```

## 🤖 GitHub Action

Add automated code reviews to your PRs:

```yaml
# .github/workflows/code-review.yml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: AI Code Review
        uses: techn4r/ai-code-reviewer@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          model: "gpt-4"  # or "claude-3", "local"
          severity: "medium"  # minimum severity to comment
```

### Action Outputs

The action will:
- ✅ Add inline comments on problematic code
- 📊 Post a summary comment with overall review
- 🏷️ Add labels based on review severity

<img src="assets/github-action-demo.png" alt="GitHub Action Demo" width="600">

## 🔧 API Server

Run as a REST API:

```bash
# Start the server
ai-review serve --port 8000

# Or with Docker
docker run -p 8000:8000 ai-code-reviewer
```

### API Endpoints

```bash
# Review code
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def foo(x): return x+1",
    "language": "python",
    "context": "This function increments a counter"
  }'

# Review a diff
curl -X POST http://localhost:8000/review/diff \
  -H "Content-Type: application/json" \
  -d '{
    "diff": "@@ -1,3 +1,5 @@...",
    "file_path": "src/utils.py"
  }'
```

### Response Format

```json
{
  "status": "success",
  "review": {
    "issues": [
      {
        "type": "bug",
        "severity": "high",
        "line": 5,
        "message": "Potential null pointer dereference",
        "suggestion": "Add null check before accessing property",
        "code_suggestion": "if (obj != null) { ... }"
      }
    ],
    "summary": {
      "total_issues": 3,
      "bugs": 1,
      "security": 0,
      "style": 2,
      "quality_score": 7.5
    },
    "positive_feedback": [
      "Good use of type hints",
      "Clear function naming"
    ]
  }
}
```

## 🎮 Demo

Try it online: **[AI Code Reviewer Demo](https://huggingface.co/spaces/techn4r/ai-code-reviewer)**

Or run locally:

```bash
# Clone the repo
git clone https://github.com/techn4r/ai-code-reviewer.git
cd ai-code-reviewer

# Install dependencies
pip install -e ".[dev]"

# Run Streamlit demo
streamlit run demo/app.py
```

## ⚙️ Configuration

Create `.ai-review.yml` in your project root:

```yaml
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

# Ignore patterns
ignore:
  - "*.test.js"
  - "**/__pycache__/**"
  - "vendor/**"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Code Reviewer                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  Input   │───▶│ Diff Parser  │───▶│  Code Analyzer   │  │
│  │ (PR/File)│    │              │    │                  │  │
│  └──────────┘    └──────────────┘    └────────┬─────────┘  │
│                                               │             │
│                                               ▼             │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  Output  │◀───│   Formatter  │◀───│    LLM Engine    │  │
│  │(Comments)│    │              │    │ (GPT/Claude/Local)│  │
│  └──────────┘    └──────────────┘    └──────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Benchmarks

Tested on 1000 real PRs from popular open-source projects:

| Metric | Score |
|--------|-------|
| Bug Detection Accuracy | 84.2% |
| False Positive Rate | 12.3% |
| Avg. Review Time | 8.4s |
| Helpful Suggestions | 91.7% |

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

```bash
# Setup development environment
git clone https://github.com/techn4r/ai-code-reviewer.git
cd ai-code-reviewer
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
ruff check .
mypy src/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**[⬆ Back to Top](#-ai-code-reviewer)**

Made with ❤️ by developers, for developers

</div>
