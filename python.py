import streamlit as st
import sys
import io
import re
import uuid
from typing import List, Tuple, Dict
import traceback

# Move set_page_config to the top
st.set_page_config(page_title="Python IDE", page_icon="🐍")

# Enhanced Custom CSS for Professional Design
st.markdown("""
    <style>
        /* Global Styling */
        .stApp {
            background-color: #f4f6f9;
            font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
        }

        /* Title Styling */
        .title {
            color: #2c3e50;
            text-align: center;
            font-weight: 700;
            margin-bottom: 20px;
            background: linear-gradient(90deg, #3498db, #2980b9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Code Editor Styling */
        .code-editor {
            font-family: 'Fira Code', 'Courier New', monospace;
            background-color: #ffffff;
            border: 1px solid #e0e4e8;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            white-space: pre-wrap;
            line-height: 1.6;
        }

        /* Syntax Highlighting */
        .python-keyword {
            color: #2980b9;
            font-weight: 600;
        }
        .python-builtin {
            color: #e74c3c;
        }
        .python-string {
            color: #27ae60;
        }
        .python-comment {
            color: #7f8c8d;
            font-style: italic;
        }

        /* Button Styling */
        .stButton>button {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 6px;
            transition: all 0.3s ease;
            font-weight: 600;
        }

        .stButton>button:hover {
            background-color: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        /* Submitted Code Styling */
        .submitted-code {
            margin-bottom: 10px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 6px;
        }

        /* Output Styling */
        .output-container {
            background-color: #f1f3f5;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }

        .output-error {
            color: #e74c3c;
        }
    </style>
""", unsafe_allow_html=True)


def highlight_python(code: str) -> str:
    """
    Highlight Python keywords, builtins, strings, and comments
    """
    # Keywords
    keywords = [
        'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del', 'elif',
        'else', 'except', 'False', 'finally', 'for', 'from', 'global', 'if', 'import',
        'in', 'is', 'lambda', 'None', 'nonlocal', 'not', 'or', 'pass', 'raise',
        'return', 'True', 'try', 'while', 'with', 'yield'
    ]

    # Builtins
    builtins = [
        'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set',
        'tuple', 'enumerate', 'zip', 'map', 'filter', 'sum', 'max', 'min'
    ]

    # Highlighted code
    highlighted = code

    # Highlight comments (before other highlighting to avoid breaking string comments)
    highlighted = re.sub(
        r'(#.*?$)',
        r'<span class="python-comment">\1</span>',
        highlighted,
        flags=re.MULTILINE
    )

    # Highlight strings
    highlighted = re.sub(
        r'(\'\'\'.*?\'\'\'|\"\"\".*?\"\"\"|\'.*?\'|\".*?\")',
        r'<span class="python-string">\1</span>',
        highlighted,
        flags=re.DOTALL
    )

    # Highlight keywords
    for keyword in keywords:
        highlighted = re.sub(
            r'\b' + re.escape(keyword) + r'\b',
            f'<span class="python-keyword">{keyword}</span>',
            highlighted
        )

    # Highlight builtins
    for builtin in builtins:
        highlighted = re.sub(
            r'\b' + re.escape(builtin) + r'\b',
            f'<span class="python-builtin">{builtin}</span>',
            highlighted
        )

    return highlighted


def safe_execute_code(code: str) -> Tuple[bool, str]:
    """
    Safely execute Python code with output and error handling
    """
    # Redirect stdout and stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture

    try:
        # Execute the code
        exec(code)

        # Capture output
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()

        # Combine outputs
        output = stdout_output + stderr_output

        return True, output.strip() if output.strip() else "Code executed successfully with no output."

    except Exception as e:
        # Capture full traceback
        error_traceback = traceback.format_exc()
        return False, error_traceback

    finally:
        # Restore original stdout and stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        stdout_capture.close()
        stderr_capture.close()


def is_safe_code(code: str) -> bool:
    """
    Basic safety check for potentially dangerous operations
    """
    unsafe_patterns = [
        r'import\s+(os|sys|subprocess|shutil)',  # Prevent system-level imports
        r'open\(',  # Prevent file operations
        r'exec\(',  # Prevent code execution
        r'eval\(',  # Prevent expression evaluation
    ]

    for pattern in unsafe_patterns:
        if re.search(pattern, code):
            return False
    return True


# Main Streamlit App
def main():
    # Title
    st.markdown('<h1 class="title">Python IDE & Compiler</h1>', unsafe_allow_html=True)

    # Initialize session state
    if 'submitted_codes' not in st.session_state:
        st.session_state.submitted_codes = []
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())

    # Code input area
    code = st.text_area(
        "Enter your Python code:",
        height=300,
        help="Write your Python code here. Be cautious with external imports and system operations."
    )

    # Display highlighted code
    if code:
        st.markdown(f"""
            <div class="code-editor">
                {highlight_python(code)}
            </div>
        """, unsafe_allow_html=True)

    # Run Code Button
    if st.button("Run Code"):
        if not is_safe_code(code):
            st.error("⚠️ Potentially unsafe code detected. Some operations are restricted.")
        else:
            success, output = safe_execute_code(code)

            # Display output
            st.markdown('<div class="output-container">', unsafe_allow_html=True)
            if success:
                st.success(f"✅ Code Execution Successful:")
                st.code(output)
            else:
                st.error(f"❌ Code Execution Failed:")
                st.markdown(f'<pre class="output-error">{output}</pre>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # Submit Code Button
    if st.button("Submit Code"):
        if not is_safe_code(code):
            st.error("⚠️ Potentially unsafe code detected. Some operations are restricted.")
        else:
            try:
                st.session_state.submitted_codes.append(code)
                st.success("✅ Code submitted successfully!")
            except Exception as e:
                st.error(f"Error submitting code: {str(e)}")

    # Display Submitted Codes
    if st.session_state.submitted_codes:
        st.markdown("### Submitted Codes")
        for idx, submitted_code in enumerate(st.session_state.submitted_codes, 1):
            st.markdown(f"""
                <div class="submitted-code">
                    {idx}. <div class="code-editor">
                        {highlight_python(submitted_code)}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Clear Submitted Codes Button
    if st.button("Clear Submitted Codes"):
        st.session_state.submitted_codes = []
        st.rerun()

    # Footer
    st.markdown('<div class="footer">Python IDE © 2024</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()