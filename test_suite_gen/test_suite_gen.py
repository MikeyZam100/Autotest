from .utils import *
from utils.code_extractor import extract_test_code

# Load test suite generation prompt
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "test_suite_gen_prompt.txt")
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    test_suite_prompt = f.read()

# Format the prompt template for the LLM
test_suite_prompt_template = PromptTemplate(
    input_variables=[
        "function_signature",
        "function_name",
        "import_path",
        "code"
    ],
    template=test_suite_prompt
)

# Set up the LLM
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
        self.chain = test_suite_prompt_template | llm

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
        llm_message = self.chain.invoke(prompt_input)

        # Handle raw string return from LLM
        if hasattr(llm_message, 'content'):
            raw_content = llm_message.content.strip()
        else:
            raw_content = str(llm_message).strip()

        # Remove markdown code fences
        if raw_content.startswith("```"):
            raw_content = re.sub(r"^```(?:\w+)?\n", "", raw_content)
            raw_content = re.sub(r"\n```$", "", raw_content)

        # Debug print
        print("🧪 Cleaned test code preview:\n", raw_content[:300])  # print first 300 chars for sanity

        # Return structured result
        return {
            "test_suite": raw_content,
            "status": "generated"
        }

