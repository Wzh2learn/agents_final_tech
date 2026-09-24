# Phase 1a 功效/MDE 敏感性网格（D 类字段的设计期决策支持；纯数学，不读任何数据）

> 状态: 活跃 | 更新: 2026-09-24 | 取代/被取代: 不取代 `DATA_NO_GO` 报告、裁定清单或口径缺口件；为裁定清单 §2「D 类」与 §4 第 5 步提供可算的取值面
> 用途: 把 D 类两项（`minimum_uid_by_role_family`、`minimum_uid_by_action`，以及与之联动的 `mde_by_confirmatory_contrast`）从「凭感觉填」变成「在一张显式假设网格上选点」，并暴露一处**结构性欠功效风险**。
> 边界: **本件是设计期工具，不是实验、不是结果、不是论文数字。** 不批准任何数值、不产生任何可写进论文的测量值、不改 `POWER_GO`、不改判据、不读任何数据集、不填任何 `UNSET`、不解 `DATA_NO_GO`。所有输入一律是**显式标注的未批准假设**，在网格上扫描；**没有任何一格是推荐值**。

## 1 为什么不用仓内 88 个历史 eval 工件去「测」方差（关键纪律）

仓内 `logs/graph/eval/` 有 88 个已验收工件，看起来能提供方差。但 `docs/experiments/2026-09-23_phase1a_data_no_go.md` 明令：

> Historical checkpoints, old accepted labels, DPO pairs, and rolling audit artifacts may be used for **provenance and failure analysis only**. They must not be re-split into training data, used to tune a rule, or used as a replacement for a sealed/test layer.

且该报告的门槛表把 Statistical plan 一项记为 “Power, non-inferiority margin, and acceptance parameters are **not approved** for this gate ⇒ No inferential or non-inferiority conclusion”。

同时预注册件 §6.3 要求的是「用**开发侧方差假设**做 UID 聚类 MDE/功效分析；**不用 sealed 结果反推参数**」——注意是**假设**（assumption），不是从历史结果测出来的量。

⇒ 本件因此**完全不读任何数据**，只做「显式假设 → 闭式公式 → 网格」的设计期计算。这既符合 §6.3 与 §11.2（“未确认时只报告敏感性范围”），也避免把历史工件当成 Phase 1a 的方差来源（跨实验族外推，且违反上面的 permitted-use 限制）。

## 2 方法与公式

合同指定的设计（`research/phase1a_data_contract.py`）: `cluster_unit = lineage_uid`（:918）· `seed_uid_aggregation = fixed_seed_pair_then_uid_cluster_bootstrap`（:942）· 质量/安全/retention 用**单侧**置信界对 $\mp\delta$（§6.3 :116）· `H3a_cluster_any_harm` 用 `exact_mcnemar`（:950）· Holm step-down（:944-955）。

### 2.1 UID 聚类下的单侧非劣所需独立 UID 数 K

```text
Var(mean diff) ~= sigma^2 * [1 + (m-1)*rho] / (K * m)
=> K >= (z_{1-alpha} + z_{power})^2 * sigma^2 * [1 + (m-1)*rho] / (m * delta^2)
```

- `K` = 独立 `lineage_uid` 数，即 `minimum_uid_by_role_family` 所约束的量
- `m` = 每个 UID 内的观测数（事件 × seed 对）
- `rho` = **UID 内相关（ICC）**
- `sigma` = **配对差值**（A2−A1）的单观测标准差；配对通常比原始指标小，勿用原始指标 SD
- `delta` = 非劣边界（`delta_quality` / `delta_harm` / `delta_retention`）
- `DEFF = 1 + (m-1)*rho` 为标准设计效应

### 2.2 三处独立交叉核验（全部 PASS，可重跑）

1. **退化到教科书式**: 取 `m=1, rho=0`，公式必须等于无聚类的单侧非劣样本量。实测 `z_{0.95}=1.644854`、`z_{0.80}=0.841621`、和 `2.486475`，`sigma=0.10, delta=0.05` ⇒ 教科书 `n_obs = 24.7302 → ceil 25`，网格 `m=1,rho=0` 给出 **25**，**逐位相等**。`m=4,rho=0` 给 `K=7`（总观测 28 ≥ 25，多出的是整簇取整），行为正确。
2. **精确 McNemar 下限用暴力枚举复核**: `alpha=0.05` 暴力搜得 `d_min=5`，与对数式 `ceil(log(0.05)/log(0.5))=5` 一致；`0.01→7`、`0.005→8` 同样一致；并逐个断言 `0.5^(d-1) > alpha >= 0.5^d`。
3. **不走 `0.5^d` 捷径、直接用二项系数枚举**: `P(min(b,c)=0 | H0) = C(d,0)*0.5^d`，实测 `d=3→0.125`（不显著）、`d=4→0.0625`（**不显著**）、`d=5→0.03125`（显著）、`d=6→0.015625`（显著）⇒ 硬下限确为 **5**。

## 3 表 A：所需独立 UID 数 K（288 格，`alpha=0.05` 单侧）

`power=0.80, sigma=0.10, m=4`

```text
rho\delta      0.01     0.02     0.03     0.05
      0.0      155       39       18        7
     0.05      178       45       20        8
      0.1      201       51       23        9
      0.2      248       62       28       10
```

`power=0.80, sigma=0.20, m=4`

```text
rho\delta      0.01     0.02     0.03     0.05
      0.0      619      155       69       25
     0.05      711      178       79       29
      0.1      804      201       90       33
      0.2      990      248      110       40
```

`power=0.90, sigma=0.10, m=4`

```text
rho\delta      0.01     0.02     0.03     0.05
      0.0      215       54       24        9
     0.05      247       62       28       10
      0.1      279       70       31       12
      0.2      343       86       39       14
```

`power=0.90, sigma=0.20, m=4`

```text
rho\delta      0.01     0.02     0.03     0.05
      0.0      857      215       96       35
     0.05      985      247      110       40
      0.1     1114      279      124       45
      0.2     1371      343      153       55
```

全 288 格的 K 值域 = **1 .. 2056**。

**读法（这是本表最重要的一句话）**: 在 `delta=0.02` 这一列上，K 从 **39**（`sigma=0.10, rho=0, power=0.8`）一路到 **343**（`sigma=0.20, rho=0.2, power=0.9`），**跨一个数量级**。主导项是 `sigma`（平方关系），不是 `rho`。⇒ **在没有真实开发侧 `sigma` 之前，D 类两项在数学上无法收敛到唯一值**；这不是「还没算」，而是「输入不存在」。数据补充合同必须先交付能估 `sigma` 的开发侧样本，D 类才可定值。

### 3.1 设计效应本身

```text
m\rho        0.0     0.05      0.1      0.2
     2      1.00     1.05     1.10     1.20
     4      1.00     1.15     1.30     1.60
     8      1.00     1.35     1.70     2.40
```

**必须警告的符号冲突**: 本件的 `rho` 是 **UID 内相关 ICC**，与 §7 收据里的 `risk_limit`（即 $\rho_{\max}$，候选风险上限，讨论起点 0.1）是**完全不同的两个量**，只是共用一个希腊字母。**不得把 `risk_limit=0.1` 当作 ICC 代进设计效应**——那会把 `m=4` 的 DEFF 误设为 1.30，从而系统性低估所需 K 约 23%。

## 4 表 B：`exact_mcnemar` 的硬下限（本件最重要的发现）

`H3a_cluster_any_harm` 被合同钉死为 `exact_mcnemar`（:950）。精确检验在 `d` 个不一致对（discordant pairs）下，**可达到的最小单侧 p 值**是「全部不一致对同向」时的 `0.5^d`。故显著性**在数学上不可能**，除非 `0.5^d <= alpha`：

```text
alpha=0.05 : d_min = 5   (0.5^5 = 0.03125;  0.5^4 = 0.06250 > 0.05)
alpha=0.01 : d_min = 7   (0.5^7 = 0.00781;  0.5^6 = 0.01563 > 0.01)
alpha=0.005: d_min = 8   (0.5^8 = 0.00391;  0.5^7 = 0.00781 > 0.005)
```

⇒ **合同对 `minimum_uid_by_action` 只要求 `>= 2`（:962-968），那是一个健全性下限，不是功效下限。** 填 2 能让合同 PASS，但对 `H3a_cluster_any_harm` 而言**在任何数据下都不可能得出显著结论**。

要**期望**观测到 `d` 个不一致对，需要总量 `N ~= d / p_d`（`p_d` = 不一致率）：

```text
p_d\target_d         5        8       10       20
        0.01      500      800     1000     2000
        0.02      250      400      500     1000
        0.05      100      160      200      400
         0.1       50       80      100      200
         0.2       25       40       50      100
```

**结论（须用户/导师裁，本件不代判）**: 若真实伤害不一致率低（例如 1%–2%），`H3a_cluster_any_harm` 属**结构性欠功效**——无论人怎么填 `minimum_uid_by_action` 都救不回来。可选处置只有三条，且都属判据面，需显式授权：① 把该假设降为 exploratory（但 §6.3 :117 已把它固定在 RQ3 确认性家族里）；② 提高数据补充规模到 `N >= 250–500`；③ 改用渐近 McNemar 或别的检验（= 改冻结判据）。**在裁定前，`mde_by_confirmatory_contrast["H3a_cluster_any_harm"]` 不是自由变量，它被这个下限约束。**

## 5 表 C：最稀的动作决定总量（`minimum_uid_by_action` 的真实代价）

合同要求 `minimum_uid_by_action` 的键集**恰好**为 `{map_to, skip, hold}`（:962-968）。约束来自**最稀的那个动作**：`N_total >= K_required / prevalence`。以 `power=0.8, sigma=0.10, m=4, rho=0.05` 为参照行（`K` 按 `delta` = `{0.01:178, 0.02:45, 0.03:20, 0.05:8}`）：

```text
prev\delta      0.01     0.02     0.03     0.05
      0.01    17800     4500     2000      800
      0.02     8900     2250     1000      400
      0.05     3560      900      400      160
       0.1     1780      450      200       80
       0.2      890      225      100       40
      0.33      540      137       61       25
```

⇒ 若 `hold` 的真实占比是 1%–2%，而 `delta` 又要取到 0.01–0.02，则所需总量落在 **4 500 – 17 800** 个 UID 量级。这是给**数据补充合同**（`DATA_NO_GO` 报告的 “Executable supplement contract” 八角色）的定量输入：交付规模与动作占比必须先测，否则 D 类填任何值都是空中楼阁。

## 6 对决策 6（D 类）的意义：只给取值面，不给取值

1. `minimum_uid_by_role_family` 与 `mde_by_confirmatory_contrast` **不能独立填**：固定 `alpha/power/sigma/rho/m` 后，两者由表 A 的公式**互相决定**。填一个而不核另一个，等于把功效声明写成装饰。
2. 在拿到真实开发侧 `sigma`、`rho`、`m` 与动作占比之前，**D 类无可定值**。表 A 显示同一 `delta` 下 K 跨一个数量级，主导项是 `sigma`。
3. `H3a_cluster_any_harm` 的 MDE 受表 B 的**硬下限**约束，不随人意；这是本件查出的新风险，此前无任何条目记录。
4. 建议的裁定顺序（与裁定清单 §4 一致，本件只补定量依据）: 先由数据补充交付**开发侧**样本以估 `sigma/rho/m/动作占比` → 再在表 A/C 上选点 → 最后按表 B 核 `H3a_cluster_any_harm` 是否可达，不可达则须先裁 §4 的三条处置之一。

## 7 局限（如实列，勿当结论用）

- `sigma`、`rho`、`m`、`p_d`、动作占比**全部未知**，本件只扫描，不估计、不推荐。
- §2.1 用**设计效应聚类模型**近似合同指定的**两阶段 bootstrap**（先成对重采样 seed，再在 seed 内成对重采样 UID）。两者在小样本或强不平衡下会有偏差；**最终方差必须由真实数据上的 bootstrap 给出**，本件的 K 只是设计期量级。
- 表 B 的 `d_min` 是**必要条件而非充分条件**：它假设全部不一致对同向（最有利情形）。真实数据下达到同样功效需要更多不一致对。
- Holm step-down 会进一步抬高所需样本量（家族内多重比较），本件**未**计入 ⇒ 表 A 的 K 是**下界**，偏乐观。
- 公式假设近似正态；对 `harmful_map_rate` 这类稀有二项指标，正态近似在低事件率下不可靠，应改用精确法（表 B 即为此而设）。

## 8 复现与取证

```bash
ssh jinrong-dev
~/wzh/projects/agents_final_tech/venv/bin/python /tmp/p1a_power_sensitivity.py
~/wzh/projects/agents_final_tech/venv/bin/python /tmp/p1a_power_crosscheck.py
```

| 文件（GB10 `/tmp`，仓外，不 commit） | sha256 |
|---|---|
| `p1a_power_sensitivity.py` | `3b253e45be1419b9d8cc8ffd5701c9e9fa298d1e8730018c98e13a7676740619` |
| `p1a_power_sensitivity.json` | `97c8d317c7524c169dcf3a24866734c447b7587ac87e0df606c0303bdd8ddd48` |
| `p1a_power_crosscheck.py` | `ae5ede8439117c05338556041a506fa6033be666af8519c4c969968843f29e07` |

纯 stdlib（`statistics.NormalDist`、`math`），**零第三方依赖、零端点、零模型调用、零数据读取**；脚本内含 `assert`，任一交叉核验不通过即抛错而非静默出数。`/tmp` 非持久，故全部数值表已逐字抄入本件。

## 9 红线自查

- 未读任何数据集、未读 `logs/graph/eval/` 任何工件作为方差来源（§1 说明理由）。
- 未批准任何数值、未填任何 `UNSET`、未改预注册合同与 `phase1a_data_contract.py`、未改冻结判据/阈值/oracle/冻结 hash。
- 未解 `DATA_NO_GO`（本件反而给出「D 类在拿到开发侧 `sigma` 前不可定值」的定量理由）；未启动 Phase 1a/2；未授权训练或模型端点。
- 零端点、零模型调用、零 canary、零 judge、零起 run；未派发任何 Loop A/B/C 卡。
- 未动 `docs/33`、`docs/34`；未 pull production；未重启 daemon 与 `:5050`；未改 crontab；四件用户资产零触碰。
- 本件不含任何可写入论文的测量值；所有数字均为「假设 → 闭式公式」的推导结果，且已标注为设计期量级而非结论。
