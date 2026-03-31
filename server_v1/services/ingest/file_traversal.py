# services/ingest/file_traversal.py
import os
from typing import Dict, List, Set, Optional
from pathlib import Path
from core.logging import get_logger
from services.ingest.nodes_extractor import extract_nodes_from_file
from services.ingest.nodes_extractor import make_base_node
from services.ingest.helper.imports_resolver import resolve_imports_to_node_ids

logger = get_logger(__name__)

IGNORE_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'dist', 
    'build', '.next', 'coverage', '.cache', 'out', '.vscode',
    '.idea', 'venv', 'env', '__mocks__', '.pytest_cache'
}

LANGUAGES = {
    'py': 'python', 
    'js': 'javascript', 
    'ts': 'typescript', 
    'jsx': 'javascript',
    'tsx': 'typescript'
}

DOC_EXTENSIONS = ('.md', '.txt', '.rst', '.markdown')
CONFIG_EXTENSIONS = ('.json', '.yaml', '.yml', '.toml', '.ini', '.cfg')

STANDARD_LIBS = {
    'python': {'os', 'sys', 'json', 're', 'typing', 'collections', 'itertools', 
               'functools', 'pathlib', 'datetime', 'math', 'random', 'unittest',
               'pytest', 'numpy', 'pandas', 'requests', 'flask', 'django'},
    'javascript': {'react', 'react-dom', 'vue', 'angular', 'axios', 'lodash',
                   'express', 'next', 'node'},
    'typescript': {'react', 'react-dom', 'vue', 'angular', 'axios', 'lodash',
                   'express', 'next', 'node'}
}


def extract_all_nodes(repo_path: str) -> List[Dict]:
    """Extract all nodes with cross-file relationship tracking."""
    all_nodes = []

    root_node_id = f"{repo_path}:ROOT"
    root_node = make_base_node(
        node_id=root_node_id,
        name="ROOT", 
        ast_type="ROOT",
        file_path=repo_path,
        language="",
        code_str="",
        start_line=0,
        end_line=0,
        start_byte=0,
        end_byte=0,
        size=0,
        depth=0
    )

    all_nodes.append(root_node)
    
    logger.info(f"Initializing comprehensive file traversal and syntax extraction for {os.path.basename(repo_path)}...")
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            ext = file.split('.')[-1].lower()
            
            if ext in LANGUAGES:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repo_path)
                language = LANGUAGES[ext]
                
                logger.info(f"Processing {relative_path}...")
                
                # Extract all nodes from this
                nodes = extract_nodes_from_file(file_path, language, root_node_id)

                if len(nodes) > 0:
                    all_nodes.extend(nodes)
            
            elif file.lower().endswith(('.md', '.txt')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Simple chunking (you can replace with your chunk_text function)
                    chunk_size = 1000
                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i+chunk_size]
                        all_nodes.append({
                            'id': f"{file_path}:FILE_CHUNK_{i}",
                            'ast_type': 'FILE_CHUNK',
                            'name': f"{os.path.basename(file_path)}_chunk_{i//chunk_size}",
                            'code_str': chunk,
                            'file': file_path,
                            'language': 'markdown',
                            'start_line': 1,
                            'end_line': len(chunk.splitlines()),
                            'relationships': {},
                            'metadata': {}
                        })
                except Exception as e:
                    logger.error(f"Failed to read {file_path}: {e}")
    
    logger.info(f"AST extraction phase complete. Discovered {len(all_nodes)} distinct code elements across repository.")
    
    all_nodes = resolve_imports_to_node_ids(all_nodes, repo_path)
    
    return all_nodes