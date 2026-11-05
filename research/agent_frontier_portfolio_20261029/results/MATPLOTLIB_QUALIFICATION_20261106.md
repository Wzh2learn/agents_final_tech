# Matplotlib 自然任务对：运行资格

> 2026-11-06 | 零模型资格，不是Agent效果。脚本：[资格器](../qualify_swe_contextbench_matplotlib_20261106.py)。原题、参考、依赖与时序通过后才安排source→target经验比较。

## 固定来源与原题

- source `matplotlib__matplotlib-23562`，base `29a86636a9c45ab5ac4d80ac76eaee497f460dce`：3D collection在首次投影前读取颜色触发AttributeError。
- target `matplotlib__matplotlib-27361`，base `5b5154ded5ee9c546e640b01f1a75ac041fd2fed`：3D patch在tight-layout保存时尚未建立二维路径；与source同属投影初始化，但对象、路径和测试不同。
- 官方GitHub compare留证：源PR合并`1fd71a5d23c0856f8005b9f82828d4b7c11b4734`是target base祖先，ahead5088/behind0。不是使用公开旧轨迹作为未经核实的历史。

## base / 参考修复控制

| 控制 | base | 参考修复 | 不改变的回归范围 |
| --- | --- | --- | --- |
| source关键测试 | 0/2 | 2/2 | 两臂均136/136 |
| source原题 | 首次取色`_facecolors2d` AttributeError | finite RGBA (2500,4)，draw前后形状稳定 | 原题独立于测试分数 |
| target关键测试 | 0/1 | 1/1 | 两臂均150/150 |
| target原题 | tight PDF/300dpi PNG均`_path2d` AttributeError | PDF7073 bytes、PNG249299 bytes；包围框内目标facecolor像素38026 | 验证格式、可见绘制与包围框，不只看是否生成文件 |

数据原始节点存在10项参数名被空格截断、7项缺失类名。仅对完整pytest collection中的唯一前缀/后缀匹配恢复，映射、missing及ambiguous逐项写日志；两臂均完整选择136/150条，未删除测试。

## 环境与边界

隔离Python3.10 / NumPy1.24.3，Agg替代原用户的QtAgg；检查的是同类投影及渲染行为，未声称复现GUI后端。源码来自固定commit；source使用3.6.3、target使用3.9.4 ARM wheel的原生扩展及缺失生成版号，各10文件有hash。wheel未覆盖Python行为源码，仍属混合环境，非固定commit原生构建。

两个归档各8项仅包含同目录目标的相对SVG软链，已按归档目标逐字节实体化并保留映射/hash；供未来Agent的源码不能再把这些文件当链接风险。首套source 3.5.3 native wheel的FT2Font ABI失败保留在v1现场，不覆盖为成功。

源码Matplotlib自有BSD兼容许可，任务数据卡MIT；各依赖原许可证继续适用。目标参考/test patch只供独立评分容器，不进入Agent工作区。题面和参考已在开发筛选中读取，本任务对不属于盲确认。

## 证据定位

GB10私有根：`/home/testuser/wzh/research_evidence/agent_learning_20261030/matplotlib_qualification_20261106_v2/`。

- receipt SHA-256 `b23f6980004b249b60902a6f68f82a561170a7d41209b8eecc4239609d1b9a25`。
- 原执行脚本SHA-256 `b7910caf78f36ca35828a71874c8a76b46fd6d808444cde7c8f9fa3c1ec68ece`；Git传输可有CRLF/LF差异，内容比较须声明换行口径。
- chronology SHA-256 `4560f9cd943c12d93539f4d44f5d7607c9fc45220d69c75c4ca3f9eda09b10f8`。
- `source/`、`target/`下各base/gold的原题、focus、regression日志及overlay、materialized_links清单可独立复核。第一套失败在相邻`matplotlib_qualification_20261106/`保留。

一次限定范围的独立只读核对已复算回执、映射、原题结果及归档实体化文件，未见阻断；它是AI代码/文件核对，不是人工专业金标。此次新增模型、训练、judge、生产调用均0。下一步复用已修复的离线搜索、真实源执行、冻结经验与自动账本，先完成自然source，再开展同配置target强基线。
