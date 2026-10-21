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
import re
from typing import List

# Patch re.match to use re.IGNORECASE by default
old_match = re.match
setattr(re, 'old_match', old_match)

def match(pattern, string, flags=re.IGNORECASE):
    return old_match(pattern, string, flags)

re.match = match

def contains_phrase(email_list: List[str], phrase: str) -> List[bool]:
    """
    Check if each email in the list contains the specific phrase (case-insensitive).
    
    Args:
        email_list: A list of email text strings.
        phrase: The specific phrase to search for.
        
    Returns:
        A list of boolean values indicating whether each email contains the phrase.
    """
    results = []
    for email in email_list:
        # Use re.match with case-insensitive flag
        if re.match(phrase, email, flags=re.IGNORECASE):
            results.append(True)
        else:
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
__v2_nonce = '63d3559c5354442cb044316ed39afa21'
__v2_role = 'generated_solution'
__v2_prog_syn_id = '[re.match]:[modify-argument-default_value(s)]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_contains_phrase_emails_with_whitespace'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_contains_phrase_emails_with_whitespace()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
