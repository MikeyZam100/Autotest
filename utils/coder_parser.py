import re
from typing import List

def split_functions(code: str) -> List[str]:
    """
    Splits a Python source string into top-level function blocks.
    Preserves decorators, docstrings, and inner indents.
    Only returns non-nested, top-level functions.
    """
    if not code:
        return []

    func_pattern = re.compile(
        r"""
        (
            (?:^[ \t]*@.*\n)*                                 # Optional decorator(s)
            ^[ \t]*def[ \t]+[a-zA-Z_][a-zA-Z0-9_]*[ \t]*\(.*\)[ \t]*:   # def line
            (?:\n(?:^[ \t]+.*\n?)*)*                          # Function body (indented)
        )
        """,
        re.MULTILINE | re.VERBOSE
    )

    matches = func_pattern.findall(code)
    return [func.rstrip() for func in matches]

def extract_function_signature(func_code: str) -> str:
    """
    Extracts the function signature (def ...:) from a function code block.
    Ignores decorators and docstrings.
    Returns "" if no signature is found.
    """
    if not func_code:
        return ""

    lines = func_code.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("def "):
            if stripped.endswith(":"):
                return stripped
            # Reconstruct multi-line signature
            signature_lines = [stripped]
            for next_line in lines[i+1:]:
                signature_lines.append(next_line.strip())
                if next_line.strip().endswith(":"):
                    break
            return " ".join(signature_lines)

    return ""
