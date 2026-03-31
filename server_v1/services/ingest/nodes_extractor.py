from typing import Dict, List, Optional, Set
from services.ingest.parser import get_parser
from core.logging import get_logger

from services.ingest.helper.regex_extractor.extract_calls import extract_calls_from_text
from services.ingest.helper.regex_extractor.extract_imports import extract_imports
from services.ingest.helper.regex_extractor.extract_names import extract_name_from_node

logger = get_logger(__name__)

MAX_CHUNK_SIZE = 1500  
MIN_CHUNK_SIZE = 50 


def make_base_node(
    node_id: str,
    name: Optional[str],
    ast_type: str,
    file_path: str,
    language: str,
    code_str: str,
    start_line: int,
    end_line: int,
    start_byte: int,
    end_byte: int,
    size: int,
    depth: int
) -> Dict:
    """Unified node skeleton for all node types."""
    return {
        "id": node_id,
        "name": name,
        "code_str": code_str,
        "ast_type": ast_type,
        "file": file_path,
        "language": language,
        "start_line": start_line,
        "end_line": end_line,
        "start_byte": start_byte,
        "end_byte": end_byte,
        "size": size,
        "relationships": {
            "belongs_to": [],      
            "parent": [],        
            "sibling": [],        
            "function_call": [],  
            "class_call": [],     
            "implements": [],      
            "extends": [],        
            "imports_from": []    
        },
        "metadata": {
            "depth": depth,
            "calls": [],          
            "type_references": [], 
            "is_definition": False,
            "definition_type": None 
        }
    }


def extract_nodes_from_file(file_path: str, language: str, root_node_id: str) -> List[Dict]:

    try:
        logger.info(f"Extracting Abstract Syntax Tree (AST) components from: {file_path.split('/')[-1]}")
        with open(file_path, 'rb') as f:
            code = f.read()
        code_str = code.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []
    
    # once for whole code content of that file
    file_imports = extract_imports(code_str, language)
    
    # A File Node, for building proper dependency graph
    file_node_id = f"{file_path}:FILE"
    file_node = make_base_node(
        node_id=file_node_id,
        name=file_path.split('/')[-1], 
        ast_type="file",
        file_path=file_path,
        language=language,
        code_str=f"File: {file_path}\nLines: {len(code_str.splitlines())}",
        start_line=1,
        end_line=len(code_str.splitlines()),
        start_byte=0,
        end_byte=len(code_str),
        size=len(code_str),
        depth=0
    )
    
    # File node relationships
    file_node["relationships"]["belongs_to"] = [root_node_id]
    file_node["relationships"]["imports_from"] = file_imports
    

    # Parse AST
    parser = get_parser(language)
    if not parser:
        logger.warning(f"No parser for {language}, returning only FILE node")
        return [file_node]
    
    tree = parser.parse(code)
    
    # Initialize this with file_node
    all_nodes = [file_node]
    
    # Store chunks by ID for lookup
    chunks_dict: Dict[str, Dict] = {file_node_id: file_node}
    
    # Track definitions in this file (for call resolution)
    definitions: Dict[str, str] = {}  # name -> node_id
    
    def chunk_ast_node(
        node,
        sibling_ids: Optional[List[str]] = None,
        depth: int = 1
    ) -> List[str]:
        
        if sibling_ids is None:
            sibling_ids = []
        
        node_size = node.end_byte - node.start_byte
        
        
        # CASE 1: Node fits - create chunk
        if node_size <= MAX_CHUNK_SIZE:
            try:
                text = node.text.decode('utf-8', errors='ignore')
            except:
                return sibling_ids
            
            if not text.strip():
                return sibling_ids
            
            # node.type = function_definition, for_statement, identifier, class declaration
            chunk_id = f"{file_path}:{node.start_point[0]}:{node.type}"
            
            # # Skip duplicates
            # if chunk_id in chunks_dict:
            #     return sibling_ids
            
            # Extract name, like for any function chunk, the name will be funciton name
            name = extract_name_from_node(node, text, language)
            
            # Extract calls from code text
            calls = extract_calls_from_text(text, language)
            
            
            # Determine if definition and its type
            is_def, def_type = get_definition_info(node.type, language)
            
            # Create chunk
            chunk = make_base_node(
                node_id=chunk_id,
                name=name,
                ast_type=node.type,
                file_path=file_path,
                language=language,
                code_str=text,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                size=node_size,
                depth=depth
            )
            
            # Set relationships
            chunk["relationships"]["belongs_to"] = [file_node_id]
            
            # Add nearby siblings (last 2-3 only)
            nearby_siblings = sibling_ids[-2:] if len(sibling_ids) >= 2 else sibling_ids
            chunk["relationships"]["sibling"] = nearby_siblings.copy()
            
            # Imports only for import statement nodes
            if node.type in ['import_statement', 'import_declaration', 'import_from_statement']:
                chunk["relationships"]["imports_from"] = file_imports
            
            # Set metadata
            chunk["metadata"]["calls"] = list(calls)
            chunk["metadata"]["is_definition"] = is_def
            chunk["metadata"]["definition_type"] = def_type
            
            # Store chunk
            chunks_dict[chunk_id] = chunk
            all_nodes.append(chunk)
            
            # Track definitions (for later call resolution)
            if is_def and name:
                definitions[name] = chunk_id
            
            # Add bidirectional sibling links (only to nearby siblings)
            for sib_id in nearby_siblings:
                if sib_id in chunks_dict:
                    chunks_dict[sib_id]["relationships"]["sibling"].append(chunk_id)
            
            return sibling_ids + [chunk_id]
        
        # CASE 2: Node too large - RECURSE to children 
        else:
            child_sibling_ids = []
            for child in node.children:
                child_sibling_ids = chunk_ast_node(
                    child,
                    sibling_ids=child_sibling_ids,
                    depth=depth + 1
                )
            return sibling_ids
    
    # Start recursion (FILE node is parent of top-level)
    chunk_ast_node(
        tree.root_node,
        sibling_ids=[],
        depth=1
    )
    
    # ========================================================================
    # POST-PROCESSING: Resolve calls to definition node IDs
    # ========================================================================
    
    for chunk_id, chunk in chunks_dict.items():
        if chunk_id == file_node_id:
            continue
        
        raw_calls = chunk["metadata"].get("calls", [])
        
        for call_name in raw_calls:
            # Check if this call matches a definition in the file
            if call_name in definitions:
                def_node_id = definitions[call_name]
                
                # Determine if it's a function or class call
                def_node = chunks_dict[def_node_id]
                def_type = def_node["metadata"].get("definition_type")
                
                if def_type in ["function", "method"]:
                    if def_node_id not in chunk["relationships"]["function_call"]:
                        chunk["relationships"]["function_call"].append(def_node_id)
                
                elif def_type in ["class", "interface", "enum"]:
                    if def_node_id not in chunk["relationships"]["class_call"]:
                        chunk["relationships"]["class_call"].append(def_node_id)

    logger.info(f"Compiled {len(all_nodes)} structural CodeNodes from {file_path.split('/')[-1]}")
    return all_nodes







def get_definition_info(ast_type: str, language: str) -> tuple[bool, Optional[str]]:
    definition_map = {
        # Functions
        'function_definition': 'function',
        'function_declaration': 'function',
        'function_expression': 'function',
        'arrow_function': 'function',
        'method_definition': 'method',
        
        # Classes
        'class_definition': 'class',
        'class_declaration': 'class',
        
        # Interfaces
        'interface_declaration': 'interface',
        
        # Types
        'type_alias_declaration': 'type',
        
        # Enums
        'enum_declaration': 'enum',
        
        # Variables
        'lexical_declaration': 'variable',
        'variable_declaration': 'variable'
    }
    
    def_type = definition_map.get(ast_type)
    return (def_type is not None, def_type)