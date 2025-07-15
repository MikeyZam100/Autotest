from langchain_core.runnables import Runnable
from utils.code_parser import split_functions, extract_function_signature

import re

class TestabilityAnalyzerAgent(Runnable):
    """
    LangChain-compatible agent that analyzes Python code for function-level testability.
    Receives a code string and filename, returns a list of testability reports.
    """

    def invoke(self, input_dict: dict) -> list:
        """
        Args:
            input_dict: {
                "code": <str>,  # Python code (possibly a full file)
                "filename": <str>
            }
        Returns:
            List of dicts, one per function:
            {
                "function_name": ...,
                "function_signature": ...,
                "is_testable": True/False,
                "requires_refactor": True/False,
                "reason": <str>,
                "action": "testable" | "refactor_required" | "skip"
            }
        """
        code = input_dict.get("code", "")
        filename = input_dict.get("filename", "")

        # Use code_parser to split code into functions
        functions = split_functions(code)

        reports = []
        for func_code in functions:
            signature = extract_function_signature(func_code)
            function_name = self._extract_function_name(signature)

            # Heuristics for CLI/IO
            is_cli = any(word in func_code.lower() for word in ["input(", "print(", "sys.stdin", "sys.stdout"])
            has_logic = self._has_internal_logic(func_code)

            # Determine testability
            if not signature or not function_name:
                reports.append({
                    "function_name": function_name or "unknown",
                    "function_signature": signature or "",
                    "is_testable": False,
                    "requires_refactor": False,
                    "reason": "Missing or malformed function signature.",
                    "action": "skip"
                })
                continue

            if is_cli and has_logic:
                reports.append({
                    "function_name": function_name,
                    "function_signature": signature,
                    "is_testable": False,
                    "requires_refactor": True,
                    "reason": "CLI wrapper around logic; needs refactor.",
                    "action": "refactor_required"
                })
            elif is_cli and not has_logic:
                reports.append({
                    "function_name": function_name,
                    "function_signature": signature,
                    "is_testable": False,
                    "requires_refactor": False,
                    "reason": "Pure CLI/IO function with no testable logic.",
                    "action": "skip"
                })
            elif has_logic:
                reports.append({
                    "function_name": function_name,
                    "function_signature": signature,
                    "is_testable": True,
                    "requires_refactor": False,
                    "reason": "Pure logic with no CLI.",
                    "action": "testable"
                })
            else:
                reports.append({
                    "function_name": function_name,
                    "function_signature": signature,
                    "is_testable": False,
                    "requires_refactor": False,
                    "reason": "No testable logic detected.",
                    "action": "skip"
                })

        return reports

    def _extract_function_name(self, signature: str) -> str:
        if not signature:
            return ""
        match = re.match(r"\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", signature)
        return match.group(1) if match else ""

    def _has_internal_logic(self, code: str) -> bool:
        # Heuristic: look for assignments, control flow, return, yield, assert, math ops, etc.
        logic_keywords = [
            "=", "+", "-", "*", "/", "%", "**", "try:", "except", "if ", "for ", "while ",
            "return", "yield", "assert"
        ]
        return any(keyword in code for keyword in logic_keywords)