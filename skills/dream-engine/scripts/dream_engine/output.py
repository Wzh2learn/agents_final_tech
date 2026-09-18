from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import Config
from .models import DreamResult, IdeaCandidate


def _render_scores(idea: IdeaCandidate) -> str:
    """Render multi-dimensional scores as a visual bar."""
    dims = [
        ("新颖", idea.score_novelty),
        ("可行", idea.score_feasibility),
        ("真实", idea.score_soundness),
        ("惊喜", idea.score_surprise),
        ("落地", idea.score_applicability),
    ]
    has_scores = any(v > 0 for _, v in dims)
    if not has_scores:
        return ""

    lines = ["", "**多维评分**：", ""]
    for label, score in dims:
        bar_len = int(score * 10)
        bar = "█" * bar_len + "░" * (10 - bar_len)
        lines.append(f"  {label} {bar} {score:.1f}")
    if idea.score_rationale:
        lines.append("")
        lines.append(f"  > {idea.score_rationale}")
    lines.append("")
    return "\n".join(lines)


def _avg_score(idea: IdeaCandidate) -> float:
    """Average of non-zero multi-dimensional scores."""
    scores = [idea.score_novelty, idea.score_feasibility,
              idea.score_soundness, idea.score_surprise,
              idea.score_applicability]
    valid = [s for s in scores if s > 0]
    return sum(valid) / len(valid) if valid else 0.0


def render_dream_report(result: DreamResult, config: Config) -> str:
    """Render a DreamResult as Markdown in inverted-pyramid format."""
    ts = result.timestamp.strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# 🌙 做梦报告 {ts}",
        f"> 本轮处理 {result.total_nodes_processed} 个节点，"
        f"产出 {len(result.ideas)} 个 idea，"
        f"耗时 {result.duration_seconds:.1f}s，"
        f"LLM 调用 {result.llm_calls} 次。",
        "",
    ]

    scored_ideas = sorted(
        ((idea, _avg_score(idea)) for idea in result.ideas),
        key=lambda x: x[1], reverse=True,
    )
    for i, (idea, avg) in enumerate(scored_ideas, 1):
        if avg < 0.5:
            confidence_tag = "⚠️低置信"
        elif idea.confidence == "engineering_only":
            confidence_tag = "🔧工程优化"
        elif idea.confidence == "high":
            confidence_tag = "⭐高置信"
        else:
            confidence_tag = "🎲高风险高收益"

        is_weak = avg < 0.5

        if is_weak:
            lines.append(f"<details>")
            lines.append(f"<summary>💡 Idea {i}：{idea.title} [{confidence_tag}] (avg={avg:.2f})</summary>")
            lines.append("")

        if not is_weak:
            lines.append(f"## 💡 Idea {i}：{idea.title} [{confidence_tag}]")
        lines.append(f"**一句话**：{idea.insight or idea.title}")
        lines.append("")

        # 层2: 可读摘要
        if idea.readable_abstract:
            lines.append("### 📖 通俗解读")
            lines.append("")
            lines.append(idea.readable_abstract)
            lines.append("")

        # 层2: 示意图/例子
        if idea.illustration:
            lines.append("### 🎨 示意图")
            lines.append("")
            lines.append("```")
            lines.append(idea.illustration)
            lines.append("```")
            lines.append("")

        # 多维评分
        scores_md = _render_scores(idea)
        if scores_md:
            lines.append(scores_md)

        lines.append("<details>")
        lines.append("<summary>展开论文骨架 + 验证方案</summary>")
        lines.append("")
        lines.append(f"**Problem**: {idea.problem}")
        lines.append("")
        lines.append(f"**Insight**: {idea.insight}")
        lines.append("")
        lines.append(f"**Method**: {idea.method}")
        lines.append("")
        lines.append(f"**Expected Result**: {idea.expected_result}")
        lines.append("")
        lines.append(f"**最强反对者**: {idea.strongest_objection}")
        lines.append("")
        lines.append(f"**最小验证实验**: {idea.min_experiment}")
        lines.append("")
        if idea.dream_scene:
            lines.append(f"**梦境场景**: {idea.dream_scene}")
            lines.append("")
        lines.append(f"**联想路径**: {' → '.join(idea.dream_path)}")
        lines.append("")
        lines.append("</details>")
        lines.append("")
        lines.append(f"<!-- idea_id: {idea.id} | 用 /dream explore {idea.id[:8]} 深入探索 -->")
        lines.append("")

        if is_weak:
            lines.append("</details>")
            lines.append("")

    return "\n".join(lines)


def save_dream_report(result: DreamResult, config: Config) -> tuple[str, str]:
    """Save dream result as both JSON and Markdown. Returns (json_path, md_path)."""
    dreams_dir = Path(config.storage.dreams_dir)
    dreams_dir.mkdir(parents=True, exist_ok=True)

    ts = result.timestamp.strftime("%Y%m%d_%H%M%S")

    json_path = dreams_dir / f"dream_{ts}.json"
    json_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md_path = dreams_dir / f"dream_{ts}.md"
    md_path.write_text(
        render_dream_report(result, config),
        encoding="utf-8",
    )

    return str(json_path), str(md_path)


def load_dream_results(config: Config, limit: int = 10) -> list[DreamResult]:
    """Load recent dream results from disk, newest first."""
    dreams_dir = Path(config.storage.dreams_dir)
    if not dreams_dir.exists():
        return []

    json_files = sorted(dreams_dir.glob("dream_*.json"), reverse=True)[:limit]
    results = []
    for f in json_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        results.append(DreamResult.from_dict(data))
    return results


def update_idea_rating(config: Config, idea_id: str, rating: int) -> bool:
    """Find and update a specific idea's rating in saved dream results."""
    dreams_dir = Path(config.storage.dreams_dir)
    if not dreams_dir.exists():
        return False

    for json_file in sorted(dreams_dir.glob("dream_*.json"), reverse=True):
        data = json.loads(json_file.read_text(encoding="utf-8"))
        modified = False
        for idea_data in data.get("ideas", []):
            if idea_data.get("id") == idea_id:
                idea_data["user_rating"] = rating
                modified = True
                break
        if modified:
            json_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            result = DreamResult.from_dict(data)
            md_path = json_file.with_suffix(".md")
            md_path.write_text(
                render_dream_report(result, config),
                encoding="utf-8",
            )
            return True
    return False
