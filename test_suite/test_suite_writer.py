import os
from langchain_core.runnables import Runnable

class TestSuiteWriterAgent(Runnable):
    """
    Writes cleaned test code to disk as the final step in the test suite generation pipeline.
    """

    def invoke(self, input_dict: dict) -> dict:
        test_code = input_dict.get("test_code", "")
        test_filename = input_dict.get("test_filename", "")
        function_name = input_dict.get("function_name", "")

        # If test_code is empty or just whitespace, skip writing
        if not test_code or not test_code.strip():
            return {
                "function_name": function_name,
                "test_filename": test_filename,
                "status": "skipped_empty"
            }

        try:
            test_dir = os.path.dirname(test_filename)
            if test_dir:
                os.makedirs(test_dir, exist_ok=True)
            with open(test_filename, "w", encoding="utf-8") as f:
                f.write(test_code)
            return {
                "function_name": function_name,
                "test_filename": test_filename,
                "status": "written"
            }
        except Exception as e:
            return {
                "function_name": function_name,
                "test_filename": test_filename,
                "status": f"error:
            }