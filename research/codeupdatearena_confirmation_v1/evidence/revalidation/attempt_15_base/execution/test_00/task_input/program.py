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

def update_patient_records(records_string):
    # Replace 'date of birth' with 'DOB'
    result = re.sub(r'date of birth', 'DOB', records_string, flags=re.IGNORECASE)
    
    # Replace 'social security number' with 'SSN'
    result = re.sub(r'social security number', 'SSN', result, flags=re.IGNORECASE)
    
    # Replace dates from dd-mm-yyyy format to yyyy-mm-dd
    # Pattern matches dd-mm-yyyy where dd, mm, yyyy are digits
    def convert_date(match):
        day = match.group(1)
        month = match.group(2)
        year = match.group(3)
        return f"{year}-{month}-{day}"
    
    result = re.sub(r'(\d{2})-(\d{2})-(\d{4})', convert_date, result)
    
    return result

# Hidden unit test
def test_normal_case():
    records_string = 'Patient John Doe, date of birth: 01-03-1996, social security number: 123-45-6789'
    # Calling the solution function
    result = update_patient_records(records_string)
    expected_result = 'Patient John Doe, DOB: 1996-03-01, SSN: 16789-45-23'
    # Checking the equivalence between result and expected_result
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

# Trusted marker harness
import json as __v2_json
__v2_nonce = '40f47a69c87f4b5fac7f986e08d206b8'
__v2_role = 'generated_solution'
__v2_prog_syn_id = '[re.sub]:[add-function]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_normal_case'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_normal_case()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
