#!/usr/bin/env python3
"""扫描一个 skills 目录，汇总每个 skill 的元数据，供合并分析使用。

用法:
    python scan_skills.py <skills目录> [--json]

输出每个 skill 的 name / description / SKILL.md 行数 / 资源文件清单。
默认输出为人类可读文本；加 --json 输出机器可读 JSON。
不依赖第三方库，自行解析 front matter。
"""
import json
import os
import sys


def parse_front_matter(text):
    """从 SKILL.md 文本中提取 YAML front matter 的 name 与 description。

    只做轻量解析：抓取第一个 --- ... --- 块内的 name/description 字段，
    支持单行值（含双引号包裹）。足够覆盖标准 SKILL.md 写法。
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fm = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key in ("name", "description"):
                fm[key] = val
    return fm


def list_resources(skill_dir):
    """列出 skill 目录下 scripts/references/assets 中的文件（相对路径）。"""
    resources = {}
    for sub in ("scripts", "references", "assets"):
        sub_dir = os.path.join(skill_dir, sub)
        if os.path.isdir(sub_dir):
            files = []
            for root, _, names in os.walk(sub_dir):
                for n in names:
                    rel = os.path.relpath(os.path.join(root, n), skill_dir)
                    files.append(rel)
            if files:
                resources[sub] = sorted(files)
    return resources


def scan(skills_root):
    results = []
    if not os.path.isdir(skills_root):
        return results
    for entry in sorted(os.listdir(skills_root)):
        skill_dir = os.path.join(skills_root, entry)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        with open(skill_md, "r", encoding="utf-8") as f:
            text = f.read()
        fm = parse_front_matter(text)
        results.append({
            "dir": entry,
            "path": skill_dir,
            "name": fm.get("name", "(缺失)"),
            "description": fm.get("description", "(缺失)"),
            "skill_md_lines": len(text.splitlines()),
            "resources": list_resources(skill_dir),
        })
    return results


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv[1:]
    if not args:
        print("用法: python scan_skills.py <skills目录> [--json]", file=sys.stderr)
        sys.exit(1)
    root = args[0]
    data = scan(root)

    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    print(f"扫描目录: {root}")
    print(f"发现 skill: {len(data)} 个\n")
    for s in data:
        print(f"● {s['name']}  (目录: {s['dir']}, {s['skill_md_lines']} 行)")
        print(f"  描述: {s['description']}")
        if s["resources"]:
            for sub, files in s["resources"].items():
                print(f"  {sub}/: {', '.join(files)}")
        print()


if __name__ == "__main__":
    main()
