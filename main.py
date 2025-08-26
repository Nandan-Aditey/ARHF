"""
Module Name: User Interface
Purpose:
This module defines the Flask-based web application that serves as the front-end
for the ARHF Tool. It provides users with an interactive interface to generate,
verify, and refine Python function implementations using LLMs, CrossHair, and
other automated testing tools.

Specifically, this UI module:
- Renders the main landing page for user input.
- Accepts function details (name, docstring, arguments, return types, and user-provided doctests).
- Generates an initial candidate function implementation via LLMs, ensuring it passes syntax checks.
- Validates and regenerates function code until all user-provided doctests pass.
- Suggests additional doctests from LLMs, CrossHair, and integrates them into the workflow.
- Handles error scenarios gracefully (invalid details, failed generations).
- Supports iterative refinement ("refute" flow), where users and LLMs collaborate to improve failing code.
- Stores relevant session data (function metadata, doctests, generated code) across multiple request/response cycles.
- Returns final function code once it is verified against all doctests.

Date: 20 December 2024
"""

import sys
import os
from flask import Flask, render_template, request, session

# Add the root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary functions
from Crosshair.generate_doctest import generate_doctest_CrossHair
from LLM.LLM_Interface import generate_llm_doctests, Create_File, check_syntax_errors, verified_code_gen, refute_llm_code, refute_code_errors
from processes.function_parser import function_signature_generator, user_doctests_generator, user_refute_doctests_generator
from processes.doctests import suggested_doctest_inputs_generator, refuted_doctest_inputs_generator, suggested_doctests_list_generator, final_doctests_generator, final_doctests

UI = Flask(__name__)

# Remember to set the secret key for session management in your .env file, take a look at .env.example
UI.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')

# We have added print statements at various stages to help with debugging and understanding the flow of data.

# Loads the home page
@UI.route("/")
def UI_for_AI():
    return render_template('home.html')

@UI.route("/suggestedDoctests", methods=["POST"])
def show_suggested_doctests():
    # User provided details for the function stored in function_details, sample dictionary in format/functionDetailsType.txt
    function_details = dict(request.form)

    # Storing all necessary information inside variables
    function_name = function_details["function_name"]
    docstring = function_details["docstring"]
    function_signature = function_signature_generator(function_details)
    user_doctests = user_doctests_generator(function_details)
    number_of_arguments = function_details["number_of_arguments"]
    number_of_return_types = function_details["number_of_return_types"]
    print("user_doctests:", user_doctests)
    return_type = function_details["return_1"]

    # Generating first instance of function code (may contain ambiguities which resolved by our tool later)
    function_code = check_syntax_errors(function_signature, docstring, user_doctests)

    print("function_code:", function_code)

    # Send the user to error page if LLM was unable to generate function code with the given details, or other issues such as credit limitations etc.
    if not function_code:
        return render_template('errorGeneratingFunctionCode.html', error_message = "Seems you provided incorrect details or the LLM crashed")

    # Regenerating function code if it fails any of the doctests provided by user
    function_code = verified_code_gen(function_name, function_code, user_doctests)

    # The second level of error handling when LLM generated code is unable to pass all the user provided doctests
    if isinstance(function_code, dict):
        return render_template('errorGeneratingFunctionCode.html', error_message = "Seems llm generated code didn't pass all the doctests, or it crashed.")

    # Function code generation is done, that is syntax error free and passes all the user doctests

    # Suggested doctests generation
    file_name = Create_File(function_name, function_code) #for generation of ghostwriter and crosshair doctests

    # LLM doctests generation
    llm_doctests = generate_llm_doctests(function_signature, docstring)
    print("llm doctests:", llm_doctests)

    # Crosshair doctests generation
    Doctests_CrossHair = generate_doctest_CrossHair(file_name)
    print("Crosshair: ", Doctests_CrossHair)

    # Was used to test a feature, currently not in use hence just using an empty list inplace
    Doctests_GhostWriter = []

    # Combines all doctests, and removes duplicates.
    suggested_doctest_inputs = suggested_doctest_inputs_generator(user_doctests, llm_doctests, Doctests_CrossHair, Doctests_GhostWriter)
    print("suggested_doctest_inputs:", suggested_doctest_inputs)

    # Creation of suggested_doctests list to be shown on the page, this runs the function on the inputs generated to get the outputs
    suggested_doctests = suggested_doctests_list_generator(suggested_doctest_inputs, function_name, function_code)
    print("suggested_doctests:", suggested_doctests)

    # If no suggested_doctests, return the generated function_code
    if len(suggested_doctests) == 0:
        return render_template('yourFunctionCode.html', function_code = function_code)

    # Store necessary information in session, so it can be used for other requests/pages
    session['function_name'] = function_name
    session['docstring'] = docstring
    session['function_signature'] = function_signature
    session['user_doctests'] = user_doctests
    session['suggested_doctests'] = suggested_doctests
    session['function_code'] = function_code
    session['return_type'] = return_type 

    # Rendering suggested doctests page
    is_tuple = isinstance(suggested_doctests[0][0], tuple)   # Variable to check if input for doctests are tuples or non-tuples
    return render_template('suggestedDoctests.html', suggested_doctests = suggested_doctests, function_name = function_name, is_tuple = is_tuple)

@UI.route("/functionCode", methods=["POST"])
def get_function_code():

    # User expected outputs for suggested doctests is in doctests_details, a sample is contained in format/doctestDetailsType.txt
    doctests_details = dict(request.form)

    # Retrieve necessary information from session
    function_name = session.get('function_name')
    docstring = session.get('docstring')
    function_signature = session.get('function_signature')
    user_doctests = session.get('user_doctests')   #non-empty
    suggested_doctests = session.get('suggested_doctests')   #non-empty
    function_code = session.get('function_code')  #not None
    return_type = session.get('return_type')

    # Generating final doctests list for final code generation
    doctests, all_doctests_passed = final_doctests_generator(doctests_details, user_doctests, suggested_doctests, return_type)

    session['doctests'] = doctests  # store final doctests in session for later use

    # If all doctests are passed, return function_code
    if all_doctests_passed:
        return render_template('yourFunctionCode.html', function_code = function_code)

    # Regeneration of function code to pass all doctests
    function_code = check_syntax_errors(function_signature, docstring, doctests)

    if not function_code:
        return render_template('errorGeneratingFunctionCode.html', error_message = "Seems LLM couldn't generate the function code based on the suggested doctests or the LLM crashed")

    function_code = verified_code_gen(function_name, function_code, doctests)

    if isinstance(function_code, dict):
        min_value = min(function_code.values())
        min_key = next(key for key, value in function_code.items() if value == min_value)
        return render_template(
            'errorGeneratingFunctionCode.html',
            min_key = min_key
        )

    # Function code generation is done, that is syntax error free and passes all the user doctests and suggested doctests
    return render_template('yourFunctionCode.html', function_code = function_code)


@UI.route("/postFinalChoice", methods=["POST"])
def post_final_choice():
    action = request.form.get("action")

    if action == "go_back":
        return render_template('home.html')

    elif action == "refute":
        # Store the function code in the session for later use
        function_code = session.get('function_code')
        doctests = session.get('doctests')
        function_name = session.get('function_name')

        llm_doctests = refute_llm_code(function_code, doctests)

        print("llm doctests:", llm_doctests)

        #creation of refuted_doctests list to be shown on the page
        refuted_doctests = suggested_doctests_list_generator(llm_doctests, function_name, function_code)
        print("refuted_doctest:", refuted_doctests)

        if len(refuted_doctests) == 0:
            return render_template('yourFunctionCode.html', function_code = function_code)
        
        session['refuted_doctests'] = refuted_doctests

        print("refuted_doctests from session:", session.get('refuted_doctests'))

        print("function_name from session:", function_name)

        return render_template('refuteUser.html', refuted_doctests = refuted_doctests, function_name = function_name)
    return "Invalid action", 400


# The below features have not been entirely implemented, the route discussed in the ARHF paper ends here.


@UI.route("/refuteCode", methods=["POST"])
def refute_Code():
    function_details = dict(request.form)

    function_code = session.get('function_code')
    function_name = session.get('function_name')
    doctests = session.get('doctests')
    print("doctests from session:", doctests)
    refuted_doctests = session.get('refuted_doctests')

    user_doctests = user_refute_doctests_generator(function_details, function_details["number_of_doctests"]) # Doctests with inputs and expected outputs

    llm_doctests = refute_llm_code(function_code, doctests)
    session['llm_doctests'] = llm_doctests
    print("llm doctests:", llm_doctests)

    refuted_doctest_inputs = refuted_doctest_inputs_generator(doctests, llm_doctests, user_doctests)
    print("suggested_doctest_inputs:", refuted_doctest_inputs)

    session['refuted_doctests_inputs'] = refuted_doctest_inputs

    session['user_doctests'] = user_doctests

    # Creation of suggested_doctests list to be shown on the page
    suggested_doctests = suggested_doctests_list_generator(refuted_doctest_inputs, function_name, function_code)
    print("suggested_doctests:", suggested_doctests)

    is_tuple = isinstance(refuted_doctests[0][0], tuple)   # Variable to check if input for doctests are tuples or non-tuples

    return render_template('refuteCode.html', suggested_doctests = suggested_doctests, function_name = function_name, is_tuple = is_tuple)


@UI.route("/refuteFunctionCode", methods=["POST"]) 
def refute_function_code():

    old_doctests = session.get('doctests')

    function_name = session.get('function_name')

    function_code = session.get('function_code')

    doctests_details = dict(request.form)

    llm_doctests = session.get('llm_doctests')

    user_doctests = session.get('user_doctests')

    doctests, all_doctests_passed = final_doctests(doctests_details, llm_doctests, user_doctests, old_doctests)

    if all_doctests_passed:
        return render_template('yourFinalCode.html', function_code = function_code)
    
    temp_code = function_code
    
    function_code = refute_code_errors(session.get('function_code'), doctests)

    if not function_code:
        return render_template('errorGeneratingFunctionCode.html', error_message = f"Seems LLM couldn't generate the function code based on the suggested doctests or the LLM crashed \n\n\n Function Code: \n f{temp_code}")

    function_code = verified_code_gen(function_name, function_code, doctests) 
    if not function_code:
        return render_template('errorGeneratingFunctionCode.html', error_message = f"Seems llm generated code didn't pass all the doctests, or it crashed. \n\n\n Function Code: \n f{temp_code}")

    return render_template('yourFinalCode.html', function_code = function_code)


if __name__ == '__main__':
    UI.run(host='0.0.0.0')