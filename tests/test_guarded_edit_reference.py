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


ACCESSOR_BEFORE = '''class Source:
 def read_path(self):
  return self.original
 def project(self):
  self.projected = path_builder()
'''
ACCESSOR_AFTER = ACCESSOR_BEFORE.replace(
    '  return self.original',
    "  if hasattr(self, 'projected'):\n   return self.projected\n  return self.original")


def test_accessor_baseline_binds_distinct_roles_and_preserves_base_getter():
    schema = module.learn_accessor(ACCESSOR_BEFORE, ACCESSOR_AFTER)
    text = '''class Base:
 def read_path(self):
  return self.display
 def project(self):
  self.display = path_builder()
class Renamed(Base):
 def read_path(self):
  current = self
  return current.saved
 def project(self):
  self.display = path_builder()
'''
    changed, edits = module.bind_accessor(text, schema)
    assert len(edits) == 1 and edits[0]['class_name'] == 'Renamed'
    namespace = {}
    exec(changed, namespace)
    base = namespace['Base']()
    base.display = object()
    assert base.read_path() is base.display
    cls = namespace['Renamed']
    undrawn, drawn, legacy = cls(), cls(), cls()
    undrawn.saved = object()
    drawn.saved, drawn.display = object(), object()
    legacy.display = object()
    assert undrawn.read_path() is undrawn.saved
    assert drawn.read_path() is drawn.display
    assert legacy.read_path() is legacy.display


def test_accessor_baseline_abstains_on_ambiguous_producer_roles():
    schema = module.learn_accessor(ACCESSOR_BEFORE, ACCESSOR_AFTER)
    text = ACCESSOR_BEFORE.replace('self.projected = path_builder()',
                                   'self.projected = path_builder()\n  self.second = path_builder()')
    changed, edits = module.bind_accessor(text, schema)
    assert not edits and changed.decode() == text


def test_accessor_source_requires_the_observed_conditional_program():
    with pytest.raises(ValueError, match='observed lazy accessor'):
        module.learn_accessor(ACCESSOR_BEFORE, ACCESSOR_BEFORE.replace('self.original', '0'))
