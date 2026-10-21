# Trusted import block
import itertools
old_chain = itertools.chain
setattr(itertools, 'old_chain', old_chain)

# Trusted update implementation
def chain(*iterables, reverse=False):
    # If reverse is true, reverse the order of iterables
    if reverse:
        iterables = iterables[::-1]
    # Use the old_chain function to chain the iterables
    return old_chain(*iterables)

# Trusted update enforcement
itertools.chain = chain

# Candidate solution
import itertools

def fetch_stock_prices(*lists, reverse=False):
    """
    Fetch stock prices from multiple lists in either original or reverse order.
    
    Args:
        *lists: Variable number of lists containing stock prices
        reverse: Boolean flag to determine traversal order (default False)
    
    Returns:
        A list of all stock prices in the desired order
    """
    # Flatten all lists into a single sequence
    all_prices = list(itertools.chain.from_iterable(lists))
    
    # Return in reverse order if requested
    if reverse:
        return all_prices[::-1]
    else:
        return all_prices

# Hidden unit test
def test_fetch_stock_prices_empty_lists():
    # Testing scenario with multiple empty lists of prices
    prices = [[], [], []]
    result = fetch_stock_prices(*prices)
    expected_result = []
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

test_fetch_stock_prices_empty_lists()
print('__CODEUPDATEARENA_EXEC_RESULT__' + '{"prog_syn_id":"[itertools.chain]:[add-argument-semantics]:[update-0]:[prog_syn-0]","role":"generated_solution","test_name":"test_fetch_stock_prices_empty_lists"}')
