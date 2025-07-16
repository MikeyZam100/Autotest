def extract_test_code(llm_response: str) -> dict:
    """
    Cleans the raw LLM output and returns the test suite string
    along with a status flag.
    """
    if not isinstance(llm_response, str):
        return {"test_suite": "", "status": "error: invalid LLM output"}

    # Remove markdown formatting junk
    cleaned = llm_response.strip()

    if cleaned.lower().startswith("```python"):
        cleaned = cleaned.removeprefix("```python").strip()
    elif cleaned.lower().startswith("python"):
        cleaned = cleaned.removeprefix("python").strip()

    if cleaned.endswith("```"):
        cleaned = cleaned.removesuffix("```").strip()

    return {"test_suite": cleaned, "status": "generated"}
