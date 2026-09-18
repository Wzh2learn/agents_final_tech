#!/usr/bin/env python3
"""UserPromptSubmit hook 路由脚本：根据 prompt 关键词，注入"建议使用某 skill"的提示。

工作方式:
    从 stdin 读取 hook 传入的 JSON（含 "prompt" 字段），
    按 routes.json 中每条路由的 keywords 做忽略大小写与空白的子串匹配，
    命中则把该路由的 hint 输出到 stdout（Claude Code/Qoder 会将其注入上下文），
    无命中则静默退出，不产生任何噪音。

用法（在 hook 命令中）:
    python skill_router.py --routes /path/to/routes.json

routes.json 结构见 assets/routes.example.json。
不依赖第三方库。
"""
import json
import os
import re
import sys


def _norm(s):
    """归一化：转小写并去除所有空白。

    中文用户输入的空格很随意（"重复的 skill" 与 "重复的skill" 应等价匹配），
    去空白后再做子串比较，可避免因空格差异导致的漏匹配。
    """
    return re.sub(r"\s+", "", s.lower())


def load_routes(routes_path):
    # 降级原则：路由表缺失/损坏时警告放行（不无声 fail-open，对齐 git-commit-guard 2026-07-29 评审修复纪律）
    if not routes_path:
        print("[skill-hook-trigger] ⚠️ 未指定 --routes 且脚本同目录无 routes.json，路由兜底静默失效，本次放行", file=sys.stderr)
        return []
    if not os.path.isfile(routes_path):
        print(f"[skill-hook-trigger] ⚠️ 路由表不存在：{routes_path}，路由兜底静默失效，本次放行", file=sys.stderr)
        return []
    try:
        with open(routes_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[skill-hook-trigger] ⚠️ 路由表解析失败：{routes_path}（{e}），本次放行", file=sys.stderr)
        return []
    return data.get("routes", [])


def read_prompt():
    """从 stdin 读取 hook 输入 JSON，取出 prompt 文本。"""
    try:
        raw = sys.stdin.read()
    except Exception:
        return ""
    if not raw.strip():
        return ""
    try:
        payload = json.loads(raw)
        return payload.get("prompt", "") or ""
    except json.JSONDecodeError:
        # 容错：若不是 JSON，就把原始输入当作 prompt
        return raw


def match_routes(prompt, routes):
    """返回命中的路由列表（按命中关键词数降序，取区分度更高者优先）。

    路由可设 "require_all": true，表示其 keywords 必须全部出现才算命中，
    用于把宽泛的单词组合成高精度规则、抑制误报。
    """
    norm_prompt = _norm(prompt)
    hits = []
    for r in routes:
        kws = [k for k in r.get("keywords", []) if k]
        matched = [k for k in kws if _norm(k) in norm_prompt]
        if not matched:
            continue
        if r.get("require_all") and len(matched) != len(kws):
            continue
        hits.append((len(matched), r, matched))
    hits.sort(key=lambda x: x[0], reverse=True)
    return hits


def main():
    routes_path = None
    max_hits = 3  # 最多注入几条建议，避免一次刷出过多提示形成噪音
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--routes" and i + 1 < len(argv):
            routes_path = argv[i + 1]
        if a == "--max" and i + 1 < len(argv):
            try:
                max_hits = max(1, int(argv[i + 1]))
            except ValueError:
                pass
    # 默认在脚本同目录找 routes.json
    if not routes_path:
        default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "routes.json")
        if os.path.isfile(default):
            routes_path = default

    routes = load_routes(routes_path)
    prompt = read_prompt()
    if not prompt or not routes:
        sys.exit(0)

    hits = match_routes(prompt, routes)
    if not hits:
        sys.exit(0)

    # 按 skill 去重：hits 已按命中数降序，保留每个 skill 命中最多的那条路由的 hint，
    # 并合并同一 skill 其它路由命中的关键词。这样为一个 skill 配多条路由变体时，
    # 不会重复刷屏；--max 也在去重后生效，限制的是"建议的 skill 数"而非原始路由数。
    agg = {}
    order = []
    for _, r, matched in hits:
        skill = r.get("skill", "(未命名)")
        if skill not in agg:
            agg[skill] = {"hint": r.get("hint", ""), "matched": list(matched)}
            order.append(skill)
        else:
            for k in matched:
                if k not in agg[skill]["matched"]:
                    agg[skill]["matched"].append(k)

    order = order[:max_hits]
    lines = ["[skill-hook-trigger] 依据本次请求的关键词，以下 skill 可能适用，请判断是否调用："]
    for skill in order:
        info = agg[skill]
        lines.append(f"- {skill}：{info['hint']}（命中关键词：{', '.join(info['matched'])}）")

    # stdout 内容会被注入到会话上下文
    print("\n".join(lines))
    sys.exit(0)


if __name__ == "__main__":
    main()
