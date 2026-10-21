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
def test_ids_numeric_only():
    # Initializing a list of employee ids with numeric-only ids
    employee_ids = ['EMP001', '002', '003', '004', 'EMP005']
    # Calling the function to validate the employee ids
    result = validate_employee_id(employee_ids)
    # As per the problem statement, any Employee ID that does not start with 'EMP' is invalid.
    # Therefore, the expected result is a list of Employee IDs that do not start with 'EMP'.
    # In the given input list ['EMP001', '002', '003', '004', 'EMP005'], the ids '002', '003' and '004' do not start with 'EMP'.
    # Hence, these ids are invalid.
    # So, the expected result is ['002', '003', '004'].
    expected_result = ['002', '003', '004']
    
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

# Trusted marker harness
import json as __v2_json
__v2_nonce = '4bed4c5261db4aafb461876f642039d2'
__v2_role = 'reference_solution'
__v2_prog_syn_id = '[re.match]:[modify-function-name]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_ids_numeric_only'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_ids_numeric_only()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
