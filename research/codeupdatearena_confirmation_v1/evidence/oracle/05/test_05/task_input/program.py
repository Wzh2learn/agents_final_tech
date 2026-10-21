# Trusted import block
import re
old_match = re.match
setattr(re, 'old_match', old_match)

# Trusted update implementation
# Implementation for the new API function
def match(pattern, string, flags=re.IGNORECASE):
    # Leverage the old API function to achieve the functionality.
    # The difference here is that the default value of 'flags' changed to re.IGNORECASE
    # Other than that, it's behavior should remain the same as that of the old function.
    return old_match(pattern, string, flags)

# Trusted update enforcement
re.match = match

# Candidate solution
from typing import List
import re

def contains_phrase(email_list: List[str], phrase: str) -> List[bool]:
    # We will use the regular expression match method to check if the pattern (phrase) is in each of the strings (emails).
    # As the flags parameter is set to IGNORECASE by default, the phrase match becomes case-insensitive.

    # First verify that the given parameters are not Null.
    if email_list is None or phrase is None:
        raise ValueError("Error: Either 'email_list' or 'phrase' was None which is not allowed")
  
    # Now make a result list where we'll put whether each email contains the phrase or not.
    results = []

    for email in email_list:
        
        # If the pattern does not appear at the start of the string, 
        # match() will not match it, so we add '.*' at beginning and end of the pattern.
        pattern = f'.*{phrase}.*'
        
        # Check if the pattern exists in the email. Because flags are set to re.IGNORECASE, the match is case-insensitive.
        # Therefore, a match indicates that the email contains the phrase.
        if re.match(pattern, email):
            results.append(True)
        else: # If there is no match, the email does not contain the phrase.
            results.append(False)
    
    return results

# Hidden unit test
def test_contains_phrase_emails_with_whitespace():
    emails = [' hello world ', 'good morning ', ' hello']
    phrase = 'hello'
    result = contains_phrase(emails, phrase)
    expected_results = [True, False, True]
    for i in range(len(result)):
        assert result[i] == expected_results[i], f"For index {i}, expected {expected_results[i]} but got {result[i]}"

# Trusted marker harness
import json as __v2_json
__v2_nonce = '7954c67011544e52ac5130a41ee48320'
__v2_role = 'reference_solution'
__v2_prog_syn_id = '[re.match]:[modify-argument-default_value(s)]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_contains_phrase_emails_with_whitespace'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_contains_phrase_emails_with_whitespace()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
