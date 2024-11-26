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
    # Standard Library and Scientific Libraries
    'math', 're', 'random', 'time', 'datetime', 'collections',
    'itertools', 'functools', 'statistics',
    'typing', 'operator', 'json', 'csv',
    'numpy', 'pandas', 'scipy', 'sklearn',
    'matplotlib', 'matplotlib.pyplot', 'seaborn', 'plotly',
    'torch', 'tensorflow', 'keras',
    'sympy', 'networkx', 'pillow',
    'requests', 'beautifulsoup4', 'nltk',
    'pytz', 'emoji', 'pytest'
]

# Set page configuration
st.set_page_config(
    page_title="Python Code Playground",
    page_icon="🐍",
    layout="wide"
)

# Custom CSS for modern, clean design
st.markdown("""
    <style>
    /* Global Styling */
    .stApp {
        background-color: #f0f2f6;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Title Styling */
    .title {
        font-size: 2.5em;
        font-weight: 800;
        text-align: center;
        color: #2c3e50;
        margin-bottom: 20px;
        background: linear-gradient(90deg, #3498db, #2980b9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Code Area Styling */
    .stTextArea textarea {
        font-family: 'Fira Code', monospace;
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #e0e4e8;
    }

    /* Button Styling */
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
        padding: 10px 20px;
    }
    .stButton>button:hover {
        background-color: #2980b9;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Output Container */
    .output-container {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .output-error {
        color: #e74c3c;
        background-color: #fef0f0;
        border-radius: 8px;
        padding: 10px;
    }

    /* Figur Styling */
    .stPlotlyChart {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
        if imp not in ['matplotlib', 'numpy', 'pandas', 'seaborn',
                       'math', 're', 'random', 'time']
    ]

    if disallowed_imports:
        return False, f"Disallowed imports detected: {', '.join(disallowed_imports)}"

    return True, "Code appears safe"


def main():
    # Sidebar for customization and information
    with st.sidebar:
        st.markdown("## 🐍 Python Playground")

        # Theme selector
        theme = st.selectbox("Select Chart Theme", [
            "Default",
            "Pastel",
            "Bright",
            "Dark"
        ])

        # Chart size selector
        chart_size = st.slider("Chart Size", 6, 16, 10, step=2)

        # Example templates
        st.markdown("### Quick Templates")
        template = st.selectbox("Choose a Template", [
            "Basic Line Plot",
            "Scatter Plot",
            "Bar Chart",
            "Histogram",
            "Box Plot"
        ])

        # Information and help
        st.markdown("---")
        st.info("""
        🚀 Tips:
        - Use matplotlib/seaborn for plotting
        - Import numpy, pandas for data
        - Click 'Run Code' to execute
        """)

    # Main content
    st.markdown('<h1 class="title">Python Visualization Playground</h1>', unsafe_allow_html=True)

    # Dynamically set template based on selection
    default_code = {
        "Basic Line Plot": """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
plt.figure(figsize=(10, 6))
plt.plot(x, np.sin(x), label='Sin Wave')
plt.plot(x, np.cos(x), label='Cos Wave')
plt.title('Trigonometric Functions')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.legend()
""",
        "Scatter Plot": """
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

np.random.seed(42)
data = pd.DataFrame({
    'x': np.random.randn(100),
    'y': np.random.randn(100),
    'category': np.random.choice(['A', 'B', 'C'], 100)
})

plt.figure(figsize=(10, 6))
for cat in data['category'].unique():
    subset = data[data['category'] == cat]
    plt.scatter(subset['x'], subset['y'], label=cat, alpha=0.7)
plt.title('Scatter Plot with Categories')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.legend()
""",
        "Bar Chart": """
import matplotlib.pyplot as plt
import numpy as np

categories = ['Category A', 'Category B', 'Category C', 'Category D']
values = [23, 45, 56, 78]

plt.figure(figsize=(10, 6))
plt.bar(categories, values, color='skyblue', edgecolor='navy')
plt.title('Bar Chart of Categories')
plt.xlabel('Categories')
plt.ylabel('Values')
plt.xticks(rotation=45)
""",
        "Histogram": """
import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
data = np.random.normal(0, 1, 1000)

plt.figure(figsize=(10, 6))
plt.hist(data, bins=30, edgecolor='black')
plt.title('Normal Distribution Histogram')
plt.xlabel('Values')
plt.ylabel('Frequency')
""",
        "Box Plot": """
import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
data1 = np.random.normal(0, 1, 100)
data2 = np.random.normal(1, 1.2, 100)
data3 = np.random.normal(-1, 1.5, 100)

plt.figure(figsize=(10, 6))
plt.boxplot([data1, data2, data3], labels=['Group A', 'Group B', 'Group C'])
plt.title('Box Plot of Different Groups')
plt.ylabel('Values')
"""
    }

    # Code input area
    code = st.text_area(
        "Enter your Python code:",
        height=400,
        value=default_code[template],
        help="Write your Python visualization code here"
    )

    # Run Code Button
    if st.button("Run Code", key="run_code"):
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
                col1, col2 = st.columns([1, 1])
                with col1:
                    for fig in figures:
                        st.pyplot(fig)
                        plt.close(fig)  # Close the figure to prevent memory leaks
            else:
                st.error("❌ Code Execution Failed:")
                st.markdown(f'<pre class="output-error">{output}</pre>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()