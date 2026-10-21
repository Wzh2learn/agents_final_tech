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

# Save the original split function
old_split = re.split
setattr(re, 'old_split', old_split)

def parse_genomic_data(data_string):
    """
    Parse genomic sequence data by splitting on 'N', 'NN', or 'NNN' separators.
    
    Args:
        data_string (str): A string representing genomic sequence data where
                           sequences are separated by 'N', 'NN', or 'NNN'.
                           Assumes 'N' at both start and end.
    
    Returns:
        list: A list of separated gene sequences.
    """
    # Use the updated re.split that accepts an iterable of patterns
    patterns = ['N', 'NN', 'NNN']
    
    # Split the string using the patterns
    # Note: The update description mentions that patterns are applied sequentially
    # However, for splitting on multiple delimiters, we typically want to split
    # on any of them. The standard re.split with a single pattern won't work
    # for multiple different length patterns directly.
    # 
    # Given the update description says "patterns are applied in a sequence",
    # this is unusual for split operations. Let's re-read carefully.
    # 
    # Actually, looking at the problem, we need to split by N, NN, or NNN.
    # The most robust way is to use a regex pattern that matches any of these.
    # But the update says re.split now accepts an iterable of patterns.
    # 
    # Let's implement based on the described behavior: patterns applied sequentially.
    # This is tricky because after splitting by 'N', the remaining parts might
    # still contain 'NN' or 'NNN' if we're not careful.
    #
    # However, a more standard interpretation for "split by multiple delimiters"
    # is to use a regex like 'N{1,3}' or '(N|NN|NNN)'.
    #
    # Given the ambiguity and the fact that the update description is somewhat
    # non-standard for split operations, let's use a regex pattern that matches
    # one or more N's (up to 3 as per the problem) to split.
    #
    # Actually, re-reading: "Each pattern in the 'patterns' iterable is used
    # independently to split the string." This suggests it might work like
    # re.split with a combined pattern.
    #
    # Let's use a regex pattern that matches N, NN, or NNN.
    # We can combine them into a single regex: 'N{1,3}' but that would also
    # match N, NN, NNN, NNNN, etc. The problem says only N, NN, or NNN.
    # So we should use '(N|NN|NNN)' or 'N{1,3}' if we assume max 3.
    #
    # Given the update says the pattern argument is now an iterable, let's
    # try to use it as described. But since the behavior is unclear, let's
    # use a standard regex approach that works for this problem.
    
    # Use regex to split by N, NN, or NNN
    # The pattern '(N|NN|NNN)' will match any of these
    result = re.split(r'(N|NN|NNN)', data_string)
    
    # Filter out empty strings and the separator patterns themselves
    gene_sequences = [seq for seq in result if seq and seq not in ['N', 'NN', 'NNN']]
    
    return gene_sequences

# Hidden unit test
def test_case_with_no_gene_sequence():
    # Define a genomic data string with no gene sequences, only 'N' separators
    data_string = 'NNNNNNNNNNN'
    result = parse_genomic_data(data_string)
    expected_result = []
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

# Trusted marker harness
import json as __v2_json
__v2_nonce = '3c65369b94834e64878ef7fb1ba0927a'
__v2_role = 'generated_solution'
__v2_prog_syn_id = '[re.split]:[modify-argument-semantics]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_case_with_no_gene_sequence'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_case_with_no_gene_sequence()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
