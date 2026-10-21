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
    # If no lists of prices are provided, raise an exception
    if len(lists) == 0:
        raise Exception("No arguments provided")
    
    # If at least one argument is not a list, raise a TypeError
    for lst in lists:
        if not isinstance(lst, list):
            raise TypeError("All arguments must be lists")

    # If 'reverse' is set to True, return the prices in reverse order
    # Using itertools.chain function to chain all the lists.
    # We first reverse each list inside the list of lists and then pass them to itertools.chain function with reverse=True
    if reverse:
        return list(itertools.chain(*[lst[::-1] for lst in lists[::-1]], reverse=reverse))

    # If 'reverse' is set to False or not provided, return the prices in original order.
    # Using itertools.chain function to chain all the lists.
    return list(itertools.chain(*lists, reverse=reverse))

# Hidden unit test
def test_fetch_stock_prices_empty_lists():
    # Testing scenario with multiple empty lists of prices
    prices = [[], [], []]
    result = fetch_stock_prices(*prices)
    expected_result = []
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

test_fetch_stock_prices_empty_lists()
print('__CODEUPDATEARENA_EXEC_RESULT__' + '{"prog_syn_id":"[itertools.chain]:[add-argument-semantics]:[update-0]:[prog_syn-0]","role":"reference_solution","test_name":"test_fetch_stock_prices_empty_lists"}')
