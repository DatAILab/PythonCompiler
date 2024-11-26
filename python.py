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

st.set_page_config(page_title="Python Playground with Charts", page_icon="📊")

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


def safe_execute_code(code: str) -> Tuple[bool, str, List[plt.Figure]]:
    """
    Safely execute Python code with comprehensive output, error handling, and chart capture
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

    # List to capture matplotlib figures
    captured_figures = []

    try:
        # Create a comprehensive global namespace
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
            },
            'plt': plt,
            'sns': sns,
            'np': np,
            'pd': pd,
        }

        # Special handling for imports
        import_statements = []
        code_without_imports = []
        imported_modules = {}

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
                # Handle different import formats
                if import_stmt.startswith('import '):
                    # Simple import: import numpy as np
                    module_name = import_stmt.split()[1]
                    alias = module_name

                    # Check for 'as' alias
                    if ' as ' in import_stmt:
                        module_name = import_stmt.split()[1]
                        alias = import_stmt.split()[-1]

                    # Ensure module is allowed
                    if any(module_name.startswith(allowed) for allowed in ALLOWED_MODULES):
                        module = importlib.import_module(module_name)
                        exec_globals[alias] = module
                        imported_modules[alias] = module

                elif import_stmt.startswith('from '):
                    # From import: from matplotlib import pyplot as plt
                    parts = import_stmt.split()
                    module_name = parts[1]
                    imported_name = parts[3]
                    alias = parts[-1] if len(parts) > 4 and parts[4] == 'as' else imported_name

                    # Ensure module is allowed
                    if any(module_name.startswith(allowed) for allowed in ALLOWED_MODULES):
                        module = importlib.import_module(module_name)
                        exec_globals[alias] = getattr(module, imported_name)
                        imported_modules[alias] = getattr(module, imported_name)

            except ImportError as e:
                # Log the import error but continue
                print(f"Import warning: {e}")

        # Execute the rest of the code
        exec('\n'.join(code_without_imports), exec_globals)

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
    # Allowed system-level imports and libraries
    allowed_imports = [
        'matplotlib', 'numpy', 'pandas', 'seaborn', 'plotly',
        'scipy', 'sklearn', 'torch', 'tensorflow', 'keras'
    ]

    # Dangerous patterns to block
    unsafe_patterns = [
        r'open\(',  # File operations
        r'exec\(',  # Code execution
        r'eval\(',  # Expression evaluation
    ]

    # Check for unsafe patterns
    for pattern in unsafe_patterns:
        if re.search(pattern, code):
            return False, "Unsafe code pattern detected"

    # Check imported modules
    imports = re.findall(r'^import\s+(\w+)', code, re.MULTILINE)
    from_imports = re.findall(r'^from\s+(\w+)', code, re.MULTILINE)

    disallowed_imports = [
        imp for imp in set(imports + from_imports)
        if imp not in allowed_imports and imp not in ['math', 're', 'random', 'time']
    ]

    if disallowed_imports:
        return False, f"Disallowed imports detected: {', '.join(disallowed_imports)}"

    return True, "Code appears safe"


def main():
    st.markdown('<h1 class="title">Python Playground with Charts</h1>', unsafe_allow_html=True)

    # Code input area with larger height and better styling
    code = st.text_area(
        "Enter your Python code:",
        height=400,
        help="Write your Python code here. Supports plotting with matplotlib and seaborn.",
        value="""# Example: Creating different types of charts
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

# Line Plot
plt.figure(figsize=(10, 4))
x = np.linspace(0, 10, 100)
plt.plot(x, np.sin(x), label='Sin Wave')
plt.plot(x, np.cos(x), label='Cos Wave')
plt.title('Trigonometric Functions')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.legend()

# Scatter Plot
plt.figure(figsize=(10, 4))
np.random.seed(42)
data = pd.DataFrame({
    'x': np.random.randn(100),
    'y': np.random.randn(100),
    'category': np.random.choice(['A', 'B', 'C'], 100)
})
sns.scatterplot(data=data, x='x', y='y', hue='category')
plt.title('Scatter Plot with Categories')

# Bar Plot
plt.figure(figsize=(10, 4))
categories = ['Category A', 'Category B', 'Category C', 'Category D']
values = [23, 45, 56, 78]
plt.bar(categories, values)
plt.title('Bar Chart')
plt.xlabel('Categories')
plt.ylabel('Values')
plt.xticks(rotation=45)

plt.tight_layout()
"""
    )

    # Run Code Button
    if st.button("Run Code"):
        # First, check code safety
        is_safe, safety_message = is_safe_code(code)

        if not is_safe:
            st.error(f"⚠️ {safety_message}")
        else:
            # Execute code
            success, output, figures = safe_execute_code(code)

            # Display output
            st.markdown('<div class="output-container">', unsafe_allow_html=True)
            if success:
                st.success("✅ Code Execution Successful:")

                # Display text output if any
                if output and output != "Code executed successfully with no output.":
                    st.code(output, language='python')

                # Display figures
                for fig in figures:
                    st.pyplot(fig)
                    plt.close(fig)  # Close the figure to prevent memory leaks
            else:
                st.error("❌ Code Execution Failed:")
                st.markdown(f'<pre class="output-error">{output}</pre>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()