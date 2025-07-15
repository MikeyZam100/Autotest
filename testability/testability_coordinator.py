from langchain_core.runnables import Runnable

class TestabilityCoordinatorAgent(Runnable):
    """
    Coordinates routing of function blueprints based on testability reports.
    Sends 'refactor_required' to RefactorTriggerAgent,
    'testable' to TestSuiteGenAgent, and ignores 'skip'.
    """

    def invoke(self, input_dict: dict) -> list:
        """
        Args:
            input_dict: {
                "testability_reports": List[dict],
                "blueprints": List[dict],
                "refactor_agent": <RefactorTriggerAgent instance>,
                "test_suite_gen_agent": <TestSuiteGenAgent instance>
            }
        Returns:
            Updated list of blueprints after processing all testability actions.
        """
        testability_reports = input_dict.get("testability_reports", [])
        blueprints = input_dict.get("blueprints", [])
        refactor_agent = input_dict.get("refactor_agent")
        test_suite_gen_agent = input_dict.get("test_suite_gen_agent")

        # Helper: map function_name to blueprint
        def get_blueprint_by_name(function_name):
            for bp in blueprints:
                sig = bp.get("function_signature", "")
                # Extract function name from signature
                import re
                match = re.match(r"\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", sig)
                if match and match.group(1) == function_name:
                    return bp
            return None

        # Partition reports by action
        refactor_reports = []
        refactor_blueprints = []
        testable_reports = []
        testable_blueprints = []

        for report in testability_reports:
            action = report.get("action")
            function_name = report.get("function_name")
            bp = get_blueprint_by_name(function_name)
            if not bp:
                continue
            if action == "refactor_required":
                refactor_reports.append(report)
                refactor_blueprints.append(bp)
            elif action == "testable":
                testable_reports.append(report)
                testable_blueprints.append(bp)
            # skip: do nothing

        # Refactor phase
        updated_blueprints = blueprints.copy()
        if refactor_reports and refactor_agent:
            # Refactor agent expects blueprints and reports
            refactor_result = refactor_agent.invoke({
                "reports": refactor_reports,
                "blueprints": refactor_blueprints
            })
            # Replace/extend blueprints as needed
            if isinstance(refactor_result, list):
                # Remove old refactored blueprints, add new ones
                refactored_names = {r.get("function_name") for r in refactor_reports}
                updated_blueprints = [
                    bp for bp in updated_blueprints
                    if bp.get("function_signature", "").split("(")[0].replace("def ", "").strip() not in refactored_names
                ]
                updated_blueprints.extend(refactor_result)

        # Test suite generation phase
        if testable_reports and test_suite_gen_agent:
            test_suite_gen_agent.invoke({
                "reports": testable_reports,
                "blueprints": testable_blueprints
            })

        # Maintain original order: sort by order in original blueprints
        def blueprint_sort_key(bp):
            try:
                return blueprints.index(bp)
            except ValueError:
                return len(blueprints)  # new blueprints go last

        updated_blueprints = sorted(updated_blueprints, key=blueprint_sort_key)