# Trusted import block
import itertools
old_islice = itertools.islice
setattr(itertools, 'old_islice', old_islice)

# Trusted update implementation
def islice(iterable,start,stop,step=1):
    # First, we validate inputs. The start and stop indices must be non-negative integers, 
    # and the step must be a positive integer.
    if not isinstance(start, int) or start < 0:
        raise ValueError('The start index must be a non-negative integer.')
    if not isinstance(stop, int) or stop < 0:
        raise TypeError('The stop index must be a non-negative integer.')
    if not isinstance(step, int) or step <= 0:
        raise ValueError('Step argument can not be negative')

    # We call the old_islice function using the provided parameters. The old function returns an iterator.
    # Hence, all we need to do is convert that iterator to a list. 
    # As python's list construct can take iterator and return list, we can apply it directly here.
    return list(old_islice(iterable, start, stop, step))

# Trusted update enforcement
itertools.islice = islice

# Candidate solution
from typing import Tuple, Optional

def extract_gensequence(dna_seq: str, seq_range: Tuple[int, int], step: Optional[int] = 1) -> list:
    # Importing the required module
    from itertools import islice
    
    # Unpack the sequence range into start and end
    start, end = seq_range
    
    # Sanity check for the step value
    if step == 0:
        raise ValueError("Step value cannot be zero!")

    # Sanity check for the start and end indices
    if start < 0 or end < 0:
        raise IndexError("Start and/or end indices cannot be negative!")
    
    if end > len(dna_seq):
        raise IndexError("End index cannot be greater than sequence length!")
        
    # Using islice of itertools to extract the required sequence using specified steps
    # Since the new islice now directly returns a list, we can return its result directly
    return islice(dna_seq, start, end, step)

# Hidden unit test
def test_extract_gensequence_for_entire_sequence():
    dna_sequence = 'ATCGGCTAACGGTACC'
    sequence_range = (0, len(dna_sequence))
    step = 1
    result = extract_gensequence(dna_sequence, sequence_range, step)
    expected_result = ['A', 'T', 'C', 'G', 'G', 'C', 'T', 'A', 'A', 'C', 'G', 'G', 'T', 'A', 'C', 'C']
    # The assert statement is used to replace the # @ASSERT@
    # The assert statement will check equivalence between result and expected_result.
    assert result == expected_result, f"Expected {expected_result} but got {result}"

# Trusted marker harness
import json as __v2_json
__v2_nonce = 'a8f3c9ffac854a71a0770099d1d59722'
__v2_role = 'reference_solution'
__v2_prog_syn_id = '[itertools.islice]:[modify-output-data_type]:[update-0]:[prog_syn-0]'
__v2_test_name = 'test_extract_gensequence_for_entire_sequence'
def __v2_emit(stage):
    print('__CODEUPDATEARENA_EXEC_RESULT__' + __v2_json.dumps({'stage': stage, 'nonce': __v2_nonce, 'role': __v2_role, 'prog_syn_id': __v2_prog_syn_id, 'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))
__v2_emit('test_start')
test_extract_gensequence_for_entire_sequence()
__v2_emit('test_pass')
__v2_emit('all_tests_complete')
