"""CLI helpers for Claude Code to call via Bash.

Each subcommand outputs structured JSON to stdout.
Usage: python3 -m dream_engine.helpers <command> [args]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from .config import load_config, Config
from .storage import MemoryStore
from .collector import MemoryCollector
from .models import DreamResult, IdeaCandidate, ConceptNode
from .errors import DreamError


CONFIG_PATH = "config.yaml"


def _get_config(config_path: str = CONFIG_PATH) -> Config:
    cfg = load_config(config_path)
    # resolve storage paths relative to config file's directory
    config_dir = Path(config_path).resolve().parent
    if not Path(cfg.storage.memories_path).is_absolute():
        cfg.storage.memories_path = str(config_dir / cfg.storage.memories_path)
    if not Path(cfg.storage.dreams_dir).is_absolute():
        cfg.storage.dreams_dir = str(config_dir / cfg.storage.dreams_dir)
    raw_graph = cfg.storage.graph_path
    if not Path(raw_graph.replace("{namespace}", cfg.storage.namespace)).is_absolute():
        cfg.storage.graph_path = str(config_dir / raw_graph)
    return cfg


def _get_store(config: Config) -> MemoryStore:
    return MemoryStore(config.memories_path)


def cmd_ingest(args):
    config = _get_config(args.config)
    store = _get_store(config)
    collector = MemoryCollector(config, store)

    if args.path:
        p = Path(args.path)
        if p.is_file():
            nodes = collector.ingest_file(str(p))
        elif p.is_dir():
            nodes = collector.ingest_directory(str(p))
        else:
            print(json.dumps({"error": f"路径不存在: {args.path}"}))
            return
    else:
        nodes = collector.ingest_all()

    by_type: dict[str, int] = {}
    for n in nodes:
        by_type[n.source_type] = by_type.get(n.source_type, 0) + 1

    result = {
        "new_nodes": len(nodes),
        "total": store.count(),
        "by_type": by_type,
    }
    print(json.dumps(result, ensure_ascii=False))


def cmd_list_gists(args):
    config = _get_config(args.config)
    store = _get_store(config)
    gists = store.get_all_gists()
    print(json.dumps(gists, ensure_ascii=False))


def cmd_load_nodes(args):
    config = _get_config(args.config)
    store = _get_store(config)
    ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    nodes = store.get_nodes_by_ids(ids)
    result = [
        {
            "id": n.id,
            "content": n.content,
            "gist": n.gist,
            "source_type": n.source_type,
            "source_path": n.source_path,
            "tags": n.tags,
        }
        for n in nodes
    ]
    print(json.dumps(result, ensure_ascii=False))


def cmd_run_activation(args):
    import networkx as nx
    from .activation import SpreadingActivation, run_multi_round_dream

    config = _get_config(args.config)
    graph_path = Path(config.graph_path)
    if not graph_path.exists():
        print(json.dumps({"error": "图谱未构建，先运行 graph build"}))
        return

    data = json.loads(graph_path.read_text())
    graph = nx.node_link_graph(data)

    if graph.number_of_nodes() == 0:
        print(json.dumps({"error": "图谱为空"}))
        return

    sa = SpreadingActivation(graph, config)

    if args.seed == "random":
        seed_id = random.choice(list(graph.nodes))
    else:
        seed_id = args.seed
        if seed_id not in graph:
            print(json.dumps({"error": f"种子节点不存在: {seed_id}"}))
            return

    seed_name = graph.nodes[seed_id].get("name", seed_id[:8])

    round_paths = run_multi_round_dream(
        sa, seed_id,
        [{"name": r.name, "threshold": r.activation_threshold, "top_k": r.top_k}
         for r in config.dream.rounds],
    )

    result = {
        "seed_id": seed_id,
        "seed_name": seed_name,
        "rounds": {},
    }
    for rname, paths in round_paths.items():
        result["rounds"][rname] = [
            {"node_ids": path, "formatted": sa.format_path(path)}
            for path in paths
        ]

    print(json.dumps(result, ensure_ascii=False))


def cmd_save_concepts(args):
    import networkx as nx
    from .graph_builder import KnowledgeGraphConstructor

    config = _get_config(args.config)
    input_data = json.loads(Path(args.input).read_text())

    builder = KnowledgeGraphConstructor(config)
    concepts = []
    for raw in input_data:
        concept = ConceptNode(
            name=raw["name"],
            node_type=raw.get("type", "concept"),
            gist=raw.get("gist", ""),
            tags=raw.get("tags", []),
            source_memory_ids=raw.get("source_memory_ids", []),
        )
        concepts.append(concept)

    builder.add_concepts(concepts)
    builder.build_cooccurrence_edges()
    builder.save_graph()

    stats = builder.get_stats()
    print(json.dumps(stats, ensure_ascii=False))


def cmd_save_edge_decisions(args):
    import networkx as nx
    from .graph_builder import KnowledgeGraphConstructor

    config = _get_config(args.config)
    decisions = json.loads(Path(args.input).read_text())

    builder = KnowledgeGraphConstructor(config)
    builder.load_graph()
    builder.apply_edge_decisions(decisions)
    builder.save_graph()

    stats = builder.get_stats()
    print(json.dumps(stats, ensure_ascii=False))


def cmd_save_dream(args):
    from .output import save_dream_report

    config = _get_config(args.config)
    data = json.loads(Path(args.input).read_text())
    result = DreamResult.from_dict(data)
    json_path, md_path = save_dream_report(result, config)
    print(json.dumps({"json_path": json_path, "md_path": md_path}, ensure_ascii=False))


def cmd_rate(args):
    from .output import update_idea_rating
    from .feedback import apply_rating_feedback

    config = _get_config(args.config)
    if args.rating < 1 or args.rating > 5:
        print(json.dumps({"error": "评分必须在 1-5 之间"}))
        return

    # save rating to dream result file
    update_idea_rating(config, args.idea_id, args.rating)

    # apply Hebbian feedback to graph edges
    feedback_result = apply_rating_feedback(config, args.idea_id, args.rating)
    print(json.dumps(feedback_result, ensure_ascii=False))


def cmd_find_collisions(args):
    """Find semantically distant but potentially interesting node pairs for dreaming."""
    import re

    config = _get_config(args.config)
    store = _get_store(config)
    nodes = store.get_all()

    if len(nodes) < 6:
        print(json.dumps({"error": f"节点太少({len(nodes)}个)，至少需要6个"}))
        return

    num_groups = args.num

    def extract_keywords(text: str) -> set[str]:
        words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', text.lower()))
        stopwords = {'这个', '那个', '一个', '我们', '可以', '使用', '通过', '进行', '需要',
                     'the', 'and', 'for', 'this', 'that', 'with', 'from', 'not', 'are'}
        return words - stopwords

    node_kw = [(n, extract_keywords(n.content)) for n in nodes]

    # score all cross-type pairs by keyword distance
    # want: different source files + low keyword overlap + some shared context
    pairs = []
    for i in range(len(node_kw)):
        for j in range(i + 1, len(node_kw)):
            na, ka = node_kw[i]
            nb, kb = node_kw[j]
            if not ka or not kb:
                continue
            # must be from different source files
            if na.source_path == nb.source_path:
                continue
            overlap = len(ka & kb)
            union = len(ka | kb)
            jaccard = overlap / union if union else 0
            # want low overlap (distant) but 1-3 shared keywords (not random)
            if overlap < 1 or overlap > 10:
                continue
            if jaccard > 0.15:
                continue
            # bonus for cross source_type
            type_bonus = 1.5 if na.source_type != nb.source_type else 1.0
            score = (1 - jaccard) * overlap * type_bonus
            pairs.append((score, na, nb))

    pairs.sort(key=lambda x: x[0], reverse=True)

    # pick top groups, avoid reusing nodes
    used_ids = set()
    groups = []
    for score, na, nb in pairs:
        if na.id in used_ids or nb.id in used_ids:
            continue
        groups.append({
            "path": f"[{na.gist}] --?-→ [{nb.gist}]",
            "nodes": [
                {"id": na.id, "gist": na.gist, "source_type": na.source_type,
                 "content": na.content},
                {"id": nb.id, "gist": nb.gist, "source_type": nb.source_type,
                 "content": nb.content},
            ],
            "distance_score": round(score, 3),
        })
        used_ids.update([na.id, nb.id])
        if len(groups) >= num_groups:
            break

    print(json.dumps({"collisions": groups, "total_candidates": len(pairs)}, ensure_ascii=False))


def cmd_update_gists(args):
    config = _get_config(args.config)
    store = _get_store(config)
    gist_updates = json.loads(Path(args.input).read_text())

    updated = 0
    for entry in gist_updates:
        node_id = entry.get("id")
        gist = entry.get("gist")
        if node_id and gist:
            if store.update_node(node_id, {"gist": gist}):
                updated += 1

    print(json.dumps({"updated": updated, "total": len(gist_updates)}, ensure_ascii=False))


def cmd_consolidate(args):
    from .consolidation import run_nrem

    config = _get_config(args.config)
    stats = run_nrem(config)
    print(json.dumps(stats, ensure_ascii=False))


def cmd_status(args):
    import networkx as nx
    from .output import load_dream_results

    config = _get_config(args.config)
    store = _get_store(config)

    node_count = store.count()
    results = load_dream_results(config, limit=100)
    total_ideas = sum(len(r.ideas) for r in results)
    rated = sum(1 for r in results for i in r.ideas if i.user_rating is not None)

    graph_info = {"nodes": 0, "edges": 0, "built": False}
    graph_path = Path(config.graph_path)
    if graph_path.exists():
        try:
            data = json.loads(graph_path.read_text())
            G = nx.node_link_graph(data)
            graph_info = {
                "nodes": G.number_of_nodes(),
                "edges": G.number_of_edges(),
                "built": True,
            }
        except Exception:
            pass

    status = {
        "memory_nodes": node_count,
        "dream_sessions": len(results),
        "total_ideas": total_ideas,
        "rated_ideas": rated,
        "graph": graph_info,
    }
    print(json.dumps(status, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Dream Engine Helpers")
    parser.add_argument("--config", default=CONFIG_PATH)
    sub = parser.add_subparsers(dest="command")

    p_ingest = sub.add_parser("ingest")
    p_ingest.add_argument("--path", default=None)

    sub.add_parser("list-gists")

    p_load = sub.add_parser("load-nodes")
    p_load.add_argument("--ids", required=True)

    p_act = sub.add_parser("run-activation")
    p_act.add_argument("--seed", default="random")

    p_concepts = sub.add_parser("save-concepts")
    p_concepts.add_argument("--input", required=True)

    p_edges = sub.add_parser("save-edge-decisions")
    p_edges.add_argument("--input", required=True)

    p_dream = sub.add_parser("save-dream")
    p_dream.add_argument("--input", required=True)

    p_rate = sub.add_parser("rate")
    p_rate.add_argument("--idea-id", required=True)
    p_rate.add_argument("--rating", type=int, required=True)

    p_collisions = sub.add_parser("find-collisions")
    p_collisions.add_argument("--num", type=int, default=3)

    p_gists = sub.add_parser("update-gists")
    p_gists.add_argument("--input", required=True)

    sub.add_parser("consolidate")

    sub.add_parser("status")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    try:
        commands = {
            "ingest": cmd_ingest,
            "list-gists": cmd_list_gists,
            "load-nodes": cmd_load_nodes,
            "run-activation": cmd_run_activation,
            "save-concepts": cmd_save_concepts,
            "save-edge-decisions": cmd_save_edge_decisions,
            "save-dream": cmd_save_dream,
            "rate": cmd_rate,
            "find-collisions": cmd_find_collisions,
            "update-gists": cmd_update_gists,
            "consolidate": cmd_consolidate,
            "status": cmd_status,
        }
        commands[args.command](args)
    except DreamError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
