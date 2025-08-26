"""
Module Name: Doctest Generators
Purpose:
This module manages the generation and refinement of doctests for the ARHF tool.
It helps us:
- Collect unique doctests from users, LLMs, and analysis tools.
- Run candidate functions on suggested inputs to capture outputs or errors.
- Merge confirmed doctests with user-provided ones to build the final test set.

Date: 26 December 2024
"""


def suggested_doctest_inputs_generator(user_doctests: list, llm_doctests: list, crosshair_doctests: list, ghostwriter_doctests: list) -> list:
    """
    Returns a list of suggested doctests with unique entries distinct from the doctests in user doctests.
    """
    user_doctest_inputs = [doctest[0] for doctest in user_doctests]
    suggested_doctests = []

    # We check each source of generated doctests and filter out duplicates
    for doctest_list in (llm_doctests, crosshair_doctests, ghostwriter_doctests):
        for doctest_input in doctest_list:
            if doctest_input not in user_doctest_inputs and doctest_input not in suggested_doctests:
                suggested_doctests.append(doctest_input)
    
    return suggested_doctests


def refuted_doctest_inputs_generator(doctests: list, llm_doctests: list, user_doctests) -> list:
    """
    Returns a list of suggested doctests with unique entries distinct from the doctests in user doctests.
    """

    
    # We check both llm_doctests and doctests to find new candidates
    user_doctest_inputs = [doctest[0] for doctest in user_doctests]
    suggested_doctests = []
    
    for doctest_list in (llm_doctests, doctests):
        for doctest_input in doctest_list:
            if doctest_input not in user_doctest_inputs and doctest_input not in suggested_doctests:
                suggested_doctests.append(doctest_input)
    
    return suggested_doctests


def suggested_doctests_list_generator(suggested_doctest_inputs: list, function_name: str, function_code: str) -> list:
    """
    Returns a list of suggested doctests with outputs returned by the function_code.
    """
    if suggested_doctest_inputs == []:
        return []
    
    suggested_doctests =[]

    namespace = {}
    exec(function_code, namespace)
    function_ref = namespace.get(function_name)

    if not isinstance(suggested_doctest_inputs[0], tuple):
        for doctest_input in suggested_doctest_inputs:
            try:
                output = function_ref(doctest_input)
                suggested_doctests.append((doctest_input, output))
            except Exception as e:
                suggested_doctests.append((doctest_input, f"Error: {str(e)}"))
    else:
        for doctest_input in suggested_doctest_inputs:
            try:
                output = function_ref(*doctest_input)
                suggested_doctests.append((doctest_input, output))
            except Exception as e:
                suggested_doctests.append((doctest_input, f"Error: {str(e)}"))

    return suggested_doctests
    
def final_doctests_generator(doctests_details: dict, user_doctests: list, suggested_doctests: list, return_type: str) -> list:
    """
    All the three arguments are non-empty. Returns a list of all doctests with expected outputs. 
    Also returns a boolen value representing if all the doctests are passed or not.
    """

    all_doctests_passed = True
    new_doctests = []

    # Go through each suggested doctest and see if the user accepted it
    for i in range(len(suggested_doctests)):
        doctest = suggested_doctests[i]
        if doctests_details[f"confirmation_{i}"] == "accept":
            if doctest[1] != "Error":
                new_doctests.append(doctest)
        else:
            all_doctests_passed = False
            if doctests_details[f"output_{i}"] != "Error":
                if return_type == "str":
                    new_doctests.append((doctest[0], doctests_details[f"output_{i}"]))
                else:
                    new_doctests.append((doctest[0], eval(doctests_details[f"output_{i}"])))
    
    return (user_doctests + new_doctests), all_doctests_passed #non-empty



def final_doctests(doctests_details, llm_doctests, user_doctests, old_doctests):

    all_doctests_passed = True
    new_doctests = []

    for _ in range(len(llm_doctests)):
        doctest = llm_doctests[_]
        if doctests_details[f"confirmation_{_}"] == "accept":
            if doctest[1] != "Error":
                new_doctests.append(doctest)
        else:
            all_doctests_passed = False
            if doctests_details[f"output_{_}"] != "Error":
                new_doctests.append((doctest[0], doctests_details[f"output_{_}"]))
    
    return (new_doctests + user_doctests + old_doctests), all_doctests_passed