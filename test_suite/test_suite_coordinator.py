from .utils import *
from .test_suite_gen import TestSuiteGenAgent
from .test_suite_cleaner import TestSuiteCleanerAgent
from .test_suite_writer import TestSuiteWriterAgent

import re

class TestSuiteCoordinatorAgent(Runnable):
    """
    Orchestrates the test suite generation pipeline:
    - Receives blueprints and testability reports
    - Forwards testable functions to downstream agents (gen, clean, write)
    - Returns a list of results (one per function processed)
    """

    def invoke(self, input_dict: dict) -> list:
        """
        Args:
            input_dict: {
                "blueprints": List[dict],
                "testability_reports": List[dict]
            }
        Returns:
            List of dicts, one per processed function:
            {
                "function_name": ...,
                "status": ...,
                "test_filename": ...
            }
        """
        blueprints = input_dict.get("blueprints", [])
        testability_reports = input_dict.get("testability_reports", [])

        # Build a lookup for reports by function_name
        report_lookup = {r["function_name"]: r for r in testability_reports}

        # Instantiate downstream agents
        gen_agent = TestSuiteGenAgent()
        cleaner_agent = TestSuiteCleanerAgent()
        writer_agent = TestSuiteWriterAgent()

        results = []

        for bp in blueprints:
            # Extract function name from signature if not present
            sig = bp.get("function_signature", "")
            match = re.match(r"\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", sig)
            function_name = match.group(1) if match else bp.get("function_name", "")

            report = report_lookup.get(function_name)
            if not report or report.get("action") != "testable":
                # Not testable or no report, skip
                results.append({
                    "function_name": function_name,
                    "status": "skipped",
                    "test_filename": bp.get("test_filename", "")
                })
                continue

            # Prepare required fields for test suite generation
            try:
                code = bp.get("code", "")
                function_signature = bp.get("function_signature", "")
                import_path = bp.get("import_path", "")
                test_filename = bp.get("test_filename", "")
                source_filename = bp.get("filename", "")

                # If code is missing, try to read from file
                if not code and source_filename and function_signature:
                    try:
                        with open(source_filename, "r", encoding="utf-8") as f:
                            file_content = f.read()
                        # Extract the function code block
                        func_pattern = re.compile(
                            rf"(^\s*def\s+{re.escape(function_name)}\s*\([^\)]*\)\s*:[\s\S]+?)(?=^\s*def\s|\Z)",
                            re.MULTILINE
                        )
                        func_match = func_pattern.search(file_content)
                        if func_match:
                            code = func_match.group(1)
                    except Exception as e:
                        results.append({
                            "function_name": function_name,
                            "status": f"error_reading_code: {e}",
                            "test_filename": test_filename
                        })
                        continue

                # Step 1: Generate raw test suite
                gen_result = gen_agent.invoke({
                    "code": code,
                    "function_signature": function_signature,
                    "function_name": function_name,
                    "import_path": import_path,
                    "test_filename": test_filename,
                    "source_filename": source_filename
                })
                raw_test_code = gen_result.get("test_suite", "")

                # Step 2: Clean the test code
                clean_result = cleaner_agent.invoke({
                    "test_code": raw_test_code,
                    "function_name": function_name,
                    "test_filename": test_filename
                })
                cleaned_test_code = clean_result.get("cleaned_test_code", "")

                # Step 3: Write the test code to disk
                write_result = writer_agent.invoke({
                    "test_code": cleaned_test_code,
                    "test_filename": test_filename,
                    "function_name": function_name
                })

                # Final output
                results.append({
                    "function_name": function_name,
                    "status": write_result.get("status", "written"),
                    "test_filename": test_filename
                })

            except Exception as e:
                results.append({
                    "function_name": function_name,
                    "status": f"error: {e}",
                    "test_filename": bp.get("test_filename", "")
                })
                continue