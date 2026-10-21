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
    # Pattern to match an IP address: 4 groups of 1-3 digits separated by dots
    ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    
    # Use re.subn to replace only the first occurrence
    result, count = re.subn(ip_pattern, mask, log_string, count=1)
    
    return result

# Hidden unit test
def test_mask_is_number():
    log_string = '204.120.0.15 made a request to server'
    # Case where number is used as a mask, should still function as expected.
    mask = '1234567890'
    result = mask_first_ip(log_string, mask)
    expected_result = '1234567890 made a request to server'
    # For comparing the strings after replacement, we can directly use `assert` statement.
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

# Trusted marker harness
import json as __v2_json
__v2_nonce = 'b3b8c434acda419ba76fd014cf31e1a6'
__v2_role = 'generated_solution'
__v2_prog_syn_id = '[re.subn]:[modify-argument-supported_value(s)]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_mask_is_number'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_mask_is_number()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
