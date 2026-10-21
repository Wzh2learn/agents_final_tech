# Trusted import block
import re
old_fullmatch = re.fullmatch
setattr(re, 'old_fullmatch', old_fullmatch)

# Trusted update implementation
def fullmatch(pattern, string, flags=0, endpos=None):
    # Check if 'endpos' is provided and if it's an instance of int
    # If not, the function will behave as the old re.fullmatch
    if endpos is not None:
        # Check if 'endpos' is outside the length of the string or negative
        # If so, raise ValueError
        if endpos < 0 or endpos > len(string):
            raise ValueError("'endpos' must be within the bounds of the string")
        else:
            # If 'endpos' is valid, match the pattern within the
            # substring of the string ending at 'endpos' using the old API
            # The substring is obtained using slicing 'string[:endpos]'
            return old_fullmatch(pattern, string[:endpos], flags)
    else:
        # If 'endpos' is not provided, behave like the old re.fullmatch
        return old_fullmatch(pattern, string, flags)

# Trusted update enforcement
re.fullmatch = fullmatch

# Candidate solution
import re
import typing

def check_patent_in_range(pattern: str, text: str, cutoff_point: int) -> typing.Optional[re.Match]:
    if cutoff_point < 0 or cutoff_point > len(text):
        raise ValueError("cutoff_point must be between 0 and the length of the string")
    
    # Use the updated re.fullmatch with endpos parameter
    match = re.fullmatch(pattern, text, endpos=cutoff_point)
    return match

# Hidden unit test
def test_check_patent_with_text_equals_cutoff_point():
    # test when text length equals cutoff point
    pattern = "PN[0-9]{5}"
    text = "PN12345"
    cutoff_point = 7
    result = check_patent_in_range(pattern, text, cutoff_point)
    expected_result = "PN12345"

    if result is not None and expected_result is not None:
        assert result.group() == expected_result, "The result does not match the expected result"
    else:
        assert result is expected_result, "The result does not match the expected result"

# Trusted marker harness
import json as __v2_json
__v2_nonce = '434f3f3778704b31853f755c036dccf9'
__v2_role = 'generated_solution'
__v2_prog_syn_id = '[re.fullmatch]:[modify-output-semantics]:[update-1]:[prog_syn-0]'
__v2_test_name = 'test_check_patent_with_text_equals_cutoff_point'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_check_patent_with_text_equals_cutoff_point()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
