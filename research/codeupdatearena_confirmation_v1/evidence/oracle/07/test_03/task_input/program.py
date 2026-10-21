# Trusted import block
import re
old_sub = re.sub
setattr(re, 'old_sub', old_sub)

# Trusted update implementation
def sub_multi(patterns_dict, string, count=0, flags=0):
    # iterate through each pattern, replacement pair in the given dictionary
    for pattern, repl in patterns_dict.items():
        # use the old_sub function to replace occurrences of the pattern with the replacement in the string
        # store the result back in the string variable to apply the next replacement in the next iteration
        string = old_sub(pattern, repl, string, count, flags)
    # after all replacements have been applied, return the final string
    return string

# Trusted update enforcement
setattr(re, 'sub_multi', sub_multi)

# Candidate solution
import re

# Function to update patient records using the new re.sub_multi function
def update_patient_records(records_string):
    # Define the dictionary with the patterns to replace and their corresponding replacement
    patterns_dict = {
        r"date of birth": "DOB",
        r"social security number": "SSN",
        r"(\d{2})-(\d{2})-(\d{4})": r"\3-\2-\1",  # regex pattern for converting date format
    }

    # Call the `re.sub_multi` function using the defined patterns dictionary 
    # This will simultaneously process any occurrence of the patterns
    return re.sub_multi(patterns_dict, records_string)

# Hidden unit test
def test_NoDOBorSSN_but_has_date():
    records_string = 'Patient Mary Doe, date: 25-12-1976'
    # Calling the solution function
    result = update_patient_records(records_string)
    expected_result = 'Patient Mary Doe, date: 1976-12-25'
    # Check equivalence between `expected_result` and `result`
    assert expected_result == result, f"Expected: {expected_result}, but got: {result}"

# Trusted marker harness
import json as __v2_json
__v2_nonce = '41d5ae04d1534a5d86c87db9f4317ff8'
__v2_role = 'reference_solution'
__v2_prog_syn_id = '[re.sub]:[add-function]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_NoDOBorSSN_but_has_date'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_NoDOBorSSN_but_has_date()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
