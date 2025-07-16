import re
from typing import List
from utils.code_parser import split_functions, extract_function_signature

def _extract_function_name(signature: str) -> str:
    if not signature:
        return ""
    match = re.match(r"\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", signature)
    return match.group(1) if match else ""

def build_blueprints_from_file(file_path: str) -> List[dict]:
    """
    Reads a Python file, extracts all top-level functions, and builds blueprint dicts for each.

    Args:
        file_path: Path to the Python file to analyze.

    Returns:
        List of blueprint dictionaries, one per function.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    function_blocks = split_functions(code)
    blueprints = []

    for func_code in function_blocks:
        signature = extract_function_signature(func_code)
        function_name = _extract_function_name(signature)
        blueprint = {
            "function_signature": signature,
            "function_name": function_name,
            "code": func_code,
            "filename": "autotest_target_file.py",
            "test_filename": "test_suite.py",
            "import_path": "autotest_target_file",
            "description": "",
            "dependencies": []
        }
        blueprints.append(blueprint)

    return blueprints