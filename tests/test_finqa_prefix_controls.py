"""Protect the matched-data comparison from silent supervision changes."""

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       'research/agent_frontier_portfolio_20261029'))
import finqa_prefix_controls as m


def example():
    rows = []
    cases = []
    for index, role in enumerate(('repair', 'closure')):
        points = [dict(target_position=3 + j, good_token=10 + j, bad_token=20 + j)
                  for j in range(3)]
        row = dict(pair_id='source/one', report='one.pdf', boundary_role=role,
                   prompt_token_count=3, input_ids=[1, 2, 3, 10, 11, 12],
                   labels=[-100, -100, -100, 10, 11, 12],
                   edit_contrasts={m.BASE_ARM: points},
                   assistant={'content': 'Original financial reasoning.'})
        rows.append(row)
        cases.append(dict(row_index=index, role=role, pair_id=row['pair_id'],
                          report=row['report'], negative_point=points[1],
                          wrong_completed_programs=['subtract(1, 2)'],
                          correct_continuations=[{'program': 'subtract(1, -2)'}]))
    data = dict(rows=rows, paired_rows=[[0, 1]], sources={'frozen': 'original'})
    diagnosis = dict(data_sha256='bound-data', cases=cases,
                     counts={'total_ambiguous_points': 2})
    return data, diagnosis


class PrefixControlTests(unittest.TestCase):
    def test_preserves_all_positive_data_and_couples_random_masks(self):
        data, diagnosis = example()
        before = copy.deepcopy(data)
        output, report = m.compile_controls(data, diagnosis, data_sha256='bound-data')
        self.assertEqual(data, before)
        for original, current in zip(data['rows'], output['rows']):
            left, right = copy.deepcopy(original), copy.deepcopy(current)
            del left['edit_contrasts'], right['edit_contrasts']
            self.assertEqual(left, right)
            for arm in (m.WITNESS_ARM, m.RANDOM_ARM):
                self.assertEqual(len(current['edit_contrasts'][arm]), 2)
            self.assertNotIn(original['edit_contrasts'][m.BASE_ARM][1],
                             current['edit_contrasts'][m.WITNESS_ARM])
        self.assertEqual(output['rows'][0]['edit_contrasts'], output['rows'][1]['edit_contrasts'])
        self.assertEqual(report['counts']['masked_points'], 2)
        self.assertEqual((output, report),
                         m.compile_controls(data, diagnosis, data_sha256='bound-data'))

    def test_empty_witness_set_keeps_every_site(self):
        data, diagnosis = example()
        diagnosis.update(cases=[], counts={'total_ambiguous_points': 0})
        output, report = m.compile_controls(data, diagnosis, data_sha256='bound-data')
        for row, old in zip(output['rows'], data['rows']):
            self.assertEqual(row['edit_contrasts'][m.WITNESS_ARM], old['edit_contrasts'][m.BASE_ARM])
        self.assertEqual(report['counts']['affected_groups'], 0)

    def test_all_sites_masked_preserves_ce_and_reports_empty_group(self):
        data, diagnosis = example()
        diagnosis['cases'] = []
        for i, row in enumerate(data['rows']):
            for point in row['edit_contrasts'][m.BASE_ARM]:
                diagnosis['cases'].append(dict(
                    row_index=i, role=row['boundary_role'], pair_id=row['pair_id'],
                    report=row['report'], negative_point=point,
                    wrong_completed_programs=['bad'], correct_continuations=[{'program': 'good'}]))
        diagnosis['counts']['total_ambiguous_points'] = 6
        output, report = m.compile_controls(data, diagnosis, data_sha256='bound-data')
        self.assertTrue(all(not r['edit_contrasts'][m.WITNESS_ARM] for r in output['rows']))
        self.assertEqual(output['rows'][0]['labels'], data['rows'][0]['labels'])
        self.assertEqual(report['counts']['empty_after_mask_groups'], 1)

    def test_rejects_stale_or_unpaired_or_unbound_witnesses(self):
        for mutation in ('digest', 'role', 'source', 'one_state', 'duplicate',
                         'point', 'label', 'witness', 'count', 'partition'):
            data, diagnosis = example()
            if mutation == 'digest': diagnosis['data_sha256'] = 'stale'
            elif mutation == 'role': diagnosis['cases'][0]['role'] = 'closure'
            elif mutation == 'source': diagnosis['cases'][0]['report'] = 'other.pdf'
            elif mutation == 'one_state': diagnosis['cases'].pop()
            elif mutation == 'duplicate': diagnosis['cases'].append(diagnosis['cases'][0])
            elif mutation == 'point': diagnosis['cases'][0]['negative_point'] = dict(target_position=0, good_token=1, bad_token=2)
            elif mutation == 'label': data['rows'][0]['labels'][4] = -100
            elif mutation == 'witness': diagnosis['cases'][0]['correct_continuations'] = []
            elif mutation == 'count': diagnosis['counts']['total_ambiguous_points'] = 3
            else: data['paired_rows'] = [[0, 0]]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                m.compile_controls(data, diagnosis, data_sha256='bound-data')


if __name__ == '__main__':
    unittest.main()
