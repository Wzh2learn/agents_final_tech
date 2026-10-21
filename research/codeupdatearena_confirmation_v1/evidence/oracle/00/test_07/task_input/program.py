# Trusted import block
import re
old_subn = re.subn
setattr(re, 'old_subn', old_subn)

# Trusted update implementation
def subn(pattern, repl, string, count=1, flags=0):
    # Call the old API function 'old_subn', passing in the arguments from the new function
    result = old_subn(pattern, repl, string, count, flags)
    
    # Return the result from the old API function
    return result

# Trusted update enforcement
re.subn = subn

# Candidate solution
import re

def mask_first_ip(log_string: str, mask: str) -> str:
    # Define the regex pattern for an IP address
    pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
    
    # Use the re.subn() function to replace the first occurrence of the pattern (IP address) in the log string with the mask
    # With the new version of re.subn(), the count default value is changed to 1.
    # So, by default only the first occurrence of the pattern is replaced in the string.
    replaced_string, _ = re.subn(pattern, mask, log_string)

    return replaced_string

# Hidden unit test
def test_log_string_is_empty():
    log_string = ''
    # Case where log string is empty, nothing to mask here.
    mask = 'XXX.XXX.XXX.XXX'
    result = mask_first_ip(log_string, mask)
    expected_result = ''
    assert result == expected_result, f"Expected '{expected_result}', but got '{result}'"

# Trusted marker harness
import json as __v2_json
__v2_nonce = '6296ee8600a34a21be36ea2d9b1b9c4d'
__v2_role = 'reference_solution'
__v2_prog_syn_id = '[re.subn]:[modify-argument-supported_value(s)]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_log_string_is_empty'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_log_string_is_empty()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
