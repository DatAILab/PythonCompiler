import streamlit as st
import sys
import io
import re
import uuid
from typing import List, Tuple, Dict
import traceback
import importlib

# Enhanced safety configuration
ALLOWED_MODULES = [
    # Standard Library
    'math', 're', 'random', 'time', 'datetime', 'collections',
    'itertools', 'functools', 'statistics',
    'typing', 'operator', 'json', 'csv',

    # Scientific and Data Libraries
    'numpy', 'pandas', 'scipy', 'sklearn',
    'matplotlib', 'seaborn', 'plotly',
    'torch', 'tensorflow', 'keras',
    'sympy', 'networkx', 'pillow',

    # Other Popular Libraries
    'requests', 'beautifulsoup4', 'nltk',
    'pytz', 'emoji', 'pytest'
]

st.set_page_config(page_title="Python Playground", page_icon="🐍")


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

def safe_execute_code(code: str) -> Tuple[bool, str]:
    """
    Safely execute Python code with comprehensive output and error handling
    """
    # Capture standard input/output/error
    old_stdin = sys.stdin
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    stdin_capture = io.StringIO()
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    sys.stdin = stdin_capture
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture

    try:
        # Enhanced execution context with safe built-ins
        exec_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'range': range,
                'int': int,
                'float': float,
                'str': str,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'sum': sum,
                'max': max,
                'min': min,
                'sorted': sorted,
                # Add other safe built-ins as needed
            }
        }

        # Dynamically import allowed libraries with error handling
        for module_name in ALLOWED_MODULES:
            try:
                module = importlib.import_module(module_name)
                exec_globals[module_name] = module
            except ImportError:
                pass

        # Execute the code
        exec(code, exec_globals)

        # Capture output
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()
        output = stdout_output + stderr_output

        return True, output.strip() if output.strip() else "Code executed successfully with no output."

    except Exception as e:
        # Capture full traceback
        error_traceback = traceback.format_exc()
        return False, error_traceback

    finally:
        # Restore original streams
        sys.stdin = old_stdin
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        stdin_capture.close()
        stdout_capture.close()
        stderr_capture.close()


def is_safe_code(code: str) -> Tuple[bool, str]:
    """
    Enhanced safety check for code execution
    """
    # List of potentially dangerous patterns to block
    unsafe_patterns = [
        r'open\(',  # File operations
        r'exec\(',  # Code execution
        r'eval\(',  # Expression evaluation
        r'os\.',  # OS interactions
        r'subprocess',  # Subprocess execution
        r'__import__',  # Dynamic module importing
        r'sys\.',  # System interactions
    ]

    # Check for unsafe patterns
    for pattern in unsafe_patterns:
        if re.search(pattern, code):
            return False, f"Unsafe code pattern detected: {pattern}"

    return True, "Code appears safe"


def main():
    st.markdown('<h1 class="title">Python Playground</h1>', unsafe_allow_html=True)

    # Code input area with larger height and better styling
    code = st.text_area(
        "Enter your Python code:",
        height=400,
        help="Write your Python code here. Supports most scientific and data libraries."
    )

    # Run Code Button
    if st.button("Run Code"):
        # First, check code safety
        is_safe, safety_message = is_safe_code(code)

        if not is_safe:
            st.error(f"⚠️ {safety_message}")
        else:
            # Execute code
            success, output = safe_execute_code(code)

            # Display output
            st.markdown('<div class="output-container">', unsafe_allow_html=True)
            if success:
                st.success("✅ Code Execution Successful:")
                st.code(output, language='python')
            else:
                st.error("❌ Code Execution Failed:")
                st.markdown(f'<pre class="output-error">{output}</pre>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()