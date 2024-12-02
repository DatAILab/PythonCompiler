import streamlit as st
import sys
import io
import re
import uuid
from typing import List, Tuple, Dict
import traceback
import importlib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

# Initialize session state for code execution history and variable storage
if 'execution_history' not in st.session_state:
    st.session_state.execution_history = []
if 'execution_state' not in st.session_state:
    st.session_state.execution_state = {}

# Configuration and allowed modules remain the same as your original code
ALLOWED_MODULES = [
    'math', 're', 'random', 'time', 'datetime', 'collections',
    'itertools', 'functools', 'statistics', 'typing', 'operator',
    'json', 'csv', 'numpy', 'pandas', 'scipy', 'sklearn',
    'matplotlib', 'matplotlib.pyplot', 'seaborn', 'plotly',
    'torch', 'tensorflow', 'keras', 'sympy', 'networkx', 'pillow',
    'requests', 'beautifulsoup4', 'nltk', 'pytz', 'emoji', 'pytest'
]

st.set_page_config(page_title="Python Console", page_icon="🐍")

# Custom CSS styling
st.markdown("""
    <style>
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
    }
    .code-cell {
        background-color: #f8f9fa;
        border-left: 3px solid #3498db;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .output-cell {
        background-color: #f1f3f5;
        margin-left: 20px;
        padding: 10px;
        border-radius: 5px;
    }
    .title {
        color: #2c3e50;
        text-align: center;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)


def safe_execute_code(code: str, execution_state: dict) -> Tuple[bool, str, List[plt.Figure]]:
    """
    Safely execute Python code with state persistence
    """
    old_stdin, old_stdout, old_stderr = sys.stdin, sys.stdout, sys.stderr
    stdin_capture = io.StringIO()
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    sys.stdin, sys.stdout, sys.stderr = stdin_capture, stdout_capture, stderr_capture

    captured_figures = []

    try:
        # Create execution environment with existing state
        exec_globals = {
            '__builtins__': __builtins__,
            'plt': plt,
            'sns': sns,
            'np': np,
            'pd': pd,
        }

        # Add existing state
        exec_globals.update(execution_state)

        # Handle imports and code execution
        import_statements = []
        code_without_imports = []

        for line in code.split('\n'):
            if line.strip().startswith(('import ', 'from ')):
                import_statements.append(line)
            else:
                code_without_imports.append(line)

        # Execute imports
        for import_stmt in import_statements:
            exec(import_stmt, exec_globals)

        # Execute main code
        exec('\n'.join(code_without_imports), exec_globals)

        # Update execution state with new variables
        execution_state.update({
            k: v for k, v in exec_globals.items()
            if not k.startswith('__') and k not in ('plt', 'sns', 'np', 'pd')
        })

        # Capture figures
        captured_figures = [plt.figure(num) for num in plt.get_fignums()]

        output = stdout_capture.getvalue()
        return True, output.strip() if output.strip() else "Code executed successfully.", captured_figures

    except Exception as e:
        return False, traceback.format_exc(), []

    finally:
        sys.stdin, sys.stdout, sys.stderr = old_stdin, old_stdout, old_stderr
        stdin_capture.close()
        stdout_capture.close()
        stderr_capture.close()


def is_safe_code(code: str) -> Tuple[bool, str]:
    """
    Check if code is safe to execute
    """
    unsafe_patterns = [r'open\(', r'exec\(', r'eval\(']

    for pattern in unsafe_patterns:
        if re.search(pattern, code):
            return False, "Unsafe code pattern detected"

    imports = re.findall(r'^import\s+(\w+)', code, re.MULTILINE)
    from_imports = re.findall(r'^from\s+(\w+)', code, re.MULTILINE)

    disallowed_imports = [
        imp for imp in set(imports + from_imports)
        if not any(imp.startswith(allowed) for allowed in ALLOWED_MODULES)
    ]

    if disallowed_imports:
        return False, f"Disallowed imports: {', '.join(disallowed_imports)}"

    return True, "Code appears safe"


def main():
    st.markdown('<h1 class="title">Python Console</h1>', unsafe_allow_html=True)

    # Code input area
    new_code = st.text_area("New Code Cell:", height=150)

    # Execute button
    if st.button("Run"):
        if new_code.strip():
            # Check code safety
            is_safe, safety_message = is_safe_code(new_code)

            if not is_safe:
                st.error(f"⚠️ {safety_message}")
            else:
                # Execute code and store in history
                success, output, figures = safe_execute_code(
                    new_code,
                    st.session_state.execution_state
                )

                st.session_state.execution_history.append({
                    'code': new_code,
                    'output': output,
                    'figures': figures,
                    'success': success
                })

    # Display execution history in reverse order
    for cell in reversed(st.session_state.execution_history):
        with st.expander("Code Cell", expanded=True):
            st.code(cell['code'], language='python')
            if cell['success']:
                st.success("Output:")
                if cell['output']:
                    st.code(cell['output'])
                for fig in cell['figures']:
                    st.pyplot(fig)
            else:
                st.error(cell['output'])


if __name__ == "__main__":
    main()