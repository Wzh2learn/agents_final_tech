# Trusted import block
import re
old_split = re.split
setattr(re, 'old_split', old_split)

# Trusted update implementation
def split(patterns, string, maxsplit=0, flags=0):
    # If patterns is a single string, then directly call old_split
    if isinstance(patterns, str):
        return old_split(patterns, string, maxsplit, flags)

    # If patterns is not iterable (e.g. int, etc.), raise TypeError
    try:
        iter(patterns)
    except TypeError:
        raise TypeError("The 'patterns' argument must be an iterable of strings.")
        
    # Apply each pattern from patterns iteratively
    result = [string]
    for pattern in patterns:
        # Ensure pattern is a string
        if not isinstance(pattern, str):
            raise TypeError("Each pattern in 'patterns' must be a string.")
        # Split current substrings using current pattern
        temp = []
        for substring in result:
            temp.extend(old_split(pattern, substring, maxsplit, flags))
        result = temp
    return result

# Trusted update enforcement
re.split = split

# Candidate solution
import re

def parse_genomic_data(data_string):
    """
    Parse genomic sequence data by splitting on 'N', 'NN', or 'NNN' separators.
    
    Args:
        data_string (str): A string containing genomic sequence data with 'N' separators.
        
    Returns:
        list: A list of separated gene sequences.
    """
    # Split the string by one or more 'N' characters
    # The problem states that the data string has 'N' at both start and end
    # So we split by N+ and filter out empty strings
    parts = re.split(r'N+', data_string)
    # Filter out empty strings that result from leading/trailing separators
    result = [part for part in parts if part]
    return result

# Hidden unit test
def test_case_with_no_gene_sequence():
    # Define a genomic data string with no gene sequences, only 'N' separators
    data_string = 'NNNNNNNNNNN'
    result = parse_genomic_data(data_string)
    expected_result = []
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

# Trusted marker harness
import json as __v2_json
__v2_nonce = 'cfcb1063e0264f6395e6b81caa554790'
__v2_role = 'generated_solution'
__v2_prog_syn_id = '[re.split]:[modify-argument-semantics]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_case_with_no_gene_sequence'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_case_with_no_gene_sequence()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
