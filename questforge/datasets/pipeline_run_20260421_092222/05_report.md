---
stage: 5
stage_name: validation_and_finalize
version: 1.0
upstream: 04_tests.md
downstream: 最终产物
domain: 纪检材料智能审查
created_at: 2026-04-23T12:55:36+08:00
created_by: agent-stage5
pass_gate: true
---

# Stage 5 · 验证报告 + benchmark

## 摘要
2 道题中 2 道通过 5 设计原则验证；覆盖矩阵高/中/低严重度问题分别为 0/0/0；先验区分度分级={'合格': 1, '优秀': 1}；独立性评分 0.75。

## 5 设计原则验证
| TEST | 真实性 | 闭环性 | 可量化 | 区分度 | 预测力 | passed |
|---|---|---|---|---|---|---|
| TEST-001 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TEST-002 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## 覆盖矩阵对齐(实际 vs 蓝图)
| TEST | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 蓝图=重点 / 实际=覆盖✓ / 点数=3 | 蓝图=常规 / 实际=覆盖✓ / 点数=4 | 蓝图=常规 / 实际=覆盖✓ / 点数=4 | 蓝图=常规 / 实际=覆盖✓ / 点数=2 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 |
| TEST-002 | 蓝图=重点 / 实际=覆盖✓ / 点数=4 | 蓝图=常规 / 实际=覆盖✓ / 点数=5 | 蓝图=常规 / 实际=覆盖✓ / 点数=4 | 蓝图=常规 / 实际=覆盖✓ / 点数=2 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 |

## 盲区清单
（无）

## 先验区分度估计
| TEST | est_D | 分级 | 主要贡献项 |
|---|---|---|---|
| TEST-001 | 0.37 | 合格 | 约束密度高 |
| TEST-002 | 0.63 | 优秀 | 约束密度高 / 干扰设计强 / 跨资产整合 |

## 独立性评分
- 最高重合对:TEST-001 × TEST-002, overlap = 0.25
- independence_score = 0.75

| pair | asset | keyword | step | pair_overlap |
|---|---|---|---|---|
| TEST-001 × TEST-002 | 0.5 | 0.0 | 0.0 | 0.25 |

## 最终产物清单
- `dataset.json` — questforge/datasets/pipeline_run_20260421_092222/dataset.json
- `dataset.xlsx` — questforge/datasets/pipeline_run_20260421_092222/dataset.xlsx
- `05_report.md` — questforge/datasets/pipeline_run_20260421_092222/05_report.md
- `traceability.json` — questforge/datasets/pipeline_run_20260421_092222/traceability.json
- `dataset_supplementary/` — questforge/datasets/pipeline_run_20260421_092222/dataset_supplementary

## 结构化数据
```json
{
  "validation": {
    "by_principle": {
      "TEST-001": {
        "real_encounter": true,
        "five_stage_coverage": true,
        "quantifiable_criteria": true,
        "discrimination": true,
        "prediction_power": true,
        "passed": true,
        "notes": [
          "角色=一线纪检监察员",
          "真实性=4/4",
          "metric_hits=纪检监察员/定性量纪建议/定性量纪/量纪建议/中央八项规定"
        ]
      },
      "TEST-002": {
        "real_encounter": true,
        "five_stage_coverage": true,
        "quantifiable_criteria": true,
        "discrimination": true,
        "prediction_power": true,
        "passed": true,
        "notes": [
          "角色=案件审理人员",
          "真实性=5/5",
          "metric_hits=修订版文书/纠错依据溯源清单/依据溯源清单/纠错依据溯源/溯源清单"
        ]
      }
    },
    "coverage_matrix": {
      "TEST-001": {
        "定义问题": {
          "blueprint": "重点",
          "covered": true,
          "rich": true,
          "points": 3
        },
        "拆解问题": {
          "blueprint": "常规",
          "covered": true,
          "rich": true,
          "points": 4
        },
        "方案生成": {
          "blueprint": "常规",
          "covered": true,
          "rich": true,
          "points": 4
        },
        "执行落地": {
          "blueprint": "常规",
          "covered": true,
          "rich": true,
          "points": 2
        },
        "元认知": {
          "blueprint": "常规",
          "covered": true,
          "rich": true,
          "points": 3
        }
      },
      "TEST-002": {
        "定义问题": {
          "blueprint": "重点",
          "covered": true,
          "rich": true,
          "points": 4
        },
        "拆解问题": {
          "blueprint": "常规",
          "covered": true,
          "rich": true,
          "points": 5
        },
        "方案生成": {
          "blueprint": "常规",
          "covered": true,
          "rich": true,
          "points": 4
        },
        "执行落地": {
          "blueprint": "常规",
          "covered": true,
          "rich": true,
          "points": 2
        },
        "元认知": {
          "blueprint": "常规",
          "covered": true,
          "rich": true,
          "points": 3
        }
      }
    },
    "coverage_gaps": [],
    "discrimination_estimate": {
      "TEST-001": {
        "est_D": 0.37,
        "grade": "合格",
        "difficulty_score_normalized": 0.42,
        "constraint_density_normalized": 1.0,
        "interference_density_normalized": 0.0,
        "cross_asset_degree_normalized": 0.0,
        "major_contributors": [
          "约束密度高"
        ]
      },
      "TEST-002": {
        "est_D": 0.63,
        "grade": "优秀",
        "difficulty_score_normalized": 0.58,
        "constraint_density_normalized": 1.0,
        "interference_density_normalized": 0.5,
        "cross_asset_degree_normalized": 0.5,
        "major_contributors": [
          "约束密度高",
          "干扰设计强",
          "跨资产整合"
        ]
      }
    },
    "independence_score": 0.75,
    "most_overlapping_pair": [
      "TEST-001",
      "TEST-002"
    ],
    "pair_details": [
      {
        "pair": [
          "TEST-001",
          "TEST-002"
        ],
        "asset_overlap": 0.5,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.25
      }
    ]
  },
  "dataset_meta": {
    "version": "1.0",
    "domain": "纪检材料智能审查",
    "business_goal": "为纪检监察员提供党纪法规、总书记讲话、理论文章、实务案例的 AI 语义检索与文书纠错辅助",
    "success_metric": "纪检员单次语义检索平均响应时间 ≤ 3 秒，文书纠错准确率 ≥ 92%",
    "created_at": "2026-04-23T12:55:36+08:00",
    "total_items": 2,
    "difficulty_distribution": {
      "advanced": 2
    },
    "source_channel": "design_doc"
  }
}
```

## 下一阶段校验清单
- [x] 所有 TEST 的 passed=true
- [x] 覆盖矩阵盲区 severity=high 数 = 0
- [x] 独立性评分 ≥ 0.5
- [x] dataset.json 结构校验通过
- [x] dataset.xlsx 已生成且关键 sheet 存在

## 备注与遗留问题
（无）
