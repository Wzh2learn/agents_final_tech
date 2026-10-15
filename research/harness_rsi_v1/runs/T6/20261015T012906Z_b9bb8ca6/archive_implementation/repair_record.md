# T6 修复记录

- Attempt 1：`archive.py` 误把仓库根解析为 `/home/testuser/wzh/projects`，并发现 T4 manifest 仅含 `absolute_path`；保留原始失败文本于 `repair_attempts/attempt1_parent_root_failure.txt`。修复为仓库根 `parents[5]` 并从绝对路径派生 run 相对路径。
- Attempt 2：父组文件哈希已匹配，但锚点被二次加 manifest 前缀而返回 `actual=null`；失败记录于 `attempt2_anchor_prefix_failure.txt`。首次修复误改了 artifact lookup。
- Attempt 3：将 artifact 与 anchor 两类 lookup 反接，109 个 artifact 误报缺失；失败记录于 `attempt3_tree_lookup_inversion.txt`。最终恢复“artifact 加前缀、anchor 用仓库相对路径”。
- 最终状态：T5 45/45 声明 mode 与交付一致，45/45 内容组成员及 4/4 tracked anchor 通过；T4 64/64 内容组成员及 3/3 tracked anchor 通过。所有失败证据保留，未删除或覆盖。
- Attempt 4：首次运行 `self_check.py` 时仓库根误解析到 `/home/testuser/wzh`，未产出任何检查结果即退出；失败文本保留于 `attempt4_selfcheck_repo_root.txt`，修复为与 `archive.py` 一致的 `parents[5]`。
- Attempt 5：`Path(__file__)` 与 `Path(__file__).parent` 的父索引不同，`parents[5]` 在 self-check 中又多解析了一层 `research`；失败文本保留于 `attempt5_selfcheck_repo_root_file_parent.txt`，最终对文件路径使用 `parents[6]`。
- Attempt 6：写入边界扫描把 `git status --ignored=matching` 返回的普通 `??` 未跟踪行也计成 ignored，误报 T6 27 项；失败文本保留于 `attempt6_ignored_status_filter.txt`，最终要求 `!!` ignored 前缀。
- Attempt 7：normal status 的路径切片与带 porcelain 状态的 allowlist 不一致，导致既有 4 个 logs 脏件和未提交 T4 v1 全部误报越界；失败文本保留于 `attempt7_status_entry_slices.txt`，最终统一为纯路径 allowlist。
- Attempt 8：T6 自身前缀仍残留 `?? ` porcelain 标记，继续与路径切片不匹配；失败文本保留于 `attempt8_run_prefix_status_slice.txt`，最终只保留 run 目录路径前缀。
