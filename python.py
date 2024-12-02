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
import streamlit.components.v1 as components

# Initialisation de l'état de session pour l'historique d'exécution et le stockage des variables
if 'execution_history' not in st.session_state:
    st.session_state.execution_history = []
if 'execution_state' not in st.session_state:
    st.session_state.execution_state = {}
if 'code_input' not in st.session_state:
    st.session_state.code_input = ""

# Configuration et modules autorisés
ALLOWED_MODULES = [
    'math', 're', 'random', 'time', 'datetime', 'collections',
    'itertools', 'functools', 'statistics', 'typing', 'operator',
    'json', 'csv', 'numpy', 'pandas', 'scipy', 'sklearn',
    'matplotlib', 'matplotlib.pyplot', 'seaborn', 'plotly',
    'torch', 'tensorflow', 'keras', 'sympy', 'networkx', 'pillow',
    'requests', 'beautifulsoup4', 'nltk', 'pytz', 'emoji', 'pytest'
]

st.set_page_config(page_title="Console Python de Data AI Lab", page_icon="🐍")

# Style CSS personnalisé
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


def executer_code_en_securite(code: str, execution_state: dict) -> Tuple[bool, str, List[plt.Figure]]:
    """
    Exécuter du code Python en toute sécurité avec persistance d'état
    """
    old_stdin, old_stdout, old_stderr = sys.stdin, sys.stdout, sys.stderr
    stdin_capture = io.StringIO()
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    sys.stdin, sys.stdout, sys.stderr = stdin_capture, stdout_capture, stderr_capture

    figures_capturees = []

    try:
        # Créer un environnement d'exécution avec l'état existant
        exec_globals = {
            '__builtins__': __builtins__,
            'plt': plt,
            'sns': sns,
            'np': np,
            'pd': pd,
        }

        # Ajouter l'état existant
        exec_globals.update(execution_state)

        # Gérer les imports et l'exécution du code
        instructions_import = []
        code_sans_imports = []

        for ligne in code.split('\n'):
            if ligne.strip().startswith(('import ', 'from ')):
                instructions_import.append(ligne)
            else:
                code_sans_imports.append(ligne)

        # Exécuter les imports
        for import_stmt in instructions_import:
            exec(import_stmt, exec_globals)

        # Exécuter le code principal
        exec('\n'.join(code_sans_imports), exec_globals)

        # Mettre à jour l'état d'exécution avec les nouvelles variables
        execution_state.update({
            k: v for k, v in exec_globals.items()
            if not k.startswith('__') and k not in ('plt', 'sns', 'np', 'pd')
        })

        # Capturer les figures
        figures_capturees = [plt.figure(num) for num in plt.get_fignums()]

        sortie = stdout_capture.getvalue()
        return True, sortie.strip() if sortie.strip() else "Code exécuté avec succès.", figures_capturees

    except Exception as e:
        return False, traceback.format_exc(), []

    finally:
        sys.stdin, sys.stdout, sys.stderr = old_stdin, old_stdout, old_stderr
        stdin_capture.close()
        stdout_capture.close()
        stderr_capture.close()


def est_code_securise(code: str) -> Tuple[bool, str]:
    """
    Vérifier si le code est sûr à exécuter
    """
    modeles_non_securises = [r'open\(', r'exec\(', r'eval\(']

    for modele in modeles_non_securises:
        if re.search(modele, code):
            return False, "Modèle de code non sécurisé détecté"

    imports = re.findall(r'^import\s+(\w+)', code, re.MULTILINE)
    imports_depuis = re.findall(r'^from\s+(\w+)', code, re.MULTILINE)

    imports_non_autorises = [
        imp for imp in set(imports + imports_depuis)
        if not any(imp.startswith(autorise) for autorise in ALLOWED_MODULES)
    ]

    if imports_non_autorises:
        return False, f"Imports non autorisés : {', '.join(imports_non_autorises)}"

    return True, "Le code semble sûr"


def main():
    st.markdown('<h1 class="title">Console Python de Data AI Lab</h1>', unsafe_allow_html=True)

    # Ajouter un script JavaScript personnalisé
    components.html("""
    <script>
    document.addEventListener('keydown', function(event) {
        if (event.shiftKey && event.key === 'Enter') {
            event.preventDefault();
            window.parent.postMessage({'type': 'streamlit:executeCode'}, '*');
        }
    });
    </script>
    """, height=0)

    # Zone de saisie de code
    nouveau_code = st.text_area(
        "Nouvelle Cellule de Code :",
        value=st.session_state.code_input,
        key="code_input_area",
        height=150,
        help="Utilisez Shift+Entrée pour exécuter le code"
    )

    # Mettre à jour la valeur dans le state
    st.session_state.code_input = nouveau_code

    # Bouton d'exécution
    col1, col2 = st.columns([3, 1])
    with col1:
        execution_demandee = st.button("Exécuter")

    # Vérifier si un message d'exécution a été reçu
    execute_from_js = st.session_state.get('execute_from_js', False)

    # Réinitialiser le flag
    if execute_from_js:
        st.session_state.execute_from_js = False

    # Conditions d'exécution
    if execution_demandee or execute_from_js:
        if nouveau_code.strip():
            # Vérifier la sécurité du code
            est_securise, message_securite = est_code_securise(nouveau_code)

            if not est_securise:
                st.error(f"⚠️ {message_securite}")
            else:
                # Exécuter le code et stocker dans l'historique
                succes, sortie, figures = executer_code_en_securite(
                    nouveau_code,
                    st.session_state.execution_state
                )

                st.session_state.execution_history.append({
                    'code': nouveau_code,
                    'output': sortie,
                    'figures': figures,
                    'success': succes
                })

                # Réinitialiser le code d'entrée
                st.session_state.code_input = ""
                st.experimental_rerun()

    # Afficher l'historique d'exécution dans l'ordre inverse
    for cellule in reversed(st.session_state.execution_history):
        with st.expander("Cellule de Code", expanded=True):
            st.code(cellule['code'], language='python')
            if cellule['success']:
                st.success("Sortie :")
                if cellule['output']:
                    st.code(cellule['output'])
                for fig in cellule['figures']:
                    st.pyplot(fig)
            else:
                st.error(cellule['output'])


if __name__ == "__main__":
    main()