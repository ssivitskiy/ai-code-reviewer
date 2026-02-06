def example_basic_review():
    from ai_code_reviewer import CodeReviewer

    reviewer = CodeReviewer()

    code = '''
def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)
'''

    result = reviewer.review(code, language="python")

    print(result)

    for issue in result.issues:
        print(f"Line {issue.line}: [{issue.severity.value}] {issue.message}")


def example_custom_config():
    from ai_code_reviewer import CodeReviewer
    from ai_code_reviewer.analyzer import ReviewConfig, ReviewMode
    from ai_code_reviewer.models import LLMProvider, Severity

    config = ReviewConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4-turbo",
        mode=ReviewMode.DEEP,
        severity_threshold=Severity.MEDIUM,
        include_positive_feedback=True,
    )

    reviewer = CodeReviewer(config)

    code = '''
import sqlite3

def get_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # SQL Injection vulnerability!
    cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
    return cursor.fetchone()
'''

    result = reviewer.review(code, language="python")

    high_issues = result.filter_by_severity(Severity.HIGH)
    print(f"Found {len(high_issues)} high-severity issues")

def example_review_file():
    from ai_code_reviewer import CodeReviewer

    reviewer = CodeReviewer()

    result = reviewer.review_file("path/to/your/file.py")

    print(f"Quality Score: {result.summary.quality_score}/10")
    print(f"Total Issues: {result.summary.total_issues}")
    print(f"Bugs: {result.summary.bugs}")
    print(f"Security Issues: {result.summary.security_issues}")

def example_review_diff():
    from ai_code_reviewer import CodeReviewer

    reviewer = CodeReviewer()

    diff = '''
diff --git a/utils.py b/utils.py
--- a/utils.py
+++ b/utils.py
@@ -10,6 +10,12 @@ def process_data(data):
     return result

+def unsafe_eval(user_input):
+    # This is dangerous!
+    return eval(user_input)
+
 def validate(value):
     if value:
         return True
'''

    results = reviewer.review_diff(diff)

    for file_result in results:
        print(f"\n📁 {file_result.file_path}")
        for issue in file_result.issues:
            print(f"  - Line {issue.line}: {issue.message}")


def example_review_staged():
    from ai_code_reviewer import CodeReviewer

    reviewer = CodeReviewer()

    results = reviewer.review_staged()

    if not results:
        print("No staged changes to review.")
        return

    total_issues = sum(len(r.issues) for r in results)

    if total_issues == 0:
        print("✅ All changes look good! Safe to commit.")
    else:
        print(f"⚠️ Found {total_issues} issues. Consider fixing before commit.")
        for result in results:
            if result.issues:
                print(f"\n{result.file_path}:")
                for issue in result.issues:
                    print(f"  [{issue.severity.value}] {issue.message}")


def example_anthropic():
    from ai_code_reviewer import CodeReviewer
    from ai_code_reviewer.analyzer import ReviewConfig
    from ai_code_reviewer.models import LLMProvider

    config = ReviewConfig(
        provider=LLMProvider.ANTHROPIC,
        model="claude-3-opus-20240229",
    )

    reviewer = CodeReviewer(config)

    result = reviewer.review(
        "def foo(x): return x + 1",
        language="python",
    )
    print(result)


def example_local_llm():
    import os

    from ai_code_reviewer import CodeReviewer
    from ai_code_reviewer.analyzer import ReviewConfig
    from ai_code_reviewer.models import LLMProvider

    os.environ["LOCAL_LLM_URL"] = "http://localhost:11434/v1"

    config = ReviewConfig(
        provider=LLMProvider.LOCAL,
        model="codellama",
    )

    reviewer = CodeReviewer(config)

    result = reviewer.review(
        "function add(a, b) { return a + b; }",
        language="javascript",
    )
    print(result)


def example_api_integration():
    import requests

    API_URL = "http://localhost:8000"

    response = requests.post(
        f"{API_URL}/review",
        json={
            "code": "def foo(): pass",
            "language": "python",
            "mode": "standard",
        }
    )

    if response.ok:
        result = response.json()
        print(f"Quality Score: {result['summary']['quality_score']}")
        for issue in result['issues']:
            print(f"- {issue['message']}")
    else:
        print(f"Error: {response.text}")

def example_batch_review():
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path

    from ai_code_reviewer import CodeReviewer

    reviewer = CodeReviewer()

    files = list(Path("src").rglob("*.py"))

    def review_file(file_path):
        try:
            return str(file_path), reviewer.review_file(file_path)
        except Exception:
            return str(file_path), None

    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        for path, result in executor.map(review_file, files):
            results[path] = result

    total_files = len(results)
    total_issues = sum(
        len(r.issues) for r in results.values() if r
    )

    print(f"Reviewed {total_files} files")
    print(f"Total issues found: {total_issues}")

if __name__ == "__main__":
    print("=" * 60)
    print("AI Code Reviewer - Examples")
    print("=" * 60)

    print("\n📝 Example 1: Basic Review")
    print("-" * 40)

    print("\nSee the source code for more examples!")
