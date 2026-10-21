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
    """
    Replaces the first occurrence of any IP address in the log with the mask string.
    
    An IP address is defined as a sequence of 4 groups separated by dots (.) where
    each group consists of 1 to 3 digits.
    
    Args:
        log_string: The input log string.
        mask: The string to replace the first IP address with.
        
    Returns:
        The log string with the first IP address replaced by the mask.
    """
    # Pattern to match an IP address: 4 groups of 1-3 digits separated by dots
    ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    
    # Use re.subn to replace the first occurrence (count=1 is default in updated version)
    result, count = re.subn(ip_pattern, mask, log_string, count=1)
    
    return result

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
__v2_nonce = '4d84e1b626cb44b98f0708e9c0c4936c'
__v2_role = 'generated_solution'
__v2_prog_syn_id = '[re.subn]:[modify-argument-supported_value(s)]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_log_string_is_empty'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_log_string_is_empty()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
