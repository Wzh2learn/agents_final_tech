# Trusted import block
import re
old_match = re.match
setattr(re, 'old_match', old_match)

# Trusted update implementation
def match_start(pattern, string, flags=0):
    # The new API function implementation does not require any changes 
    # as the behavior of the function remains the same after the update. 
    # We continue to use `old_match` function for the actual matching.
    
    # Call the `old_match` function with input parameters
    result = old_match(pattern, string, flags)
    
    # Return the result
    return result

# Trusted update enforcement
setattr(re, 'match_start', match_start)

# Candidate solution
import re
from typing import List

def validate_employee_id(employee_ids: List[str]) -> List[str]:   
    # Define the pattern for matching the starting of the string
    pattern = 'EMP'
    
    # List to store the invalid employee ids
    invalid_ids = [] 
    
    # Loop through each employee id
    for id in employee_ids:
        # Use the new re.match_start function to check if the id starts with EMP
        match = re.match_start(pattern, id)
        # If the match doesn't exist, the id is invalid
        if match is None:
            invalid_ids.append(id)
            
    return invalid_ids

# Hidden unit test
def test_ids_with_emp():
    # Initializing a list of employee ids
    employee_ids = ['EMP001', 'EMP002', '003', 'EMP004', '005']
    # Calling the function to validate the employee ids
    result = validate_employee_id(employee_ids)
    # Since the function needs to return the IDs which don't start with 'EMP',
    # the expected result would be ['003', '005']
    expected_result = ['003', '005']
    
    # Testing if the resulting list matches the expected list
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

# Trusted marker harness
import json as __v2_json
__v2_nonce = '6e2d77eee9674660b9e9261fb6b8ec79'
__v2_role = 'reference_solution'
__v2_prog_syn_id = '[re.match]:[modify-function-name]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_ids_with_emp'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_ids_with_emp()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
