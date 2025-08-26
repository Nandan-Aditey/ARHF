"""
Module Name: LLM Interface
Purpose:
This module handles communication with Hugging Face models for generating,
refuting, and verifying Python functions. It forms the core "LLM integration"
layer of the ARHF tool.

Specifically, this module:
- Makes robust API requests to Hugging Face with retries and validation.
- Generates candidate function code from function signatures, docstrings, and doctests.
- Refines incorrect code iteratively using doctests as ground truth.
- Extracts function code blocks safely from raw LLM responses.
- Generates suggested doctests (including edge cases) to strengthen testing.
- Validates generated code by running it against provided doctests.
- Creates project files for storing generated functions.
- Provides utilities for parsing and normalizing LLM-produced doctest inputs.

Date: 20 December 2023
"""


import re
import time
import ast
from pathlib import Path
import logging
import sys
import math
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError
from dotenv import load_dotenv
import os

load_dotenv()

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)


# API endpoint and headers for Hugging Face Inference
client = InferenceClient(api_key=os.getenv("HUGGING_FACE_API_KEY"))


# Sample function details dictionary
'''func_details = {
  "argument_1": "x: int",
  "argument_2": "y: int",
  "argument_3": "z: int",
  "docstring": "adds three integers",
  "doctest_1": "(1, 2, 3)",
  "doctest_2": "(2, 3, 5)",
  "function_name": "add_integers",
  "number_of_arguments": "3",
  "number_of_doctests": "2",
  "number_of_return_types": "1",
  "output_1": "6",
  "output_2": "10",
  "return_1": "int"
}'''

def make_request_with_retries(client, model, messages, retries=1, delay=0.5):
    """
    Makes an API request to Hugging Face with retries for transient errors.

    Args:
        client: The Hugging Face InferenceClient.
        model: The model to use.
        messages: The messages to send to the model.
        retries: Number of retries.
        delay: Delay between retries in seconds.

    Returns:
        The response object or None if all retries fail.
    """
    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages
           )
            if response is not None:
                logging.info(f"API request successful on attempt {attempt}.")
                return response
            else:
                logging.warning(f"Attempt {attempt}: Response is None. Retrying...")

        except HfHubHTTPError as e:  
            logging.error(f"API request failed on attempt {attempt}: {str(e)}")
        
        time.sleep(delay * attempt)

    logging.error("All retry attempts failed.")
    return None

def validate_api_response(response, expected_keys):
    """
    Validates the API response structure and content.

    Args:
        response: The JSON response object.
        expected_keys: A list of keys expected in the response.

    Returns:
        A boolean indicating whether the response is valid.
    """
    if response is None:
        logging.error("Response object is None.")
        return False

    for key in expected_keys:
        if key not in response:
            logging.error(f"Missing expected key '{key}' in the response. Full response: {response}")
            return False

    return True

def extract_function_code(response_text):
    """
    Extracts the function code from the response text.

    Args:
        response_text: The raw response text from the API.

    Returns:
        The extracted function code or None if extraction fails.
    """
    match = re.search(r"```(?:python)?\s*(def .+?)```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Find the first occurrence of 'def'
    def_index = response_text.find("def ")
    if def_index == -1:
        print("No function definition found.")
        return None
    
    # Trim response_text to start from 'def'
    response_text = response_text[def_index:]
    
    # Search for the first '\n' not followed by a space or tab
    lines = response_text.splitlines()
    
    for i, line in enumerate(lines[1:], start=1):  # Start from 1 to skip the first line containing 'def'
        if not line.startswith(" ") and not line.startswith("\t"):
            response_text = "\n".join(lines[:i])
            break
    
    logging.warning("Fallback extraction used.")
    return response_text.strip()

def generate_llm_doctests(function_signature: str, docstring: str) -> list:
    """
    Generates a list of Python doctests for the function using the Hugging Face API.

    Returns:
        The a list containing doctest input tuples, returns [] on syntax error or failure.
    """
    messages = [
        {
            "role": "user",
            "content": (
                "You are an expert at designing test inputs to catch subtle bugs in Python functions. \n"
                "Generate Python doctests for the following function:\n\n"
                f"{function_signature}\n"
                "\t\"\"\"\n"
                f"\t{docstring}\n"
                "\t\"\"\"\n"
                "\t#code of the function\n"
                "Generate a list of doctest inputs for the given function where each list item is a tuple of inputs. DO NOT generate expected outputs\n"
                "Think of all possible edge cases and generate the inputs for them.\n"
                "Try to think of all ambiguities in the function signature, try to find atleast 5-7 edge cases.\n"
                "Try to have more edge cases and less normal cases.\n"
                "For example, if the function is multiply(a: int, b: int), you can generate a response like the following:\n"
                "Ensure that the inputs are in the form of TUPLES, and the output is a LIST OF TUPLES. If there are lists or tuples as part of inputs, then also form a LIST OF TUPLES, where each tuple is a doctest\n"
                "[(2, 3), (-1, 0), (6, -6)]\n"
                "if the function is double(a: str), you can generate a response like this:\n"
                "[\"hello\", \"\", \"hi\"]\n"
                "DO NOT GIVE ME DOCTEST OUTPUTS, JUST GIVE ME THE INPUTS\n"
            )
        }
    ]

    response = make_request_with_retries(client, "Qwen/Qwen2.5-Coder-32B-Instruct", messages)

    if response and validate_api_response(response, ["choices"]):
        doctest_content = response['choices'][0]['message']['content']
        print("RESPONSE DOCTESTS:\n", doctest_content)

        # Try to extract directly from brackets
        first_bracket = doctest_content.find("[")
        last_bracket = doctest_content.rfind("]")

        if first_bracket != -1 and last_bracket != -1:
            doctest_content = doctest_content[first_bracket:last_bracket + 1]
        else:
            # Try markdown block fallback
            matches = re.findall(r"```(?:python)?\s*\n(\[.*?\])\s*```", doctest_content, re.DOTALL)
            if matches:
                doctest_content = matches[0]

        # Attempt to parse with ast.literal_eval
        try:
            doctest_inputs = ast.literal_eval(doctest_content)
            if isinstance(doctest_inputs, list) and doctest_inputs:
                return doctest_inputs
        except Exception:
            pass  # fallback below

        # Fallback: regex-based extraction
        matches = re.findall(
            r'\(\s*(".*?"|\'.*?\'|".*?"\s*\*\s*\d+|\'.*?\'\s*\*\s*\d+|".*?"\s*\+\s*".*?"|\'.*?\'\s*\+\s*\'.*?\')\s*,?\s*\)',
            doctest_content,
            re.DOTALL,
        )

        doctests = []
        for m in matches:
            try:
                value = eval(m)  # Controlled eval for quoted strings
                doctests.append((value,))
            except Exception:
                continue

        if doctests == []:
            doctests = parse_doctest_inputs(doctest_content)

        doctests = normalize_doctests(doctests)

        return doctests if doctests else []

    return []


def generate_function_code(function_signature, docstring, doctests=[]) -> str:
    """
    Generates the Python function code with the given function_details dictonary using the Hugging Face API, and 
    """
    messages = [
        {
            "role": "user",
            "content": (
                "Generate Python code/program for the following function:\n\n"
                f"{function_signature}\n"
                "\t\"\"\"\n"
                f"\t{docstring}"
                "\t\"\"\"\n"
                "\t#your code here\n\n"
                "Code of the function should be generated.\n"
                "Do not have comments in the code, other than the docstring.\n"
                f"The function must satisfy these doctests: {doctests}, every doctest is a tuple (input, output) in the provided list.\n"
                "Ensure that all doctests are passed\n"
                "Your response should only contain the function code in the specified format. \n"
            )
        }
    ]

    response = make_request_with_retries(client, "Qwen/Qwen2.5-Coder-32B-Instruct", messages)
    if response and validate_api_response(response, ["choices"]):
        function_content = response['choices'][0]['message']['content']
        return extract_function_code(function_content)

    return None


def check_syntax_errors(function_signature, docstring, doctests):
    """ 
    It runs the function generate_function_code repeatedly for 3 times. Returns a string containing the syntax error free code for the function,
    under the condition that user has provided meaningful details. Else, returns None.
    """
    namespace = {}
    i = 0
    while i < 3:
        try:
            new_response = generate_function_code(function_signature, docstring, doctests)
            exec(new_response, namespace)
            return new_response
        except Exception as e:
            logging.error(f"Error during execution: {e}")
            i += 1
            continue
    logging.error("Failed to generate valid function code after 5 attempts.")
    return None


def refute_code(function_code, doctests=[]) -> str:
    """
    Generates the Python function code with the given function_details dictonary using the Hugging Face API, and 
    """
    messages = [
        {
            "role": "user",
            "content": (
                "The below python function is wrong, it does not do the task it was asked to:\n\n"
                f"{function_code}\n"
                "\t\"\"\"\n"
                "\t#your code here\n\n"
                "\t\"\"\"\n"
                "Here are the doctests, with the correct answers, keep trying till you can pass all doctests: \n"
                f"{doctests}, every doctest is a tuple (input, output) in the provided list.\n"
                "Your response should only contain the function code in the specified format. \n"
            )
        }
    ]

    response = make_request_with_retries(client, "Qwen/Qwen2.5-Coder-32B-Instruct", messages)
    if response and validate_api_response(response, ["choices"]):
        function_content = response['choices'][0]['message']['content']
        return extract_function_code(function_content)

    return None


def refute_code_errors(function_code, doctests):
    """ 
    It runs the function generate_function_code repeatedly for 3 times. Returns a string containing the syntax error free code for the function,
    under the condition that user has provided meaningful details. Else, returns None.
    """
    namespace = {}
    i = 0
    while i < 3:
        try:
            new_response = refute_code(function_code, doctests)
            exec(new_response, namespace)
            return new_response
        except Exception as e:
            logging.error(f"Error during execution: {e}")
            i += 1
            continue
    logging.error("Failed to generate valid function code after 5 attempts.")
    return None


def repromt_llm(function_code: str, doctests: list, failed_doctests: list) -> str:
    """
    Generates the code for the requested function with a new prompt, informing the api about the failed doctests.
    Returns the function code as a string, and returns None on failure.
    """

    messages = [
        {
            "role": "user",
            "content": (
                "The incorrect function code (in python) is as follows:\n\n"
                f"{function_code}\n\n"
                f"Current function code fails the doctests: {failed_doctests}\n"
                f"Modify this function code to satisfy these doctests: {doctests}, every doctest is a tuple (input, output).\n"
                "To modify this function, try to find patterns in doctests, and reverse engineer to generate the function code so that the code passes all doctests.\n"
                "The failures are due to incorrect assumptions or logic in the code. Correct those assumptions with the help of doctests.\n"
                "The docstring is ambigious, do not rely on it. You should only trust the doctests\n"
                "DO NOT RETURN NONE, try to find out the variable or expression which explains the desired output and then use that to reverse engineer.\n"
                "The doctests have many edge cases covered, while the code does not cover them.\n"
                "Carefully go through the doctests (don't modify them) and revise the function code to pass all these doctests and give the corrected code in the same format.\n"
                "Your response should only contain the function code in the specified format. \n"
                "Some edge cases are reflected in only a single doctests, so don't ignore them.\n"
                "Incase you are not able to generate the code, explain the reason for failiure"
            )
        }
    ]

    response = make_request_with_retries(client, "Qwen/Qwen2.5-Coder-32B-Instruct", messages)
    print("RESPONSE:\n", response)
    if response and validate_api_response(response, ["choices"]):
        function_content = response['choices'][0]['message']['content']
        print()
        print()
        print("\n\n\n\n Function_code:", extract_function_code(function_content))
        return extract_function_code(function_content)

    return None


def refute_llm_code(function_code: str, doctests: list) -> str:

    messages = [
        {
            "role": "user",
            "content": (
                "You are an expert at designing test inputs to catch subtle bugs in Python functions. \n"
                "The following function is buggy/does not do what we want to do, the docstring provided might be meaningless, give me doctests to figure out the correct function:\n\n"
                f"{function_code}\n"
                "\t\"\"\"\n"
                "Here are the doctests that I have:\n"
                f"\t{doctests}\n"
                "\t\"\"\"\n"
                "Generate a list of doctest inputs for the given function where each list item is a tuple of inputs. DO NOT generate expected outputs\n"
                "For example, if the function is multiply(a: int, b: int), you can generate a response like the following:\n"
                "[(2, 3), (-1, 0), (6, -6)]\n"
                "Ensure that the inputs are in the form of TUPLES, and the output is a LIST OF TUPLES. If there are lists or tuples as part of inputs, then also form a LIST OF TUPLES, where each tuple is a doctest\n"
                "if the function is double(a: str), you can generate a response like this:\n"
                "[\"hello\", \"\", \"hi\"]\n"
                "DO NOT GIVE ME DOCTEST OUTPUTS, JUST GIVE ME THE INPUTS\n"
            )
        }
    ]

    response = make_request_with_retries(client, "Qwen/Qwen2.5-Coder-32B-Instruct", messages)
    if response and validate_api_response(response, ["choices"]):
        doctest_content = response['choices'][0]['message']['content']
        
        first_bracket = doctest_content.find("[")
        last_bracket = doctest_content.rfind("]")
        
        if first_bracket != -1 and last_bracket != -1:
            doctest_content = doctest_content[first_bracket:last_bracket+1]
        else:
            return []
        
        try:
            doctest_inputs = ast.literal_eval(doctest_content)
            if isinstance(doctest_inputs, list):
                return doctest_inputs
            return []
        except Exception:
            return []
    
    return []

def Create_File(function_name, function_code):
    # Define the root directory of the project (e.g., "ARHF")
    project_root = Path(__file__).parent  # Adjust this to your project root if needed
    project_root_root = project_root.parent
    programs_folder = project_root_root / "Crosshair" / "Programs"

    # Ensure the "Programs" folder exists
    programs_folder.mkdir(exist_ok=True)

    # Save the file to the "Programs" folder
    file_name = f"{function_name}.py"
    file_path = programs_folder / file_name

    # Create the file if it doesn't exist
    if not file_path.exists():
        try:
            # Add sample function definition to the file
            file_path.write_text(function_code)
            print(f"Created file: {file_path}")
        except Exception as e:
            print(f"Error creating file {file_path}: {e}")
            sys.exit(1)

    return file_name


def test(function_name: str, function_code: str, doctests: list) -> bool:
    """
    Assuming function_code contains a valid syntax error free callable python function code, it returns a list failed_doctests, containing doctests
    that the function failed.
    """
    if doctests == []:
        return [], []
    local_env = {}
    exec(function_code, local_env)
    func = local_env.get(function_name)
    failed_doctests = [] #contains failed doctest tuples with user expected outputs
    failed_doctests_results = [] #contains failed doctest tuples with outputs given by function
    if not isinstance(doctests[0][0], tuple): #assuming the inputs are either tuples or non-tuples
        for doctest in doctests:
            try:
                output = func(doctest[0])
                if output != doctest[1]:
                    failed_doctests.append(doctest)
                    failed_doctests_results.append((doctest[0], output))
            except Exception:
                failed_doctests.append(doctest)
                failed_doctests_results.append((doctest[0], "Error"))
    else:
        for doctest in doctests:
            try:
                output = func(*doctest[0])
                if output != doctest[1]:
                    failed_doctests.append(doctest)
                    failed_doctests_results.append((doctest[0], output))
            except Exception:
                failed_doctests.append(doctest)
                failed_doctests_results.append((doctest[0], "Error"))
    return failed_doctests, failed_doctests_results


def verified_code_gen(function_name: str, function_code: str, doctests: list) -> str:
    """
    Given a valid syntax free python code as a string in function_code, it implicitly checks if the python code is a valid function definition.
    And it checks if the function code passes all the doctests in the doctests list using the test function, if at least one doctest is failed,
    function code is generated again using reprompt_llm, and this goes on for atmax 5 times. If llm is not able to generate a code with passes 
    all the doctests, it returns None.
    """

    function_passAccuracy = {}

    i = 0
    while i < 5:
        failed_doctests = test(function_name, function_code, doctests)[0]
        if len(failed_doctests) == 0:
            return function_code
        function_passAccuracy[function_code] = len(failed_doctests)
        i += 1
        if i < 5:
            function_code = repromt_llm(function_code, doctests, failed_doctests) 
    return function_passAccuracy


def parse_doctest_inputs(text: str):
    """
    Safely parse LLM-generated doctest input lists.

    Handles:
    - Comments (# ...)
    - Integer/float literals
    - Arithmetic expressions (e.g., 2**31 - 1)
    - Special constants: None, True, False
    - float("inf"), float("nan")
    - complex(real, imag)
    """
    # Strip comments
    cleaned = re.sub(r"#.*", "", text)

    # Define safe evaluation environment
    safe_env = {
        "__builtins__": {},
        "None": None,
        "True": True,
        "False": False,
        "math": math,
        "float": float,
        "complex": complex,
    }

    # Try literal_eval
    try:
        return ast.literal_eval(cleaned)
    except Exception:
        pass

    # Fall back to restricted eval
    try:
        return eval(cleaned, safe_env, {})
    except Exception:
        return []


def normalize_doctests(doctests):
    normalized = []
    for d in doctests:
        if isinstance(d, tuple) and len(d) == 1:
            normalized.append(d[0])   # Unwrap single-element tuple
        else:
            normalized.append(d)
    return normalized
