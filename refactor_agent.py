import os
from dotenv import load_dotenv
load_dotenv()

from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI
from langchain_core.runnables import Runnable
from langchain_core.runnables import RunnableLambda

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "refactor_agent_prompt.txt")
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    refactor_prompt = f.read()

refactor_prompt_template = PromptTemplate(
    input_variables=[
        "code",
        "function_signature",
        "function_name",
        "source_filename",
        "test_filename",
        "suggestion"
    ],
    template=refactor_prompt
)

llm = OpenAI(
    model="gpt-3.5-turbo-instruct",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

def parse_refactor_response(response: str) -> dict:
    """
    Parse the LLM response into a structured dictionary.
    Expects the LLM to return a JSON-like block.
    """
    import json
    try:
        # Try to find the first JSON object in the response
        start = response.find("{")
        end = response.rfind("}")
        if start != -1 and end != -1:
            json_str = response[start:end+1]
            return json.loads(json_str)
        else:
            return {
                "refactored_code": "",
                "pure_function_signature": "",
                "original_cli_function": "",
                "refactor_successful": False,
                "notes": "Could not parse LLM response as JSON."
            }
    except Exception as e:
        return {
            "refactored_code": "",
            "pure_function_signature": "",
            "original_cli_function": "",
            "refactor_successful": False,
            "notes": f"Failed to parse LLM response: {e}"
        }

class RefactorAgent(Runnable):
    """
    LangChain-compatible agent for refactoring CLI-heavy Python functions
    by extracting internal logic into a pure function.
    """

    def __init__(self):
        self.chain = refactor_prompt_template | llm | RunnableLambda(lambda x: {"output": x})

    def invoke(self, input_dict: dict) -> dict:
        # Extract required fields from input_dict
        function_signature = input_dict.get("function_signature", "")
        description = input_dict.get("description", "")
        code = input_dict.get("code", "")
        filename = input_dict.get("filename", "")
        test_filename = input_dict.get("test_filename", "")
        dependencies = input_dict.get("dependencies", [])

        # Compose suggestion for the LLM
        suggestion = (
            "Extract all internal logic into a new pure function that does not use input(), print(), or any CLI operations. "
            "The new function should accept parameters for all values that would have been gathered from the user. "
            "Update the original CLI function to call the new pure function and handle all user input/output."
        )

        # Validate required fields
        if not all([code, function_signature, filename, test_filename]):
            return {
                "new_function_blueprint": {},
                "updated_cli_code": "",
                "replace_original": False
            }

        # Prepare LLM input
        llm_input = {
            "code": code,
            "function_signature": function_signature,
            "function_name": function_signature.split("(")[0].replace("def ", "").strip(),
            "source_filename": filename,
            "test_filename": test_filename,
            "suggestion": suggestion
        }

        # Call the LLM
        result = self.chain.invoke(llm_input)
        response = result.get("output", "")
        parsed = parse_refactor_response(response)

        # If the LLM didn't return a valid refactor, mark as unsuccessful
        if not parsed.get("refactor_successful", False):
            return {
                "new_function_blueprint": {},
                "updated_cli_code": "",
                "replace_original": False
            }

        # Build the new function blueprint
        new_fn_sig = parsed.get("pure_function_signature", "")
        new_fn_desc = f"Pure logic extracted from {function_signature}."
        new_fn_blueprint = {
            "function_signature": new_fn_sig,
            "description": new_fn_desc,
            "filename": filename,
            "test_filename": test_filename,
            "dependencies": []
        }

        updated_cli_code = ""
        # Try to extract the updated CLI function from the refactored_code
        refactored_code = parsed.get("refactored_code", "")
        cli_fn_sig = parsed.get("original_cli_function", "")
        if cli_fn_sig and refactored_code:
            # Extract the CLI function code block
            import re
            pattern = rf"({cli_fn_sig}\s*:[\s\S]+?)(?=\ndef |\Z)"
            match = re.search(pattern, refactored_code)
            if match:
                updated_cli_code = match.group(1).rstrip()
            else:
                updated_cli_code = ""  # fallback

        return {
            "new_function_blueprint": new_fn_blueprint,
            "updated_cli_code": updated_cli_code,
            "replace_original": True
        }