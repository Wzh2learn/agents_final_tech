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

old_match = re.match
setattr(re, 'old_match', old_match)

def validate_employee_id(employee_ids: List[str]) -> List[str]:
    invalid_ids = []
    for emp_id in employee_ids:
        if not re.match(r'^EMP', emp_id):
            invalid_ids.append(emp_id)
    return invalid_ids

# Hidden unit test
def test_ids_without_emp():
    # Initializing a list of employee ids
    employee_ids = ['EMP100', '502', '303', 'EMP400', '505']
    # Calling the function to validate the employee ids
    result = validate_employee_id(employee_ids)
    # As per the problem statement, the invalid employee IDs are those which do not start with 'EMP'
    # Here, from the given list of employee ids ['EMP100', '502', '303', 'EMP400', '505'], only '502', '303' and '505' 
    # do not follow the pattern. Hence these are the invalid ids. 
    expected_result = ['502', '303', '505']
    
    # Checking if the result is equal to the expected result
    assert result == expected_result, f"Expected {expected_result} but got {result}"

# Trusted marker harness
import json as __v2_json
__v2_nonce = '5b8234f3896849599742253748c0a5ac'
__v2_role = 'generated_solution'
__v2_prog_syn_id = '[re.match]:[modify-function-name]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_ids_without_emp'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_ids_without_emp()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
