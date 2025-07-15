import os
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable, RunnableLambda

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "test_suite_gen_prompt.txt")
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    test_suite_prompt = f.read()

test_suite_prompt_template = PromptTemplate(
    input_variables=[
        "function_signature",
        "function_name",
        "import_path",
        "code"
    ],
    template=test_suite_prompt
)

llm = ChatOpenAI(
    model="gpt-3.5-turbo-0125",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

class TestSuiteGenAgent(Runnable):
    """
    LangChain-compatible agent for generating a raw test suite from the LLM.
    Only generates the test code; does not clean or write to disk.
    """

    def __init__(self):
        self.chain = test_suite_prompt_template | llm | RunnableLambda(lambda x: {"test_suite": x, "status": "generated"})

    def invoke(self, input_dict: dict) -> dict:
        # Validate required inputs
        required = ["code", "function_signature", "function_name", "import_path", "test_filename", "source_filename"]
        for key in required:
            if not input_dict.get(key):
                raise ValueError(f"Missing required input: {key}")

        # Prepare prompt input for the LLM
        prompt_input = {
            "function_signature": input_dict["function_signature"],
            "function_name": input_dict["function_name"],
            "import_path": input_dict["import_path"],
            "code": input_dict["code"]
        }

        # Run the LLM chain
        llm_response = self.chain.invoke(prompt_input)

        # Return structured output
        return {
            "test_suite": llm_response.get("test_suite", ""),
            "status": llm_response.get("status", "generated")
        }
