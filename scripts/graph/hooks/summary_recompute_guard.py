#!/usr/bin/env python3
# summary_recompute_guard.py — "声明摘要 ≠ 存储工件" 机械强制 (Hook Escalation 第 3 次触发)
# 三次实证: ① W2 payload_sha256 在 payload 收口前计算 (f1bf00b) ② W2 汇报写
# ports_touched=[8004] 而存储字段为 [] (36ab25f) ③ W1 汇报自指计数失真 (d4e749a)。
#
# 用法:
#   gen   <artifact> <claim=value>...   打印可粘贴的 SUMMARY-GUARD 收据块
#   check <md_file> [--warn-missing]    重读工件复算收据; 失配 -> exit 1
#
# 收据块格式 (嵌在 md 里):
#   <!-- SUMMARY-GUARD
#   artifact: logs/graph/eval/xxx.json
#   sha256: <hex>            (原始字节; 若文本件另给 sha256_lf)
#   claims:
#     payload.call_counter = 122
#     payload.t4.primary_separation_table["greedy"].mean_sep = 1.432574
#   END-SUMMARY-GUARD -->
import sys, os, json, hashlib, re

TOL = 5e-5  # 存储数字常四舍五入到 4 位小数 (抽验实证), 容差与之对齐

def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()

def file_shas(path):
    raw = open(path, "rb").read()
    out = {"raw": sha_bytes(raw)}
    lf = raw.replace(b"\r\n", b"\n")
    if lf != raw:
        out["lf"] = sha_bytes(lf)
    return out

def parse_path(p):
    # 支持 a.b.c 与 a["b.c"][0] 混写
    segs, i = [], 0
    while i < len(p):
        if p[i] == ".":
            i += 1; continue
        if p[i] == "[":
            j = p.index("]", i)
            inner = p[i + 1:j]
            if inner.startswith('"') and inner.endswith('"'):
                segs.append(inner[1:-1])
            else:
                segs.append(int(inner))
            i = j + 1
        else:
            j = i
            while j < len(p) and p[j] not in ".[":
                j += 1
            segs.append(p[i:j]); i = j
    return segs

def resolve(obj, path):
    cur = obj
    for s in parse_path(path):
        if isinstance(cur, list):
            cur = cur[int(s)]
        elif isinstance(cur, dict):
            if s not in cur:
                raise KeyError(s)
            cur = cur[s]
        else:
            raise TypeError("cannot descend into %r at %r" % (type(cur), s))
    return cur

def parse_claim_value(txt):
    t = txt.strip()
    if t == "true": return True
    if t == "false": return False
    if t.startswith('"') and t.endswith('"'): return t[1:-1]
    try: return int(t)
    except ValueError: pass
    try: return float(t)
    except ValueError: return t

def values_match(actual, expected):
    if isinstance(expected, bool) or isinstance(actual, bool):
        return actual == expected
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(actual - expected) <= TOL
    return str(actual) == str(expected)

def parse_blocks(text):
    blocks = []
    for m in re.finditer(r"<!--\s*SUMMARY-GUARD(.*?)END-SUMMARY-GUARD\s*-->", text, re.S):
        body = m.group(1)
        b = {"claims": []}
        in_claims = False
        for line in body.splitlines():
            ls = line.strip()
            if not ls: continue
            if ls.startswith("artifact:"):
                b["artifact"] = ls.split(":", 1)[1].strip(); in_claims = False
            elif ls.startswith("sha256_lf:"):
                b["sha256_lf"] = ls.split(":", 1)[1].strip(); in_claims = False
            elif ls.startswith("sha256:"):
                b["sha256"] = ls.split(":", 1)[1].strip(); in_claims = False
            elif ls.startswith("claims:"):
                in_claims = True
            elif in_claims and "=" in ls:
                k, v = ls.split("=", 1)
                b["claims"].append((k.strip(), parse_claim_value(v)))
        blocks.append(b)
    return blocks

def repo_root(anchor=None):
    # 优先从锚文件向上找 .git (hook 场景 = staged 文件), 兜底 git rev-parse
    import subprocess
    if anchor:
        d = os.path.dirname(os.path.abspath(anchor))
        while True:
            if os.path.isdir(os.path.join(d, ".git")):
                return d
            nd = os.path.dirname(d)
            if nd == d:
                break
            d = nd
    return subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True).stdout.strip()

def cmd_gen(argv):
    art = argv[0]
    claims = []
    for c in argv[1:]:
        k, v = c.split("=", 1)
        claims.append((k.strip(), v.strip()))
    root = repo_root(art)
    rel = os.path.relpath(art, root).replace(os.sep, "/") if os.path.isabs(art) else art
    shas = file_shas(art)
    # 先校验每条 claim 可解析 (防错收据入库)
    if art.endswith(".json"):
        obj = json.load(open(art, encoding="utf-8"))
        for k, v in claims:
            actual = resolve(obj, k)
            if not values_match(actual, parse_claim_value(v)):
                print("REFUSE: claim %s = %s but artifact says %r" % (k, v, actual), file=sys.stderr)
                return 2
    print("<!-- SUMMARY-GUARD")
    print("artifact: " + rel)
    print("sha256: " + shas["raw"])
    if "lf" in shas:
        print("sha256_lf: " + shas["lf"])
    if claims:
        print("claims:")
        for k, v in claims:
            print("  %s = %s" % (k, v))
    print("END-SUMMARY-GUARD -->")
    return 0

def cmd_check(argv):
    md = argv[0]
    warn_missing = "--warn-missing" in argv
    text = open(md, encoding="utf-8").read()
    blocks = parse_blocks(text)
    if not blocks:
        print("[summary-guard] %s: 无 SUMMARY-GUARD 块, 跳过" % md)
        return 0
    root = repo_root(md)
    fails = 0
    for b in blocks:
        art_rel = b.get("artifact", "")
        art = os.path.join(root, art_rel.replace("/", os.sep))
        if not os.path.exists(art):
            msg = "[summary-guard] WARN 工件不在本机 (GB10-only?): %s — 收据未复核" % art_rel
            print(msg)
            if not warn_missing:
                fails += 1
            continue
        shas = file_shas(art)
        ok_sha = b.get("sha256") in (shas.get("raw"),) or (b.get("sha256") == shas.get("raw"))
        lf_ok = ("sha256_lf" in b and b["sha256_lf"] == shas.get("lf")) or (b.get("sha256") == shas.get("lf"))
        if not (ok_sha or lf_ok):
            print("[summary-guard] FAIL sha 失配: %s (stored=%s actual_raw=%s)" % (art_rel, str(b.get("sha256"))[:16], shas["raw"][:16]))
            fails += 1
            continue
        if art.endswith(".json") and b["claims"]:
            obj = json.load(open(art, encoding="utf-8"))
            for k, expected in b["claims"]:
                try:
                    actual = resolve(obj, k)
                except Exception as e:
                    print("[summary-guard] FAIL 路径不可解析: %s (%s)" % (k, e))
                    fails += 1; continue
                if not values_match(actual, expected):
                    print("[summary-guard] FAIL 数字失配: %s = %r (收据声称 %r)" % (k, actual, expected))
                    fails += 1
    if fails:
        print("[summary-guard] %s: %d 项失配 — 摘要必须与存储工件一致, 请重读复算后再提交" % (md, fails))
        return 1
    print("[summary-guard] %s: %d 收据块复核通过" % (md, len(blocks)))
    return 0

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("gen", "check"):
        print(__doc__); return 2
    if sys.argv[1] == "gen":
        return cmd_gen(sys.argv[2:])
    return cmd_check(sys.argv[2:])

if __name__ == "__main__":
    sys.exit(main())