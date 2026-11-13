"""Receipt/prefix boundaries for the real native checkpoint experiment."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/agent_frontier_portfolio_20261029'))
from checkpoint_pairs import continuation_cut


class PrefixBoundaryTests(unittest.TestCase):
    def test_preserves_private_replay_until_first_real_public_reply(self):
        messages=[dict(role='assistant',tool_calls=[dict(id='write',name='refuel_data')]),
            dict(role='tool',id='write',requestor='assistant',error=False,
                 content='{"new_data_refueling_gb":"2.0"}'),
            dict(role='assistant',content='Please test connectivity.'),
            dict(role='user',tool_calls=[dict(name='run_speed_test')],content=None),
            dict(role='tool',requestor='user',content='No Connection'),
            dict(role='user',content='There is still no connection.'),
            dict(role='assistant',tool_calls=[dict(name='transfer_to_human_agents')])]
        self.assertEqual(continuation_cut(messages),dict(action_index=0,receipt_index=1,prefix_length=6))

    def test_unrelated_or_failed_write_receipt_cannot_define_checkpoint(self):
        for changes in [dict(id='another-call'),dict(error=True),dict(content='{"new_data_refueling_gb":0}')]:
            receipt=dict(role='tool',id='write',requestor='assistant',error=False,
                         content='{"new_data_refueling_gb":"2.0"}')
            receipt.update(changes)
            messages=[dict(role='assistant',tool_calls=[dict(id='write',name='refuel_data')]),
                      receipt,dict(role='user',content='Continue.')]
            with self.assertRaises(ValueError):continuation_cut(messages)


if __name__=='__main__':unittest.main()
