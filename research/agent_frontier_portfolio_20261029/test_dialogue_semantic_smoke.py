import unittest

try:
    from .dialogue_semantic_smoke import inspect_graph, unreachable_node_ids, choice_shape_check
except ImportError:
    from dialogue_semantic_smoke import inspect_graph, unreachable_node_ids, choice_shape_check


class DialogueSemanticSmokeTest(unittest.TestCase):
    def test_valid_minimal_graph(self):
        graph = {"nodes": [{"type": "choice", "text": "I seek shelter"},
                           {"type": "line", "text": "I will leave"}],
                 "edges": [{"to": "Welcome"}, {"to": "Exit"}]}
        self.assertEqual(inspect_graph(graph), [])

    def test_missing_choice_does_not_pass(self):
        graph = {"nodes": [{"type": "line", "text": "I seek shelter; I will leave"}],
                 "edges": [{"to": "Welcome"}, {"to": "Exit"}]}
        self.assertIn("missing_choice_node", inspect_graph(graph))

    def test_missing_target_and_malformed(self):
        self.assertIn("missing_nodes_or_edges", inspect_graph({}))
        self.assertIn("missing_choice_target:Exit", inspect_graph({"nodes": [], "edges": []}))

    def test_reachable_end_and_unreachable_cycle(self):
        graph = {"nodes": [{"id": n} for n in ("Start", "End", "Lost")],
                 "edges": [{"from": "Start", "to": "End"}, {"from": "Lost", "to": "Lost"}]}
        self.assertEqual(unreachable_node_ids(graph), ["Lost"])

    def test_choice_shapes_are_bound_to_node_identity(self):
        graph = {"nodes": [{"id": "a", "type": "choice"}, {"id": "b", "type": "line"}]}
        result = choice_shape_check(graph, '"a" [shape=diamond, label="A"];\n"b" [shape=box];')
        self.assertEqual(result["choice_count"], 1)
        self.assertEqual(result["missing_choice_diamonds"], [])
        self.assertEqual(result["nonchoice_diamonds"], [])
        wrong = choice_shape_check(graph, '"b" [shape=diamond];')
        self.assertEqual(wrong["missing_choice_diamonds"], ["a"])
        self.assertEqual(wrong["nonchoice_diamonds"], ["b"])


if __name__ == "__main__":
    unittest.main()
