import streamlit as st
import sys
import io
import re
import importlib
import traceback
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

# Enhanced safety configuration
ALLOWED_MODULES = [
    # Standard Library
    'math', 're', 'random', 'time', 'datetime', 'collections',
    'itertools', 'functools', 'statistics',
    'typing', 'operator', 'json', 'csv',

    # Scientific and Data Libraries
    'numpy', 'pandas', 'scipy', 'sklearn',
    'matplotlib', 'matplotlib.pyplot', 'seaborn', 'plotly',
    'torch', 'tensorflow', 'keras',
    'sympy', 'networkx', 'pillow',

    # Other Popular Libraries
    'requests', 'beautifulsoup4', 'nltk',
    'pytz', 'emoji', 'pytest'
]

st.set_page_config(page_title="Interactive Python Console", page_icon="📊", layout="wide")

# Custom CSS (same as previous version)
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
    .console-output {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        max-height: 300px;
        overflow-y: auto;
    }
    .code-input {
        font-family: 'Fira Code', monospace;
        background-color: #f1f3f5;
        border: 1px solid #ced4da;
        border-radius: 5px;
        padding: 10px;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)


def safe_execute_code(code: str, exec_globals: Dict) -> Tuple[bool, str, List[plt.Figure]]:
    """
    Safely execute Python code with comprehensive output, error handling, and chart capture
    """
    # Capture standard output/error
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Redirect output
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout_capture, stderr_capture

    # List to capture matplotlib figures
    captured_figures = []

    try:
        # Separate import statements from other code
        lines = code.split('\n')
        import_statements = [line for line in lines if line.strip().startswith(('import ', 'from '))]
        code_statements = [line for line in lines if not line.strip().startswith(('import ', 'from '))]

        # Handle imports
        for import_line in import_statements:
            try:
                # Check if import is allowed
                module_name = import_line.split()[1] if import_line.startswith('import ') else import_line.split()[1]

                if any(module_name.startswith(allowed) for allowed in ALLOWED_MODULES):
                    # Execute import
                    if ' as ' in import_line:
                        # Handle import with alias
                        parts = import_line.split()
                        alias = parts[-1] if parts[0] == 'import' else parts[3]
                        module = importlib.import_module(module_name)
                        exec_globals[alias] = module
                    elif import_line.startswith('from '):
                        # Handle from import
                        from_parts = import_line.split()
                        module_name = from_parts[1]
                        imported_name = from_parts[3]
                        module = importlib.import_module(module_name)
                        exec_globals[imported_name] = getattr(module, imported_name)
                    else:
                        # Simple import
                        module = importlib.import_module(module_name)
                        exec_globals[module_name] = module
                else:
                    raise ImportError(f"Module {module_name} is not in allowed modules")

            except ImportError as e:
                raise ImportError(f"Import error: {e}")

        # Combine code statements
        full_code = '\n'.join(code_statements)

        # Execute the code
        exec(full_code, exec_globals)

        # Capture matplotlib figures
        captured_figures = plt.get_fignums()
        captured_figures = [plt.figure(num) for num in captured_figures]

        # Capture output
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()
        output = stdout_output + stderr_output

        return True, output.strip() if output.strip() else "Code executed successfully with no output.", captured_figures

    except Exception as e:
        # Capture full traceback
        error_traceback = traceback.format_exc()
        return False, error_traceback, []

    finally:
        # Restore original streams
        sys.stdout, sys.stderr = old_stdout, old_stderr
        stdout_capture.close()
        stderr_capture.close()


def is_safe_code(code: str) -> Tuple[bool, str]:
    """
    Enhanced safety check for code execution
    """
    # Dangerous patterns to block
    unsafe_patterns = [
        r'open\(',  # File operations
        r'exec\(',  # Code execution
        r'eval\(',  # Expression evaluation
        r'import\s+os',  # Blocked OS module
        r'import\s+sys',  # Blocked system module
    ]

    # Check for unsafe patterns
    for pattern in unsafe_patterns:
        if re.search(pattern, code):
            return False, f"Unsafe code pattern detected: {pattern}"

    return True, "Code appears safe"


def main():
    st.markdown('<h1 class="title">Interactive Python Console</h1>', unsafe_allow_html=True)

    # Initialize or retrieve the persistent global namespace
    if 'exec_globals' not in st.session_state:
        st.session_state.exec_globals = {
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
            },
            'plt': plt,
            'sns': sns,
            'np': np,
            'pd': pd,
        }

    # Input container
    with st.form(key='code_input_form'):
        code_input = st.text_area("Enter Python Code", height=200, key="code_input",
                                  placeholder="Type your Python code here...",
                                  help="Write and run Python code. Previous code's variables are preserved.")
        submit_button = st.form_submit_button("Run Code")

    # Execute code if submitted
    if submit_button:
        # Safety check
        is_safe, safety_message = is_safe_code(code_input)

        if not is_safe:
            st.error(f"⚠️ {safety_message}")
        else:
            # Execute code
            success, output, figures = safe_execute_code(code_input, st.session_state.exec_globals)

            # Create a container for results at the top
            results_container = st.empty()

            if success:
                # Display output
                results_container.markdown(f'<div class="console-output">{output}</div>', unsafe_allow_html=True)

                # Display figures
                for fig in figures:
                    st.pyplot(fig)
                    plt.close(fig)
            else:
                # Display error
                results_container.error(output)


if __name__ == "__main__":
    main()