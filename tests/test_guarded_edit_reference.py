"""Safety checks for the restricted structural baseline's actual output."""
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / 'research/agent_frontier_portfolio_20261029/guarded_edit_reference.py'
spec = importlib.util.spec_from_file_location('guarded_edit_reference', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BEFORE = '''class Source:
 def __eq__(self, other):
  if not isinstance(other, Source):
   return False
  return self.value == other.value
'''
SCHEMA = module.learn(BEFORE, BEFORE.replace('return False', 'return NotImplemented'))


@pytest.mark.parametrize('body', [
    'if not isinstance(rhs, Target):\n   return False\n  return self.value == rhs.value',
    'if isinstance(rhs, Target):\n   return self.value == rhs.value\n  return False',
    'return isinstance(rhs, self.__class__) and self.value == rhs.value',
])
def test_parameterized_type_guard_preserves_real_inequality(body):
    text = 'class Target:\n def __eq__(self, rhs):\n  ' + body + '\n'
    changed, edits = module.bind(text, SCHEMA)
    assert len(edits) == 1
    namespace = {}
    exec(changed, namespace)
    cls = namespace['Target']
    left, same, different = cls(), cls(), cls()
    left.value = same.value = 4
    different.value = 9
    assert left.__eq__(object()) is NotImplemented
    assert left.__eq__(same) is True
    assert left.__eq__(different) is False


def test_shared_false_return_is_not_replaced_without_a_type_proof():
    text = '''class Target:
 def __eq__(self, rhs):
  if isinstance(rhs, Target):
   if self.value == rhs.value:
    return True
  return False
'''
    changed, edits = module.bind(text, SCHEMA)
    assert not edits and changed.decode() == text


def test_source_with_two_changed_returns_does_not_fit_one_edit_schema():
    before = BEFORE.replace('return self.value == other.value', 'return False')
    with pytest.raises(AssertionError, match='one exact'):
        module.learn(before, before.replace('return False', 'return NotImplemented'))
