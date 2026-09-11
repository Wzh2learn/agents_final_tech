#!/usr/bin/env python3
# summary_recompute_guard.py — "声明摘要 ≠ 存储工件" 机械强制 (Hook Escalation 第 3 次触发)
# 三次实证: ① W2 payload_sha256 在 payload 收口前计算 (f1bf00b) ② W2 汇报写
# ports_touched=[8004] 而存储字段为 [] (36ab25f) ③ W1 汇报自指计数失真 (d4e749a)。
#
# 用法:
#   gen   <artifact> <claim=value>...   打印可粘贴的 SUMMARY-GUARD 收据块
#   check <md_file> [--warn-missing] [--staged]
#                                       重读工件复算收据; 失配 -> exit 1
#       --staged: 校验对象 = **待提交的 index blob** (git show :<path>), 不是工作树文件。
#                 pre-commit 必须走该口径, 否则「工作树合法 / staged 有缺陷」可绕过守卫
#                 (审计 F02: staged 与工作树对象漂移)。
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
HEX64 = re.compile(r"^[0-9a-f]{64}$")
# F02 修复 (2026-09-10, Loop A / TASK-20260910-A4A5A4W):
# 旧实现 file_shas() 在纯 LF 工件上不产出 "lf" 键 => shas.get("lf") is None;
# 收据缺哈希字段时 b.get("sha256") / b.get("sha256_lf") 同为 None,
# 于是 `None in (raw, None)` 恒真 => 缺字段 / 空字段 / 错哈希 全部放行 (改前实测 exit 0)。

def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()

def bytes_shas(raw):
    # 两口径**永远都在** (纯 LF 件 raw == lf), 使 None 没有碰撞空间。
    lf = raw.replace(b"\r\n", b"\n")
    return {"raw": sha_bytes(raw), "lf": sha_bytes(lf)}

def file_shas(path):
    return bytes_shas(open(path, "rb").read())

def git_blob_bytes(root, rel):
    """读 index 中的 staged blob 字节; 该路径不在 index -> None。"""
    import subprocess
    r = subprocess.run(["git", "--no-pager", "show", ":" + rel.replace(os.sep, "/")],
                       cwd=root, capture_output=True)
    return None if r.returncode != 0 else r.stdout

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
    for m in re.finditer(r"^\s*<!--\s*SUMMARY-GUARD(.*?)END-SUMMARY-GUARD\s*-->", text, re.M | re.S):  # RW-3: 行首锚定, 与 OPEN_MARKER 同步
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
    shas = bytes_shas(open(art, "rb").read())
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
    if shas["lf"] != shas["raw"]:
        print("sha256_lf: " + shas["lf"])
    if claims:
        print("claims:")
        for k, v in claims:
            print("  %s = %s" % (k, v))
    print("END-SUMMARY-GUARD -->")
    return 0

  # RW-3 修复 (2026-09-12, 侧线验收 RW-3): OPEN_MARKER 加**行首锚定** (re.M)。
  # 旧式 r"<!--\s*SUMMARY-GUARD" 不锚行首 => **散文里逐字提及该标记也被计为一个 opening**,
  # 而该文档并无真收据块 => openings(1) != blocks(0) => cmd_check 无条件 FAIL => 该文件永远无法提交。
  # 实测自伤案例: memory/THREADS.md 为说明「真收据块合计 0」而逐字写出该标记 (b52675f 埋入),
  # 导致其后两批台账均无法入库。前提已由侧线全库核验: docs/ (排除 archive) 24 份 md 中真收据块 11 个,
  # **开标记 11/11 全在行首、END 11/11 配对、行中开标记 0 个** => 行首锚定不误伤任何一份,
  # 且此后文档可以安全地在散文里讨论该标记。
  # **注意 (侧线实现细节提醒)**: 锚定必须**同时**施加于本 OPEN_MARKER 与 parse_blocks() 的块解析正则,
  # 否则 openings 与 blocks 会在另一方向上分叉 (块解析仍收行中块 => openings < blocks => 同样 FAIL)。
OPEN_MARKER = re.compile(r"^\s*<!--\s*SUMMARY-GUARD", re.M)


def check_block_shape(b, idx):
    """F02 修复: 收据块结构完整性 = 硬失败。旧实现缺 sha256 时以 None 撞空口径放行。"""
    errs = []
    if not b.get("artifact"):
        errs.append("收据块 #%d 缺 artifact 字段" % idx)
    sha = b.get("sha256")
    if sha is None:
        errs.append("收据块 #%d 缺 sha256 字段 (缺失不等于通过)" % idx)
    elif not isinstance(sha, str) or not HEX64.match(sha):
        errs.append("收据块 #%d sha256 非 64 位小写十六进制: %r" % (idx, sha))
    lf = b.get("sha256_lf")
    if lf is not None and (not isinstance(lf, str) or not HEX64.match(lf)):
        errs.append("收据块 #%d sha256_lf 非 64 位小写十六进制: %r" % (idx, lf))
    return errs


def verify_shas(b, shas):
    """两口径 (raw / LF 归一) 有效非空比对。返回 (ok, reason)。

    通过条件 (任一):
      A. sha256 == raw            —— 同检出侧原字节
      B. sha256 == lf             —— 收据在 LF 侧生成, 或纯 LF 件两口径同值
      C. sha256_lf 在位且 == lf   —— 收据在 CRLF 检出侧生成 (raw 为 CRLF 口径)
    若 sha256_lf 在位但 != lf, 一律 FAIL (声称的 LF 口径与实存不符)。
    """
    sha, lf_sha = b.get("sha256"), b.get("sha256_lf")
    if lf_sha is not None and lf_sha != shas["lf"]:
        return False, "sha256_lf 与实存 LF 口径失配 (stored=%s actual_lf=%s)" % (
            str(lf_sha)[:16], shas["lf"][:16])
    if sha in (shas["raw"], shas["lf"]):
        return True, ""
    if lf_sha is not None and lf_sha == shas["lf"]:
        return True, ""
    return False, "sha256 失配 (stored=%s actual_raw=%s actual_lf=%s)" % (
        str(sha)[:16], shas["raw"][:16], shas["lf"][:16])


def artifact_bytes(root, art_rel, use_index):
    """--staged 优先读 index blob (缺陷若已暂存则必须被拒), 否则回落工作树文件。"""
    if use_index:
        blob = git_blob_bytes(root, art_rel)
        if blob is not None:
            return blob
    path = os.path.join(root, art_rel.replace("/", os.sep))
    if os.path.isfile(path):
        return open(path, "rb").read()
    return None


def cmd_check(argv):
    md = argv[0]
    warn_missing = "--warn-missing" in argv
    use_index = "--staged" in argv
    root = repo_root(None if use_index else md)
    display = md
    if use_index:
        rel_md = md.replace(os.sep, "/").lstrip("./")
        blob = git_blob_bytes(root, rel_md)
        if blob is None:
            print("[summary-guard] FAIL 无法读取 staged blob: %s (校验对象缺失不等于通过)" % rel_md)
            return 1
        text = blob.decode("utf-8", errors="replace")
        display = rel_md
    else:
        text = open(md, encoding="utf-8").read()

    blocks = parse_blocks(text)
    openings = len(OPEN_MARKER.findall(text))
    if openings != len(blocks):
        print("[summary-guard] FAIL %s: 发现 %d 个 SUMMARY-GUARD 起始标记但只有 %d 个可解析块 "
              "(块格式错误 / 未闭合 / 字段不可解析 = 收据不可信)" % (display, openings, len(blocks)))
        return 1
    if not blocks:
        print("[summary-guard] %s: 无 SUMMARY-GUARD 块, 跳过" % display)
        return 0

    fails = 0
    skipped = 0
    for i, b in enumerate(blocks, 1):
        errs = check_block_shape(b, i)
        if errs:
            for e in errs:
                print("[summary-guard] FAIL %s: %s" % (display, e))
            fails += 1
            continue
        art_rel = b["artifact"]
        raw = artifact_bytes(root, art_rel, use_index)
        if raw is None:
            msg = ("[summary-guard] WARN 工件不在本机 (GB10-only?): %s — 收据未复核"
                   % art_rel) if warn_missing else \
                  ("[summary-guard] FAIL %s: 收据块 #%d 指向的工件不可读: %s" % (display, i, art_rel))
            print(msg)
            if not warn_missing:
                fails += 1
            skipped += 1
            continue
        ok, reason = verify_shas(b, bytes_shas(raw))
        if not ok:
            print("[summary-guard] FAIL %s 收据块 #%d: %s" % (display, i, reason))
            fails += 1
            continue
        if art_rel.endswith(".json") and b["claims"]:
            try:
                obj = json.loads(raw.decode("utf-8"))
            except Exception as e:
                print("[summary-guard] FAIL %s 收据块 #%d: 工件非合法 JSON, claims 无法复核 (%s)"
                      % (display, i, e))
                fails += 1
                continue
            for k, expected in b["claims"]:
                try:
                    actual = resolve(obj, k)
                except Exception as e:
                    print("[summary-guard] FAIL 路径不可解析: %s (%s)" % (k, e))
                    fails += 1
                    continue
                if not values_match(actual, expected):
                    print("[summary-guard] FAIL 数字失配: %s = %r (收据声称 %r)" % (k, actual, expected))
                    fails += 1
    if fails:
        print("[summary-guard] %s: %d 项失配 — 摘要必须与存储工件一致, 请重读复算后再提交" % (display, fails))
        return 1
    if skipped:
        print("[summary-guard] %s: %d 收据块, %d 已复核, %d 跳过未复核（工件不在本机）— 跳过不等于通过"
              % (display, len(blocks), len(blocks) - skipped, skipped))
    else:
        print("[summary-guard] %s: %d 收据块复核通过" % (display, len(blocks)))
    return 0

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("gen", "check"):
        print(__doc__); return 2
    if sys.argv[1] == "gen":
        return cmd_gen(sys.argv[2:])
    return cmd_check(sys.argv[2:])

if __name__ == "__main__":
    sys.exit(main())
