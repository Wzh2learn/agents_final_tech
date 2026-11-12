"""Check public probe discrimination before it grades generated programs."""
import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029/corrective_program_cases.py'
spec = importlib.util.spec_from_file_location('corrective_program_cases', path)
cases = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cases)

PLOT = '''class View:
    def get_path(self):
        return self._original_path
'''
ITERABLE = '''def resolve_lookup_value(self, value, can_reuse, allow_joins):
    if hasattr(value, 'resolve_expression'):
        return value.resolve_expression(self, reuse=can_reuse, allow_joins=allow_joins)
    if isinstance(value, (list, tuple)):
        values = [self.resolve_lookup_value(x, can_reuse, allow_joins) for x in value]
        if isinstance(value, tuple):
            return type(value)(*values)
        return type(value)(values)
    return value
'''


@pytest.mark.parametrize('view', cases.VIEWS)
def test_plot_probe_retains_legacy_eager_default_counterexample(tmp_path, view):
    text, metadata = cases.source_view({'before_class': PLOT}, 'plot', view)
    path = tmp_path / 'view.py'
    projected, original = metadata['projected'], metadata['original']
    path.write_text(text)
    baseline = cases.probe(path, metadata)
    assert [row['passed'] for row in baseline['rows']] == [True, False, False]
    # A real historical difference: eager fallback reads a missing attribute.
    path.write_text(text.replace('return self.' + original,
                                 f"return getattr(self, '{projected}', self.{original})")
                    if view == 'canonical' else text.replace(
                        'return ' + cases.VIEWS[view][3] + '.' + original,
                        f"return getattr({cases.VIEWS[view][3]}, '{projected}', {cases.VIEWS[view][3]}.{original})"))
    eager = cases.probe(path, metadata)
    assert [row['passed'] for row in eager['rows']] == [True, True, False]
    receiver = 'self' if view == 'canonical' else cases.VIEWS[view][3]
    path.write_text(text.replace('return ' + receiver + '.' + original,
                                 f"return {receiver}.{projected} if hasattr({receiver}, '{projected}') else {receiver}.{original}"))
    assert cases.probe(path, metadata)['passed']


@pytest.mark.parametrize('view', cases.VIEWS)
def test_iterable_probe_accepts_both_executed_valid_repairs(tmp_path, view):
    text, metadata = cases.source_view({'before_function': ITERABLE}, 'iterable', view)
    path = tmp_path / 'resolver.py'
    path.write_text(text)
    assert [r['passed'] for r in cases.probe(path, metadata)['rows']] == [False, True, True, True]
    path.write_text(text.replace('return type(value)(*values)', 'return tuple(values)'))
    assert cases.probe(path, metadata)['passed']
    path.write_text(text.replace('return type(value)(*values)',
                                 "return type(value)(*values) if hasattr(value, '_fields') else type(value)(values)"))
    assert cases.probe(path, metadata)['passed']


def test_alias_capture_is_rejected():
    text = PLOT.replace('return self', '_active = 3\n        return self')
    with pytest.raises(ValueError, match='capture'):
        cases.source_view({'before_class': text}, 'plot', 'train_alias')


def test_probe_rejects_illegal_class_return_even_if_extracted_method_is_valid(tmp_path):
    text = '''class SourceCarrier:
    def get_path(self):
        return self._path2d if hasattr(self, '_path2d') else self._original_path
    return None
'''
    path = tmp_path / 'illegal.py'
    path.write_text(text)
    metadata = dict(kind='plot', class_name='SourceCarrier', method='get_path',
                    projected='_path2d', original='_original_path')
    with pytest.raises(SyntaxError, match='outside function'):
        cases.probe(path, metadata)


def test_public_attribute_error_identifies_the_represented_carrier(tmp_path):
    text, metadata = cases.source_view({'before_class': PLOT}, 'plot', 'train_alias')
    path = tmp_path / 'carrier.py'
    path.write_text(text)
    legacy = cases.probe(path, metadata)['rows'][-1]
    assert metadata['class_name'] in legacy['message']
    assert 'ProbeReceiver' not in legacy['message']
