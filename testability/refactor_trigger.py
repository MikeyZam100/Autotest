import re
from langchain_core.runnables import Runnable

class RefactorTriggerAgent(Runnable):
    """
    LangChain-compatible agent that triggers refactoring for CLI wrapper functions
    flagged as 'refactor_required'. Uses RefactorAgent to extract logic, updates source files,
    and returns updated/new blueprints.
    """

    def invoke(self, input_dict: dict) -> list:
        """
        Args:
            input_dict: {
                "reports": List[dict],      # testability reports with action == "refactor_required"
                "blueprints": List[dict],   # matching blueprints (same order as reports)
                "refactor_agent": <RefactorAgent instance>
            }
        Returns:
            List of updated/new blueprints (original CLI blueprints replaced, new logic blueprints appended)
        """
        reports = input_dict.get("reports", [])
        blueprints = input_dict.get("blueprints", [])
        refactor_agent = input_dict.get("refactor_agent")

        if not refactor_agent:
            print("[RefactorTrigger] No RefactorAgent provided. Skipping refactor step.")
            return blueprints

        updated_blueprints = []
        for report, blueprint in zip(reports, blueprints):
            function_name = report.get("function_name")
            function_signature = blueprint.get("function_signature")
            filename = blueprint.get("filename")
            test_filename = blueprint.get("test_filename")
            description = blueprint.get("description")
            dependencies = blueprint.get("dependencies", [])

            # Read the source file
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    file_content = f.read()
            except Exception as e:
                print(f"[RefactorTrigger] Failed to read file '{filename}': {e}")
                updated_blueprints.append(blueprint)
                continue

            # Extract the full function code block
            func_pattern = re.compile(
                rf"(^\s*def\s+{re.escape(function_name)}\s*\([^\)]*\)\s*:[\s\S]+?)(?=^\s*def\s|\Z)",
                re.MULTILINE
            )
            func_match = func_pattern.search(file_content)
            if not func_match:
                print(f"[RefactorTrigger] Could not extract code for '{function_name}' in '{filename}'. Skipping.")
                updated_blueprints.append(blueprint)
                continue
            code_block = func_match.group(1)

            # Prepare input for RefactorAgent
            input_to_refactor = {
                "function_signature": function_signature,
                "description": description,
                "code": code_block,
                "filename": filename,
                "test_filename": test_filename,
                "dependencies": dependencies
            }

            # Call RefactorAgent
            result = refactor_agent.invoke(input_to_refactor)
            if not result.get("replace_original"):
                print(f"[RefactorTrigger] Refactor failed for '{function_name}' in '{filename}'. Skipping.")
                updated_blueprints.append(blueprint)
                continue

            # Append new function blueprint if present
            new_fn_bp = result.get("new_function_blueprint")
            if new_fn_bp and new_fn_bp.get("function_signature"):
                updated_blueprints.append(new_fn_bp)

            # Replace the CLI wrapper code in the file
            updated_cli_code = result.get("updated_cli_code", "").rstrip()
            if not updated_cli_code:
                print(f"[RefactorTrigger] No updated CLI code for '{function_name}'. Skipping replacement.")
                updated_blueprints.append(blueprint)
                continue

            # Replace the old function code with the new one in the file content
            new_file_content = (
                file_content[:func_match.start(1)]
                + updated_cli_code
                + "\n"
                + file_content[func_match.end(1):]
            )

            # Write back to file
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(new_file_content)
                print(f"[RefactorTrigger] Refactored '{function_name}' in '{filename}'.")
            except Exception as e:
                print(f"[RefactorTrigger] Failed to write updated file '{filename}': {e}")
                updated_blueprints.append(blueprint)
                continue

        return updated_blueprints