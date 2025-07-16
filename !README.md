# 🧪 Autotest — Automatic Test Suite Generator for Python

## 🚀 Overview
**Autotest** is a command-line tool that analyzes a Python file, detects functions, and automatically:
- Refactors CLI-heavy logic into testable functions (if needed)
- Generates `pytest`-compatible unit tests using AI
- Runs those tests and displays results

Built for developers who want fast, hands-off test coverage—especially useful when inheriting legacy code or prototyping rapidly.

---

## 📂 Project Structure

Autotest/
├── run/
│   └── autotest_run.py        # Main entrypoint
├── autotest_target_file.py    # Input: file with Python functions
├── test_suite.py              # Output: auto-generated tests
├── blueprint/                 # Builds function blueprints
├── testability/               # Analyzes and refactors testability
├── refactor/                  # Refactoring logic for CLI-bound code
├── test_suite_gen/           # Test generator agent
├── utils/                     # Shared tools (e.g. code extractor)


---

## 🛠️ How It Works
1. Place your functions into `autotest_target_file.py`
2. Run the script:  
   python run/autotest_run.py
   
3. That’s it!  
   - If your function needs refactoring (e.g. it's inside an `if __name__ == "__main__"` block), it’s refactored first.
   - Then, tests are generated and saved to `test_suite.py`
   - Finally, `pytest` runs automatically.

---

## 📋 Example
Given this code in `autotest_target_file.py`:

def add(x, y):
    return x + y


Autotest will generate:

import pytest
from autotest_target_file import add

def test_add_normal_inputs():
    assert add(2, 3) == 5
    assert add(0, 0) == 0
    assert add(-2, 5) == 3


---

## 💡 Why This Matters
- 🔁 Reduces boilerplate test writing  
- 🧠 Uses LLM reasoning to cover edge cases  
- 🧹 Cleans up CLI-bound code for real testability  
- 🧪 Compatible with standard `pytest` workflow

---

## 📎 Requirements
- Python 3.11+
- `pytest`
- OpenAI-compatible LLM (via local or API key – see `.env`)

---

## 📦 Future Improvements (Planned)
- CLI options (e.g. `--file`, `--dry-run`)
- Support for multiple files
- Coverage reporting
- LLM model switching

This README was made at 3 am by ChatGPT