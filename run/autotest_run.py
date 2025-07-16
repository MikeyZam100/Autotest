import os
import sys
import subprocess

# === Setup Paths ===
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_FILE = os.path.join(ROOT_DIR, "autotest_target_file.py")
TEST_SUITE_FILE = os.path.join(ROOT_DIR, "test_suite.py")

# Ensure root is in sys.path for module imports
sys.path.insert(0, ROOT_DIR)

# === Import Pipeline Agents ===
from blueprint.blueprint_builder import build_blueprints_from_file
from testability.testability_analyzer import TestabilityAnalyzerAgent
from testability.refactor_trigger import RefactorTriggerAgent
from refactor.refactor_agent import RefactorAgent
from test_suite_gen.test_suite_coordinator import TestSuiteCoordinatorAgent


def load_target_code(path: str) -> str:
    if not os.path.exists(path):
        print(f"❌ Target file not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def clear_test_suite_file(path: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write("")  # Clear previous test suite


def run_pytest(path: str):
    try:
        subprocess.run(
            [sys.executable, "-m", "pytest", path],
            cwd=ROOT_DIR,
            capture_output=False
        )
    except Exception as e:
        print(f"❌ Failed to run pytest: {e}")
        sys.exit(1)


def main():
    print("🧠 Analyzing functions...")

    # Step 1: Load code
    code = load_target_code(TARGET_FILE)

    # Step 2: Extract function blueprints
    blueprints = build_blueprints_from_file(TARGET_FILE)

    # Step 3: Analyze testability
    analyzer = TestabilityAnalyzerAgent()
    testability_reports = analyzer.invoke({"code": code, "filename": TARGET_FILE})

    # Step 4: Refactor (if needed)
    if any(r.get("action") == "refactor_required" for r in testability_reports):
        print("🔁 Refactoring required functions...")
        refactor_trigger = RefactorTriggerAgent()
        refactor_agent = RefactorAgent()

        # Filter only refactor-needed items
        refactor_map = {
            r["function_name"]: r
            for r in testability_reports if r.get("action") == "refactor_required"
        }
        refactor_blueprints = [bp for bp in blueprints if bp["function_name"] in refactor_map]
        updated = refactor_trigger.invoke({
            "reports": list(refactor_map.values()),
            "blueprints": refactor_blueprints,
            "refactor_agent": refactor_agent
        })

        # Merge back into full blueprint set
        blueprints = [
            bp for bp in blueprints if bp["function_name"] not in refactor_map
        ] + updated

    # Step 5: Clear test suite
    clear_test_suite_file(TEST_SUITE_FILE)

    # Step 6: Generate test suite
    print("🛠️ Building test suite...")
    coordinator = TestSuiteCoordinatorAgent()
    coordinator.invoke({
        "blueprints": blueprints,
        "testability_reports": testability_reports
    })

    # Step 7: Run tests
    print("🚀 Running tests...")
    run_pytest(TEST_SUITE_FILE)
    print("✅ All tests complete!")


if __name__ == "__main__":
    main()
