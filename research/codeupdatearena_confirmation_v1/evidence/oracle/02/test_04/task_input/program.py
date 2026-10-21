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
def test_ids_case_sensitive():
    # Initializing a list of employee ids with different cases
    employee_ids = ['EMP001', 'emp002', 'EMP003', 'Emp004', 'eMp005']
    # Calling the function to validate the employee ids
    result = validate_employee_id(employee_ids)
    # As the problem specification states, Employee IDs should start with 'EMP'. 
    # Therefore, even though the IDs 'emp002', 'Emp004' and 'eMp005' start with 'emp' (in different case), 
    # they still should be considered invalid as per the requirement.
    # Thus, the expected invalid IDs are 'emp002', 'Emp004' and 'eMp005'.
    expected_results = ['emp002', 'Emp004', 'eMp005']
    
    # Assertion statement for checking whether the output of validate_employee_id function is as expected 
    assert(set(result)==set(expected_results)), f"For employee_ids = {employee_ids}, expected output = {expected_results} but got = {result}"

# Trusted marker harness
import json as __v2_json
__v2_nonce = 'c776862b3cc349058573b6d110560b1e'
__v2_role = 'reference_solution'
__v2_prog_syn_id = '[re.match]:[modify-function-name]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_ids_case_sensitive'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_ids_case_sensitive()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
