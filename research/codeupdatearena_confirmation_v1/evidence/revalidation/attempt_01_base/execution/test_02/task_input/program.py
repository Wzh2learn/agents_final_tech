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
def test_same_ip_multiple_occurrences():
    log_string = '204.120.0.15 made a request. Next, 204.120.0.15 tried to connect'
    # The same IP appearing twice but again we mask only the first one.
    mask = 'XXX.XXX.XXX.XXX'
    result = mask_first_ip(log_string, mask)
    expected_result = 'XXX.XXX.XXX.XXX made a request. Next, 204.120.0.15 tried to connect'
    assert result == expected_result, "Expected output does not match the result."

# Trusted marker harness
import json as __v2_json
__v2_nonce = '891b8691bb0641be87e2a01c8dcc5186'
__v2_role = 'generated_solution'
__v2_prog_syn_id = '[re.subn]:[modify-argument-supported_value(s)]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_same_ip_multiple_occurrences'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_same_ip_multiple_occurrences()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
