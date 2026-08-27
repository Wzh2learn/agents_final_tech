# -*- coding: utf-8 -*-
# K2 / 小 B 章节配图生成（侧线车道, 2026-08-27 夜）
# 数据源: checkpoint_discrimination_tables_v2.json @34c93ab + k2_ms_bc_analysis.json @711f315
# schema 溯源: docs/experiments/2026-08-27_blind_cone_chapter_skeleton.md 图清单三张 + MS/CI/BC 两张
import json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', '..', '..', 'logs', 'graph', 'eval')
OUT = HERE
os.makedirs(OUT, exist_ok=True)

d = json.load(open(os.path.join(DATA, 'checkpoint_discrimination_tables_v2.json'), encoding='utf-8'))
k = json.load(open(os.path.join(DATA, 'k2_ms_bc_analysis.json'), encoding='utf-8'))
by_type = d['by_type']
xw = d['patent_crosswalk']
props = d['properties']

# 专利四型 -> 六类分组（结构型无注入, 不出带）
groups = {}
for gname, g in xw.items():
    for t in g.get('types', []):
        groups[t] = gname
GROUP_COLORS = {'别名型': '#e8f0fe', '列名型': '#fde8e8', '类型型': '#e6f4ea'}
TYPE_ZH = {'alias_variant': '别名变体', 'mixed_lang': '中英混写', 'ocr_similar': 'OCR 形近',
           'prefix_noise': '前缀噪声', 'unit_suffix': '单位后缀', 'date_variant': '日期变体'}

def vis_rate(t): return by_type[t]['visibility_rate']
order = sorted(by_type.keys(), key=vis_rate, reverse=True)

# ---------- 图 1 · 专利四型 × 六类判别谱 ----------
fig, ax = plt.subplots(figsize=(8.6, 4.6))
xs = list(range(len(order)))
i = 0
while i < len(order):
    j = i
    while j + 1 < len(order) and groups.get(order[j+1]) == groups.get(order[i]):
        j += 1
    g = groups.get(order[i])
    if g in GROUP_COLORS:
        ax.axvspan(i - 0.45, j + 0.45, color=GROUP_COLORS[g], zorder=0)
        ax.text((i + j) / 2, 1.10, g, ha='center', fontsize=9, color='#555555')
    i = j + 1
rates = [vis_rate(t) for t in order]
ns = [by_type[t]['n_injections'] for t in order]
bars = ax.bar(xs, rates, width=0.62, color='#3b6fd4', zorder=3)
for b, r, n in zip(bars, rates, ns):
    ax.text(b.get_x() + b.get_width()/2, r + 0.02, f'{r:.2f}\n(n={n})', ha='center', va='bottom', fontsize=8.5)
ax.axhline(props['discrimination']['rate'], color='#c0392b', ls='--', lw=1.2, zorder=2)
ax.text(len(order)-0.45, props['discrimination']['rate'] + 0.015,
        f"表级判别率 {props['discrimination']['rate']*100:.1f}%（参考线）", color='#c0392b', fontsize=8.5, ha='right')
ax.set_xticks(xs); ax.set_xticklabels([TYPE_ZH[t] for t in order])
ax.set_ylim(0, 1.20); ax.set_ylabel('注入级可见率')
ax.set_title('六类表头漂移的注入级判别率与专利四型分组（n=118 注入, 95 表）')
ax.spines[['top','right']].set_visible(False)
fig.text(0.5, -0.02, 'OCR 形近类塌缩至 0（13/13 静默吸收）构成盲区方向; 数据: checkpoint_discrimination_tables_v2.json @34c93ab',
         ha='center', fontsize=7.5, color='#777777')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig1_discrimination_spectrum.png'), bbox_inches='tight')
plt.close(fig)

# ---------- 图 2 · 吸收机制分解（堆叠） ----------
fig, ax = plt.subplots(figsize=(8.6, 4.6))
t0 = [by_type[t]['match_tiers'].get('0', 0) for t in order]
t1 = [by_type[t]['match_tiers'].get('1', 0) for t in order]
t2 = [by_type[t]['match_tiers'].get('2', 0) for t in order]
ax.bar(xs, t0, width=0.62, label='可见（未吸收）', color='#3b6fd4')
ax.bar(xs, t1, width=0.62, bottom=t0, label='编辑距离=1 兜底吸收', color='#e67e22')
b2 = [a+b for a,b in zip(t0,t1)]
ax.bar(xs, t2, width=0.62, bottom=b2, label='包含(match_tier=2) 吸收', color='#c0392b')
for xi, a, b, c in zip(xs, t0, t1, t2):
    ax.text(xi, a+b+c+0.6, str(a+b+c), ha='center', fontsize=8.5, color='#333333')
ax.set_xticks(xs); ax.set_xticklabels([TYPE_ZH[t] for t in order])
ax.set_ylabel('注入数'); ax.set_ylim(0, max(a+b+c for a,b,c in zip(t0,t1,t2))*1.22)
ax.set_title('判别失败的机制分解：吸收全部经匹配层发生（OCR 形近 13/13 集中于兜底层）')
ax.legend(fontsize=8.5, frameon=False); ax.spines[['top','right']].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig2_absorption_mechanism.png'), bbox_inches='tight')
plt.close(fig)

# ---------- 图 3 · 三性质复现表（树臂 × 表臂） ----------
fig, ax = plt.subplots(figsize=(8.2, 3.4)); ax.axis('off')
rows = [
    ['判别', '9/9 判别（mutant 臂）', '75 of 95 = 78.95%'],
    ['局部', '75 of 95 PASS', '95 of 95 PASS'],
    ['零漂移', '95 of 95 PASS', '95 of 95 PASS + 独立重跑复现'],
    ['规模', '检查点树 95 mutant', '表头漂移 95 表 / 118 注入'],
]
tbl = ax.table(cellText=rows, colLabels=['性质', '树臂（08-19, checkpoint 树 mutant）', '表臂（08-26, 表头漂移注入）'],
               loc='center', cellLoc='center')
tbl.auto_set_font_size(False); tbl.set_fontsize(9.5); tbl.scale(1, 1.7)
for (r, c), cell in tbl.get_celld().items():
    if r == 0:
        cell.set_facecolor('#2f4b7c'); cell.set_text_props(color='white')
    elif c == 0:
        cell.set_facecolor('#eef2f8')
    cell.set_edgecolor('#c9d4e4')
ax.set_title('K2 v1 协议跨臂移植：三性质在两个注入臂分别成立（判据框架同一, 样本规模 +1 数量级）', fontsize=10.5, pad=14)
fig.text(0.5, 0.02, '溯源: checkpoint_discrimination_report_20260819.json（归档）+ checkpoint_discrimination_tables_v2.json properties @34c93ab',
         ha='center', fontsize=7.5, color='#777777')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig3_three_properties_table.png'), bbox_inches='tight')
plt.close(fig)

# ---------- 图 4 · MS + bootstrap CI（forest）+ 配对差 ----------
ms = k['mutation_score']; bd = ms['paired_bootstrap_type_diffs']
fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2), gridspec_kw={'width_ratios': [1, 1.15]})
ax = axes[0]
items = [('表级（主口径）\n75/95, n=95', ms['table_level_primary']),
         ('注入级（参考）\n96/118, n=118', ms['injection_level'])]
for i, (lab, m) in enumerate(items):
    lo, hi = m['ci95_boot']
    ax.errorbar(m['ms'], i, xerr=[[m['ms']-lo], [hi-m['ms']]], fmt='o', color='#2f4b7c',
                capsize=5, capthick=1.4, lw=1.6, ms=6)
    ax.text(hi+0.012, i, f"{m['ms']*100:.1f}% [{lo*100:.1f}, {hi*100:.1f}]", va='center', fontsize=8.5)
ax.set_yticks([0,1]); ax.set_yticklabels([lab for lab,_ in items], fontsize=9)
ax.set_xlim(0.55, 1.05); ax.set_ylim(-0.5, 1.5)
ax.axvline(0.7895, color='#999999', ls=':', lw=1)
ax.set_title('Mutation Score（bootstrap 2000, seed=20260827）', fontsize=10)
ax.spines[['top','right']].set_visible(False); ax.set_xlabel('MS 点估计与 95% CI')
ax = axes[1]
pitems = list(bd.items())
for i, (name, m) in enumerate(pitems):
    lo, hi = m['ci95']
    sig = not (lo <= 0 <= hi)
    ax.errorbar(m['point_diff'], i, xerr=[[m['point_diff']-lo], [hi-m['point_diff']]],
                fmt='s' if sig else 'o', color='#c0392b' if sig else '#888888', capsize=5, capthick=1.4, lw=1.6, ms=6)
    ax.text(max(hi, m['point_diff'])+0.03, i, f"{m['point_diff']:+.3f}" + ('  显著' if sig else '  n.s.'), va='center', fontsize=8.5)
ax.axvline(0, color='#333333', lw=0.9)
ax.set_yticks(list(range(len(pitems)))); ax.set_yticklabels([n for n,_ in pitems], fontsize=9)
ax.set_ylim(-0.5, len(pitems)-0.5); ax.set_xlim(-0.85, 0.85)
ax.set_title('专利三型可见率配对差（表级配对重采样）', fontsize=10)
ax.spines[['top','right']].set_visible(False); ax.set_xlabel('配对差与 95% CI')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig4_ms_ci_forest.png'), bbox_inches='tight')
plt.close(fig)

# ---------- 图 5 · BC(δ=1) 注入侧盲率 ----------
bc = k['blind_cone_bc_delta1']
fig, ax = plt.subplots(figsize=(8.6, 4.4))
bt = bc['by_type']
bo = sorted(bt.keys(), key=lambda t: bt[t]['blind_rate'], reverse=True)
br = [bt[t]['blind_rate'] for t in bo]
bn = [bt[t]['n'] for t in bo]
bb = [bt[t]['blind'] for t in bo]
ax.bar(range(len(bo)), br, width=0.62,
       color=['#c0392b' if r >= 0.99 else '#3b6fd4' for r in br])
for i, (r, n, b) in enumerate(zip(br, bn, bb)):
    ax.text(i, r + 0.02, f'{r:.2f}\n({b}/{n})', ha='center', fontsize=8.5)
ax.axhline(bc['bc_blind_mass'], color='#c0392b', ls='--', lw=1.2)
ax.text(len(bo)-0.45, bc['bc_blind_mass']+0.02, f"BC 盲质量 {bc['bc_blind_mass']:.4f}（{bc['n_blind']}/{bc['n_total']}, δ=1）",
        color='#c0392b', fontsize=8.5, ha='right')
ax.set_xticks(list(range(len(bo)))); ax.set_xticklabels([TYPE_ZH[t] for t in bo])
ax.set_ylim(0, 1.18); ax.set_ylabel('盲率（δ=1 不可见占比）')
ax.set_title('盲锥测度注入侧：OCR 形近盲率 1.0 为锥尖（真实 OCR 分布侧待 C4 合成题库）')
ax.spines[['top','right']].set_visible(False)
fig.text(0.5, -0.02, '全合成语料（TAT-QA 底座）, 甲方真实 OCR 数据红线禁入; 数据: k2_ms_bc_analysis.json @711f315',
         ha='center', fontsize=7.5, color='#777777')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig5_bc_blind_rate.png'), bbox_inches='tight')
plt.close(fig)

print('DONE', sorted(os.listdir(OUT)))
