"""
Module Name: Crosshair-DocTests
Purpose: Generate Python doctests using CrossHair.

Date: 10 December 2024
"""

import sys
from pathlib import Path

# Add the parent directory of the LLM folder to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent))

import subprocess
import re
from ast import literal_eval
import logging

logging.basicConfig(level=logging.DEBUG)  # Set logging level for detailed output

def is_crosshair_installed() -> bool:
    """
    Checks if CrossHair is installed and available in the PATH.

    Returns:
        True if CrossHair is installed, False otherwise.
    """
    result = subprocess.run(["crosshair", "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.returncode == 0



def generate_doctest_CrossHair(file_name: str):

    """
    Runs CrossHair on the specified file and extracts edge cases as doctests.

    Args:
        file_name: Path to the file containing the function.

    Returns:
        A list of tuples representing inputs and expected outputs.
    """
    # Define the root directory of the project (e.g. "ARHF")
    project_root = Path(__file__).parent
    programs_folder = project_root / "Programs"

    # Save the file to the "Programs" folder
    file_path = programs_folder / file_name

    if not is_crosshair_installed():
        logging.error("CrossHair is not installed or not in PATH.")
        sys.exit(1)

    # Validate file existence
    if not file_path.exists():
        logging.error(f"File does not exist: {file_path}")
        sys.exit(1)

    try:
        # Run CrossHair check
        result = subprocess.run(
            ["crosshair", "cover", str(file_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print("Result: ", result)

        # Log raw outputs
        logging.debug(f"CrossHair stdout: {result.stdout}")
        logging.debug(f"CrossHair stderr: {result.stderr}")

        # Check if CrossHair encountered an error
        if result.returncode != 0:
            logging.error("CrossHair encountered an error or did not generate any matches.")
            return []

        # Regex to extract input and output
        pattern = r"(\w+)\((.*?)\)"


        matches = re.findall(pattern, result.stdout)
        # Log the matches found
        logging.debug(f"Matches found: {matches}")

        # matches are like: [('Divide', '0, 0'), ('Divide', '0, -1')]

        # Extract inputs and typecast them to the correct type

        CrossHair_Inputs = []

        for match in matches:
            inputs = match[1].split(", ")

            inputs = tuple(map(literal_eval, inputs))

            CrossHair_Inputs.append(inputs)

        print("CrossHair Inputs: ", CrossHair_Inputs)
        print("CrossHair Inputs types: ", type(CrossHair_Inputs))

        return CrossHair_Inputs

    except Exception as e:
        logging.error(f"Error running CrossHair: {e}")
        return []




