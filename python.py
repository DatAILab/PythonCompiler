import streamlit as st
import sys
import io
import re
import uuid
from typing import List, Tuple, Dict
import traceback

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

# Custom CSS for enhanced styling
st.markdown("""
    <style>
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
    }
    .title {
        color: #2c3e50;
        text-align: center;
        font-weight: 700;
        background: linear-gradient(90deg, #3498db, #2980b9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stTextArea textarea {
        font-family: 'Fira Code', monospace;
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 6px;
        transition: all 0.3s ease;
    }
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
        # Create a new dictionary for global namespace
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
            }
        }

        # Special handling for imports
        import_statements = []
        code_without_imports = []

        # Separate import statements from the rest of the code
        for line in code.split('\n'):
            stripped_line = line.strip()
            if stripped_line.startswith('import ') or stripped_line.startswith('from '):
                import_statements.append(line)
            else:
                code_without_imports.append(line)

        # Execute import statements
        for import_stmt in import_statements:
            try:
                # Check if imported module is in allowed list
                module_name = import_stmt.split()[1] if import_stmt.startswith('import ') else import_stmt.split()[1]

                if module_name in ALLOWED_MODULES or any(
                        module_name.startswith(allowed) for allowed in ALLOWED_MODULES):
                    exec(import_stmt, exec_globals)
                else:
                    raise ImportError(f"Module {module_name} is not allowed")
            except ImportError as e:
                # Log the import error but continue
                print(f"Import warning: {e}")

        # Execute the rest of the code
        exec('\n'.join(code_without_imports), exec_globals)

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