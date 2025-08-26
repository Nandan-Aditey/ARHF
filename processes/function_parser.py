"""
Module Name: Function Details
Purpose:
This module provides helper functions to:
- Build Python function signatures from user input.
- Generate doctests from user-provided examples.
- Support iterative refinement through "refute" doctests.

These utilities are central to the ARHF Tool’s workflow of
transforming user input into verifiable function implementations.

Date: 22 December 2024
"""

def function_signature_generator(function_details: dict) -> str:
    """
    Returns the function signature as a string, from the given dictionary function_details.
    """
    # Extract function name
    function_name = function_details["function_name"]
    
    # Extract and format arguments
    num_args = int(function_details["number_of_arguments"])
    arguments = [function_details[f"argument_{i}"] for i in range(1, num_args + 1)]
    arg_str = ", ".join(arguments)
    
    # Extract return type (Guaranteed to be one)
    return_type = function_details["return_1"]

    # Construct function signature
    return f"def {function_name}({arg_str}) -> {return_type}:"

def user_doctests_generator(function_details: dict) -> list:
    """
    Generates a list of doctest input-output pairs from the given dictionary function_details.
    For the example input dictionary, output will be the list [((1, 2, 3), 6), ((2, 3, 5), 10)].
    User must have provided atleast one doctest, if user provides nothing or invalid python objects, this function returns [].
    """
    num_tests = int(function_details["number_of_doctests"])
    
    doctests = []
    try:
        for i in range(1, num_tests + 1):
            input_str = function_details[f"doctest_{i}"]
            output_str = function_details[f"output_{i}"]

            # Convert string representation to Python objects
            input_val = eval(input_str)  # Convert "(1, 2)" -> (1, 2) or "[1, 2]" -> [1, 2]
            output_val = eval(output_str)  # Convert "1" -> 1 or "[1, 2]" -> [1, 2]

            # Ensure single argument inputs aren't stored as tuples
            doctests.append((input_val, output_val))

        return doctests
    except Exception:
        return []
    

def user_refute_doctests_generator(function_details: dict, num_tests) -> list:
    """
    Generates a list of doctest input-output pairs from the given dictionary function_details.
    For the example input dictionary, output will be the list [((1, 2, 3), 6), ((2, 3, 5), 10)].
    User must have provided atleast one doctest, if user provides nothing or invalid python objects, this function returns [].
    """    
    doctests = []
    try:
        for i in range(1, num_tests + 1):
            input_str = function_details[f"doctest_{i}"]
            output_str = function_details[f"output_{i}"]

            # Convert string representation to Python objects
            input_val = eval(input_str)  # Convert "(1, 2)" -> (1, 2) or "[1, 2]" -> [1, 2]
            output_val = eval(output_str)  # Convert "1" -> 1 or "[1, 2]" -> [1, 2]

            # Ensure single argument inputs aren't stored as tuples
            doctests.append((input_val, output_val))

        return doctests
    except Exception:
        return []