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

# This function will split the genomic sequences that are separated by 'N', 'NN', 'NNN'
def parse_genomic_data(data_string):
    # Validation check - if the data_string is None or if it doesn't start and end with 'N', throw an exception
    if not data_string or data_string[0] != 'N' or data_string[-1] != 'N':
        raise Exception("Invalid input. String should start and end with 'N'.")
    
    # Validation check - if the data_string contains something else than 'A', 'T', 'C', 'G' and 'N', throw an exception
    for char in data_string:
        if char not in ['A', 'T', 'C', 'G', 'N']:
            raise Exception("Invalid input. String should only contain 'A', 'T', 'C', 'G' and 'N'.")
    
    # Use the updated re.split function with 'N' 'NN' 'NNN' as patterns
    # The new API expects an iterable of string patterns instead of a single pattern
    # So, we pass the patterns as a list ['N', 'NN', 'NNN']
    split_list = re.split(['N', 'NN', 'NNN'], data_string)
    
    # After splitting, the list can contain empty strings
    # We need to filter out these empty strings to get our final list of gene sequences
    # We use Python's built-in filter function for this
    return list(filter(None, split_list))

# Hidden unit test
def test_case_with_single_gene_enclosed_by_triple_Ns():
    # Define a genomic data string with a single gene separated by triple 'NNN'
    data_string = 'NNNATCNNN'
    result = parse_genomic_data(data_string)
    expected_result = ['ATC']
    # Add assertion statement
    assert result == expected_result, f"Expected {expected_result} but got {result}"

# Trusted marker harness
import json as __v2_json
__v2_nonce = '1399ec0f2ff740fd883f6d8c396235b2'
__v2_role = 'reference_solution'
__v2_prog_syn_id = '[re.split]:[modify-argument-semantics]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_case_with_single_gene_enclosed_by_triple_Ns'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_case_with_single_gene_enclosed_by_triple_Ns()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
