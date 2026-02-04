import streamlit as st
from typing import Optional

st.set_page_config(
    page_title="AI Code Reviewer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .issue-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .severity-critical { background-color: #fee2e2; border-left: 4px solid #dc2626; }
    .severity-high { background-color: #fef3c7; border-left: 4px solid #f59e0b; }
    .severity-medium { background-color: #fef9c3; border-left: 4px solid #eab308; }
    .severity-low { background-color: #dbeafe; border-left: 4px solid #3b82f6; }
    .positive-feedback { background-color: #d1fae5; border-left: 4px solid #10b981; padding: 1rem; border-radius: 0.5rem; }
    .quality-score { font-size: 3rem; font-weight: bold; text-align: center; }
    .score-good { color: #10b981; }
    .score-medium { color: #f59e0b; }
    .score-bad { color: #dc2626; }
</style>
""", unsafe_allow_html=True)


def get_severity_class(severity: str) -> str:
    return f"severity-{severity}"


def get_score_class(score: float) -> str:
    if score >= 7:
        return "score-good"
    elif score >= 4:
        return "score-medium"
    return "score-bad"


def format_issue_card(issue: dict) -> str:
    severity = issue.get("severity", "medium")
    issue_type = issue.get("type", "issue")
    line = issue.get("line", "?")
    message = issue.get("message", "")
    suggestion = issue.get("suggestion", "")
    
    emoji_map = {
        "bug": "🐛",
        "security": "🔒",
        "performance": "⚡",
        "style": "🎨",
        "maintainability": "🔧",
        "documentation": "📝",
        "best_practice": "✨",
        "type_error": "🔤",
    }
    
    emoji = emoji_map.get(issue_type, "📌")
    
    html = f"""
    <div class="issue-card {get_severity_class(severity)}">
        <strong>{emoji} {issue_type.upper()}</strong> 
        <span style="color: #6b7280;">Line {line}</span>
        <br>
        <p>{message}</p>
    """
    
    if suggestion:
        html += f'<p style="color: #059669;">💡 {suggestion}</p>'
    
    html += "</div>"
    return html


def main():
    st.markdown('<h1 class="main-header">🔍 AI Code Reviewer</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align: center; color: #6b7280;">Intelligent code review powered by LLMs</p>',
        unsafe_allow_html=True
    )

    with st.sidebar:
        st.header("⚙️ Configuration")
        
        provider = st.selectbox(
            "LLM Provider",
            ["openai", "anthropic", "local"],
            help="Select the LLM provider to use"
        )
        
        model_options = {
            "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "local": ["llama3", "codellama", "mistral"],
        }
        
        model = st.selectbox(
            "Model",
            model_options.get(provider, ["default"]),
        )
        
        mode = st.selectbox(
            "Review Mode",
            ["quick", "standard", "deep"],
            index=1,
            help="Quick: critical issues only. Standard: balanced. Deep: thorough analysis."
        )
        
        st.divider()
        
        api_key = st.text_input(
            "API Key",
            type="password",
            help="Your API key (or set via environment variable)"
        )
        
        st.divider()
        
        st.markdown("### 📊 Statistics")
        if "reviews_count" not in st.session_state:
            st.session_state.reviews_count = 0
            st.session_state.issues_found = 0
        
        col1, col2 = st.columns(2)
        col1.metric("Reviews", st.session_state.reviews_count)
        col2.metric("Issues Found", st.session_state.issues_found)

    tab1, tab2, tab3 = st.tabs(["📝 Code Review", "📋 Diff Review", "📖 About"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Your Code")
            
            language = st.selectbox(
                "Language",
                ["python", "javascript", "typescript", "java", "go", "rust", "cpp", "c"],
            )
            
            code = st.text_area(
                "Paste your code here",
                height=400,
                placeholder="def calculate_average(numbers):\n    total = 0\n    for n in numbers:\n        total += n\n    return total / len(numbers)",
            )
            
            context = st.text_input(
                "Additional context (optional)",
                placeholder="This function calculates the average of a list of numbers"
            )
            
            review_button = st.button("🔍 Review Code", type="primary", use_container_width=True)
        
        with col2:
            st.subheader("Review Results")
            
            if review_button and code:
                with st.spinner("Analyzing code..."):
                    try:
                        result = {
                            "issues": [
                                {
                                    "type": "bug",
                                    "severity": "high",
                                    "line": 5,
                                    "message": "Potential ZeroDivisionError if 'numbers' is empty",
                                    "suggestion": "Add a check for empty list before division"
                                },
                                {
                                    "type": "performance",
                                    "severity": "low",
                                    "line": 2,
                                    "message": "Manual sum calculation can be simplified",
                                    "suggestion": "Use built-in sum() function"
                                }
                            ],
                            "positive_feedback": [
                                "Clear function name",
                                "Simple and readable logic"
                            ],
                            "summary": {
                                "total_issues": 2,
                                "bugs": 1,
                                "security_issues": 0,
                                "performance_issues": 1,
                                "style_issues": 0,
                                "quality_score": 7.0
                            }
                        }
                        

                        st.session_state.reviews_count += 1
                        st.session_state.issues_found += len(result["issues"])

                        score = result["summary"]["quality_score"]
                        st.markdown(
                            f'<p class="quality-score {get_score_class(score)}">{score}/10</p>',
                            unsafe_allow_html=True
                        )
                        st.caption("Quality Score")

                        if result["issues"]:
                            st.markdown("### Issues Found")
                            for issue in result["issues"]:
                                st.markdown(format_issue_card(issue), unsafe_allow_html=True)
                        else:
                            st.success("✅ No issues found! Great code!")

                        if result["positive_feedback"]:
                            st.markdown("### ✨ Positive Feedback")
                            for fb in result["positive_feedback"]:
                                st.markdown(f"• {fb}")

                        st.markdown("### Summary")
                        cols = st.columns(4)
                        cols[0].metric("🐛 Bugs", result["summary"]["bugs"])
                        cols[1].metric("🔒 Security", result["summary"]["security_issues"])
                        cols[2].metric("⚡ Performance", result["summary"]["performance_issues"])
                        cols[3].metric("🎨 Style", result["summary"]["style_issues"])
                        
                    except Exception as e:
                        st.error(f"Error during review: {str(e)}")
            
            elif review_button:
                st.warning("Please enter some code to review.")
            else:
                st.info("Enter your code and click 'Review Code' to get started.")
    
    with tab2:
        st.subheader("📋 Diff Review")
        st.markdown("Paste your git diff to review changes.")
        
        diff = st.text_area(
            "Git Diff",
            height=300,
            placeholder="""diff --git a/example.py b/example.py
--- a/example.py
+++ b/example.py
@@ -1,5 +1,7 @@
 def calculate_average(numbers):
+    if not numbers:
+        return 0
     total = 0
     for n in numbers:
         total += n
     return total / len(numbers)""",
        )
        
        if st.button("🔍 Review Diff", type="primary"):
            if diff:
                with st.spinner("Analyzing diff..."):
                    st.success("Diff review completed! (Demo)")
                    st.info("In production, this would analyze the actual diff.")
            else:
                st.warning("Please paste a diff to review.")
    
    with tab3:
        st.subheader("📖 About AI Code Reviewer")
        
        st.markdown("""
        **AI Code Reviewer** is an intelligent code review tool powered by Large Language Models.
        
        ### Features
        
        - 🎯 **Smart Analysis** — Understands code context, not just syntax
        - 🐛 **Bug Detection** — Catches potential bugs, security issues, and anti-patterns
        - 💡 **Suggestions** — Provides actionable improvement suggestions
        - 🔄 **Multi-Language** — Supports Python, JavaScript, TypeScript, Go, Rust, Java
        - ⚡ **Fast** — Reviews typical code in seconds
        
        ### How It Works
        
        1. **Parse** — Code is parsed and analyzed for structure
        2. **Analyze** — LLM examines the code for issues
        3. **Report** — Issues are formatted with clear explanations
        
        ### Getting Started
        
        ```bash
        pip install ai-code-reviewer
        
        # CLI usage
        ai-review your_file.py
        
        # Python usage
        from ai_code_reviewer import CodeReviewer
        reviewer = CodeReviewer()
        result = reviewer.review(your_code)
        ```
        
        ### Links
        
        - [GitHub Repository](https://github.com/techn4r/ai-code-reviewer)
        - [Documentation](https://ai-code-reviewer.readthedocs.io)
        - [PyPI Package](https://pypi.org/project/ai-code-reviewer)
        """)

    st.divider()
    st.markdown(
        '<p style="text-align: center; color: #9ca3af;">Made with ❤️ by developers, for developers</p>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
