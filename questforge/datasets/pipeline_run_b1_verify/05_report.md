---
stage: 5
stage_name: validation_and_finalize
version: 1.0
upstream: 04_tests.md
downstream: 最终产物
domain: 纪检材料智能审查
created_at: 2026-05-07T23:06:31+08:00
created_by: agent-stage5
pass_gate: false
---

# Stage 5 · 验证报告 + benchmark

## 摘要
6 道题中 6 道通过 5 设计原则验证；覆盖矩阵高/中/低严重度问题分别为 0/0/0；先验区分度分级={'待改进': 2, '优秀': 4}；独立性评分 0.0。

## 5 设计原则验证
| TEST | 真实性 | 闭环性 | 可量化 | 区分度 | 预测力 | passed |
|---|---|---|---|---|---|---|
| TEST-001 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TEST-002 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TEST-003 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TEST-004 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TEST-005 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TEST-006 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## 覆盖矩阵对齐(实际 vs 蓝图)
| TEST | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 蓝图=重点 / 实际=覆盖✓ / 点数=3 | 蓝图=常规 / 实际=覆盖✓ / 点数=4 | 蓝图=常规 / 实际=覆盖✓ / 点数=4 | 蓝图=常规 / 实际=覆盖✓ / 点数=2 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 |
| TEST-002 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 | 蓝图=常规 / 实际=覆盖✓ / 点数=4 | 蓝图=常规 / 实际=覆盖✓ / 点数=4 | 蓝图=重点 / 实际=覆盖✓ / 点数=2 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 |
| TEST-003 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 | 蓝图=重点 / 实际=覆盖✓ / 点数=4 | 蓝图=重点 / 实际=覆盖✓ / 点数=7 | 蓝图=常规 / 实际=覆盖✓ / 点数=2 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 |
| TEST-004 | 蓝图=重点 / 实际=覆盖✓ / 点数=3 | 蓝图=常规 / 实际=覆盖✓ / 点数=4 | 蓝图=重点 / 实际=覆盖✓ / 点数=5 | 蓝图=常规 / 实际=覆盖✓ / 点数=2 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 |
| TEST-005 | 蓝图=重点 / 实际=覆盖✓ / 点数=4 | 蓝图=常规 / 实际=覆盖✓ / 点数=5 | 蓝图=重点 / 实际=覆盖✓ / 点数=5 | 蓝图=常规 / 实际=覆盖✓ / 点数=2 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 |
| TEST-006 | 蓝图=常规 / 实际=覆盖✓ / 点数=4 | 蓝图=重点 / 实际=覆盖✓ / 点数=5 | 蓝图=常规 / 实际=覆盖✓ / 点数=5 | 蓝图=重点 / 实际=覆盖✓ / 点数=2 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 |

## 盲区清单
（无）

## 先验区分度估计
| TEST | est_D | 分级 | 主要贡献项 |
|---|---|---|---|
| TEST-001 | 0.28 | 待改进 | 约束密度高 |
| TEST-002 | 0.28 | 待改进 | 约束密度高 |
| TEST-003 | 0.67 | 优秀 | 约束密度高 / 干扰设计强 / 跨资产整合 / 难度偏高 |
| TEST-004 | 0.67 | 优秀 | 约束密度高 / 干扰设计强 / 跨资产整合 / 难度偏高 |
| TEST-005 | 0.67 | 优秀 | 约束密度高 / 干扰设计强 / 跨资产整合 / 难度偏高 |
| TEST-006 | 0.67 | 优秀 | 约束密度高 / 干扰设计强 / 跨资产整合 / 难度偏高 |

## 独立性评分
- 最高重合对:TEST-001 × TEST-002, overlap = 1.0
- independence_score = 0.0

| pair | asset | keyword | step | pair_overlap |
|---|---|---|---|---|
| TEST-001 × TEST-002 | 1.0 | 1.0 | 1.0 | 1.0 |
| TEST-003 × TEST-004 | 1.0 | 1.0 | 1.0 | 1.0 |
| TEST-005 × TEST-006 | 1.0 | 1.0 | 1.0 | 1.0 |
| TEST-003 × TEST-005 | 1.0 | 0.0 | 0.0 | 0.5 |
| TEST-003 × TEST-006 | 1.0 | 0.0 | 0.0 | 0.5 |
| TEST-004 × TEST-005 | 1.0 | 0.0 | 0.0 | 0.5 |
| TEST-004 × TEST-006 | 1.0 | 0.0 | 0.0 | 0.5 |
| TEST-001 × TEST-003 | 0.5 | 0.0 | 0.0 | 0.25 |
| TEST-001 × TEST-004 | 0.5 | 0.0 | 0.0 | 0.25 |
| TEST-001 × TEST-005 | 0.5 | 0.0 | 0.0 | 0.25 |
| TEST-001 × TEST-006 | 0.5 | 0.0 | 0.0 | 0.25 |
| TEST-002 × TEST-003 | 0.5 | 0.0 | 0.0 | 0.25 |
| TEST-002 × TEST-004 | 0.5 | 0.0 | 0.0 | 0.25 |
| TEST-002 × TEST-005 | 0.5 | 0.0 | 0.0 | 0.25 |
| TEST-002 × TEST-006 | 0.5 | 0.0 | 0.0 | 0.25 |

## 分群聚合统计
- 全集 6 道,passed_rate=1.0,难度分布={'advanced': 2, 'expert': 4}
- difficulty_score: mean=2.11 / median=2.33 / p25=1.83 / p75=2.33 / p90=2.33
- est_D: mean=0.54 / p25=0.38 / p75=0.67
- 完整数据见 `dataset_supplementary/aggregations.json`

**按难度分群**
| difficulty | count | passed_rate | diff_score.mean | 约束.mean | 干扰.mean | est_D.mean |
|---|---|---|---|---|---|---|
| advanced | 2 | 1.0 | 1.67 | 3.0 | 0.0 | 0.28 |
| expert | 4 | 1.0 | 2.33 | 4.0 | 1.0 | 0.67 |

**按用户画像分群**(每道题可能命中多个 UG)
| user_group | count | passed_rate | diff_score.mean | est_D.mean |
|---|---|---|---|---|
| UG-001 | 4 | 1.0 | 2.0 | 0.48 |
| UG-002 | 2 | 1.0 | 2.33 | 0.67 |

## 最终产物清单
- `dataset.json` — questforge/datasets/pipeline_run_b1_verify/dataset.json
- `dataset.xlsx` — questforge/datasets/pipeline_run_b1_verify/dataset.xlsx
- `05_report.md` — questforge/datasets/pipeline_run_b1_verify/05_report.md
- `traceability.json` — questforge/datasets/pipeline_run_b1_verify/traceability.json
- `dataset_supplementary/` — questforge/datasets/pipeline_run_b1_verify/dataset_supplementary

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
          "真实性=3/3",
          "metric_hits=条款匹配/党纪条款/影响公正执行公务/公正执行公务的/执行公务的财物"
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
          "角色=一线纪检监察员",
          "真实性=3/3",
          "metric_hits=定性量纪建议/党纪条款匹配报告/党纪条款匹配/条款匹配报告/匹配报告"
        ]
      },
      "TEST-003": {
        "real_encounter": true,
        "five_stage_coverage": true,
        "quantifiable_criteria": true,
        "discrimination": true,
        "prediction_power": true,
        "passed": true,
        "notes": [
          "角色=一线纪检监察员",
          "真实性=5/5",
          "metric_hits=定性量纪综合建议/量纪综合建议/定性量纪综合/量纪综合/综合建议"
        ]
      },
      "TEST-004": {
        "real_encounter": true,
        "five_stage_coverage": true,
        "quantifiable_criteria": true,
        "discrimination": true,
        "prediction_power": true,
        "passed": true,
        "notes": [
          "角色=一线纪检监察员",
          "真实性=5/5",
          "metric_hits=定性量纪综合建议/量纪综合建议/定性量纪综合/量纪综合/综合建议"
        ]
      },
      "TEST-005": {
        "real_encounter": true,
        "five_stage_coverage": true,
        "quantifiable_criteria": true,
        "discrimination": true,
        "prediction_power": true,
        "passed": true,
        "notes": [
          "角色=案件审理人员",
          "真实性=5/5",
          "metric_hits=文书纠错分析报告/文书纠错分析/纠错分析报告/纠错分析/文书纠错"
        ]
      },
      "TEST-006": {
        "real_encounter": true,
        "five_stage_coverage": true,
        "quantifiable_criteria": true,
        "discrimination": true,
        "prediction_power": true,
        "passed": true,
        "notes": [
          "角色=案件审理人员",
          "真实性=5/5",
          "metric_hits=文书纠错分析报告/文书纠错分析/纠错分析报告/纠错分析/文书纠错"
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
          "blueprint": "常规",
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
          "blueprint": "重点",
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
      "TEST-003": {
        "定义问题": {
          "blueprint": "常规",
          "covered": true,
          "rich": true,
          "points": 3
        },
        "拆解问题": {
          "blueprint": "重点",
          "covered": true,
          "rich": true,
          "points": 4
        },
        "方案生成": {
          "blueprint": "重点",
          "covered": true,
          "rich": true,
          "points": 7
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
      "TEST-004": {
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
          "blueprint": "重点",
          "covered": true,
          "rich": true,
          "points": 5
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
      "TEST-005": {
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
          "blueprint": "重点",
          "covered": true,
          "rich": true,
          "points": 5
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
      "TEST-006": {
        "定义问题": {
          "blueprint": "常规",
          "covered": true,
          "rich": true,
          "points": 4
        },
        "拆解问题": {
          "blueprint": "重点",
          "covered": true,
          "rich": true,
          "points": 5
        },
        "方案生成": {
          "blueprint": "常规",
          "covered": true,
          "rich": true,
          "points": 5
        },
        "执行落地": {
          "blueprint": "重点",
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
        "est_D": 0.28,
        "grade": "待改进",
        "difficulty_score_normalized": 0.33,
        "constraint_density_normalized": 0.75,
        "interference_density_normalized": 0.0,
        "cross_asset_degree_normalized": 0.0,
        "major_contributors": [
          "约束密度高"
        ]
      },
      "TEST-002": {
        "est_D": 0.28,
        "grade": "待改进",
        "difficulty_score_normalized": 0.33,
        "constraint_density_normalized": 0.75,
        "interference_density_normalized": 0.0,
        "cross_asset_degree_normalized": 0.0,
        "major_contributors": [
          "约束密度高"
        ]
      },
      "TEST-003": {
        "est_D": 0.67,
        "grade": "优秀",
        "difficulty_score_normalized": 0.67,
        "constraint_density_normalized": 1.0,
        "interference_density_normalized": 0.5,
        "cross_asset_degree_normalized": 0.5,
        "major_contributors": [
          "约束密度高",
          "干扰设计强",
          "跨资产整合",
          "难度偏高"
        ]
      },
      "TEST-004": {
        "est_D": 0.67,
        "grade": "优秀",
        "difficulty_score_normalized": 0.67,
        "constraint_density_normalized": 1.0,
        "interference_density_normalized": 0.5,
        "cross_asset_degree_normalized": 0.5,
        "major_contributors": [
          "约束密度高",
          "干扰设计强",
          "跨资产整合",
          "难度偏高"
        ]
      },
      "TEST-005": {
        "est_D": 0.67,
        "grade": "优秀",
        "difficulty_score_normalized": 0.67,
        "constraint_density_normalized": 1.0,
        "interference_density_normalized": 0.5,
        "cross_asset_degree_normalized": 0.5,
        "major_contributors": [
          "约束密度高",
          "干扰设计强",
          "跨资产整合",
          "难度偏高"
        ]
      },
      "TEST-006": {
        "est_D": 0.67,
        "grade": "优秀",
        "difficulty_score_normalized": 0.67,
        "constraint_density_normalized": 1.0,
        "interference_density_normalized": 0.5,
        "cross_asset_degree_normalized": 0.5,
        "major_contributors": [
          "约束密度高",
          "干扰设计强",
          "跨资产整合",
          "难度偏高"
        ]
      }
    },
    "independence_score": 0.0,
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
        "asset_overlap": 1.0,
        "keyword_overlap": 1.0,
        "step_overlap": 1.0,
        "pair_overlap": 1.0
      },
      {
        "pair": [
          "TEST-003",
          "TEST-004"
        ],
        "asset_overlap": 1.0,
        "keyword_overlap": 1.0,
        "step_overlap": 1.0,
        "pair_overlap": 1.0
      },
      {
        "pair": [
          "TEST-005",
          "TEST-006"
        ],
        "asset_overlap": 1.0,
        "keyword_overlap": 1.0,
        "step_overlap": 1.0,
        "pair_overlap": 1.0
      },
      {
        "pair": [
          "TEST-003",
          "TEST-005"
        ],
        "asset_overlap": 1.0,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.5
      },
      {
        "pair": [
          "TEST-003",
          "TEST-006"
        ],
        "asset_overlap": 1.0,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.5
      },
      {
        "pair": [
          "TEST-004",
          "TEST-005"
        ],
        "asset_overlap": 1.0,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.5
      },
      {
        "pair": [
          "TEST-004",
          "TEST-006"
        ],
        "asset_overlap": 1.0,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.5
      },
      {
        "pair": [
          "TEST-001",
          "TEST-003"
        ],
        "asset_overlap": 0.5,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.25
      },
      {
        "pair": [
          "TEST-001",
          "TEST-004"
        ],
        "asset_overlap": 0.5,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.25
      },
      {
        "pair": [
          "TEST-001",
          "TEST-005"
        ],
        "asset_overlap": 0.5,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.25
      },
      {
        "pair": [
          "TEST-001",
          "TEST-006"
        ],
        "asset_overlap": 0.5,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.25
      },
      {
        "pair": [
          "TEST-002",
          "TEST-003"
        ],
        "asset_overlap": 0.5,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.25
      },
      {
        "pair": [
          "TEST-002",
          "TEST-004"
        ],
        "asset_overlap": 0.5,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.25
      },
      {
        "pair": [
          "TEST-002",
          "TEST-005"
        ],
        "asset_overlap": 0.5,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.25
      },
      {
        "pair": [
          "TEST-002",
          "TEST-006"
        ],
        "asset_overlap": 0.5,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.25
      }
    ]
  },
  "aggregations": {
    "global": {
      "count": 6,
      "test_ids": [
        "TEST-001",
        "TEST-002",
        "TEST-003",
        "TEST-004",
        "TEST-005",
        "TEST-006"
      ],
      "passed_rate": 1.0,
      "difficulty_distribution": {
        "advanced": 2,
        "expert": 4
      },
      "difficulty_score": {
        "count": 6,
        "mean": 2.11,
        "median": 2.33,
        "min": 1.67,
        "max": 2.33,
        "p25": 1.83,
        "p75": 2.33,
        "p90": 2.33,
        "stdev": 0.34
      },
      "constraint_count": {
        "count": 6,
        "mean": 3.67,
        "median": 4.0,
        "min": 3.0,
        "max": 4.0,
        "p25": 3.25,
        "p75": 4.0,
        "p90": 4.0,
        "stdev": 0.52
      },
      "interference_count": {
        "count": 6,
        "mean": 0.67,
        "median": 1.0,
        "min": 0.0,
        "max": 1.0,
        "p25": 0.25,
        "p75": 1.0,
        "p90": 1.0,
        "stdev": 0.52
      },
      "est_D": {
        "count": 6,
        "mean": 0.54,
        "median": 0.67,
        "min": 0.28,
        "max": 0.67,
        "p25": 0.38,
        "p75": 0.67,
        "p90": 0.67,
        "stdev": 0.2
      }
    },
    "by_difficulty": {
      "advanced": {
        "count": 2,
        "test_ids": [
          "TEST-001",
          "TEST-002"
        ],
        "passed_rate": 1.0,
        "difficulty_distribution": {
          "advanced": 2
        },
        "difficulty_score": {
          "count": 2,
          "mean": 1.67,
          "median": 1.67,
          "min": 1.67,
          "max": 1.67,
          "p25": 1.67,
          "p75": 1.67,
          "p90": 1.67,
          "stdev": 0.0
        },
        "constraint_count": {
          "count": 2,
          "mean": 3.0,
          "median": 3.0,
          "min": 3.0,
          "max": 3.0,
          "p25": 3.0,
          "p75": 3.0,
          "p90": 3.0,
          "stdev": 0.0
        },
        "interference_count": {
          "count": 2,
          "mean": 0.0,
          "median": 0.0,
          "min": 0.0,
          "max": 0.0,
          "p25": 0.0,
          "p75": 0.0,
          "p90": 0.0,
          "stdev": 0.0
        },
        "est_D": {
          "count": 2,
          "mean": 0.28,
          "median": 0.28,
          "min": 0.28,
          "max": 0.28,
          "p25": 0.28,
          "p75": 0.28,
          "p90": 0.28,
          "stdev": 0.0
        }
      },
      "expert": {
        "count": 4,
        "test_ids": [
          "TEST-003",
          "TEST-004",
          "TEST-005",
          "TEST-006"
        ],
        "passed_rate": 1.0,
        "difficulty_distribution": {
          "expert": 4
        },
        "difficulty_score": {
          "count": 4,
          "mean": 2.33,
          "median": 2.33,
          "min": 2.33,
          "max": 2.33,
          "p25": 2.33,
          "p75": 2.33,
          "p90": 2.33,
          "stdev": 0.0
        },
        "constraint_count": {
          "count": 4,
          "mean": 4.0,
          "median": 4.0,
          "min": 4.0,
          "max": 4.0,
          "p25": 4.0,
          "p75": 4.0,
          "p90": 4.0,
          "stdev": 0.0
        },
        "interference_count": {
          "count": 4,
          "mean": 1.0,
          "median": 1.0,
          "min": 1.0,
          "max": 1.0,
          "p25": 1.0,
          "p75": 1.0,
          "p90": 1.0,
          "stdev": 0.0
        },
        "est_D": {
          "count": 4,
          "mean": 0.67,
          "median": 0.67,
          "min": 0.67,
          "max": 0.67,
          "p25": 0.67,
          "p75": 0.67,
          "p90": 0.67,
          "stdev": 0.0
        }
      }
    },
    "by_user_group": {
      "UG-001": {
        "count": 4,
        "test_ids": [
          "TEST-001",
          "TEST-002",
          "TEST-003",
          "TEST-004"
        ],
        "passed_rate": 1.0,
        "difficulty_distribution": {
          "advanced": 2,
          "expert": 2
        },
        "difficulty_score": {
          "count": 4,
          "mean": 2.0,
          "median": 2.0,
          "min": 1.67,
          "max": 2.33,
          "p25": 1.67,
          "p75": 2.33,
          "p90": 2.33,
          "stdev": 0.38
        },
        "constraint_count": {
          "count": 4,
          "mean": 3.5,
          "median": 3.5,
          "min": 3.0,
          "max": 4.0,
          "p25": 3.0,
          "p75": 4.0,
          "p90": 4.0,
          "stdev": 0.58
        },
        "interference_count": {
          "count": 4,
          "mean": 0.5,
          "median": 0.5,
          "min": 0.0,
          "max": 1.0,
          "p25": 0.0,
          "p75": 1.0,
          "p90": 1.0,
          "stdev": 0.58
        },
        "est_D": {
          "count": 4,
          "mean": 0.48,
          "median": 0.48,
          "min": 0.28,
          "max": 0.67,
          "p25": 0.28,
          "p75": 0.67,
          "p90": 0.67,
          "stdev": 0.23
        }
      },
      "UG-002": {
        "count": 2,
        "test_ids": [
          "TEST-005",
          "TEST-006"
        ],
        "passed_rate": 1.0,
        "difficulty_distribution": {
          "expert": 2
        },
        "difficulty_score": {
          "count": 2,
          "mean": 2.33,
          "median": 2.33,
          "min": 2.33,
          "max": 2.33,
          "p25": 2.33,
          "p75": 2.33,
          "p90": 2.33,
          "stdev": 0.0
        },
        "constraint_count": {
          "count": 2,
          "mean": 4.0,
          "median": 4.0,
          "min": 4.0,
          "max": 4.0,
          "p25": 4.0,
          "p75": 4.0,
          "p90": 4.0,
          "stdev": 0.0
        },
        "interference_count": {
          "count": 2,
          "mean": 1.0,
          "median": 1.0,
          "min": 1.0,
          "max": 1.0,
          "p25": 1.0,
          "p75": 1.0,
          "p90": 1.0,
          "stdev": 0.0
        },
        "est_D": {
          "count": 2,
          "mean": 0.67,
          "median": 0.67,
          "min": 0.67,
          "max": 0.67,
          "p25": 0.67,
          "p75": 0.67,
          "p90": 0.67,
          "stdev": 0.0
        }
      }
    },
    "by_source_process": {
      "BP-001": {
        "count": 2,
        "test_ids": [
          "TEST-001",
          "TEST-002"
        ],
        "passed_rate": 1.0,
        "difficulty_distribution": {
          "advanced": 2
        },
        "difficulty_score": {
          "count": 2,
          "mean": 1.67,
          "median": 1.67,
          "min": 1.67,
          "max": 1.67,
          "p25": 1.67,
          "p75": 1.67,
          "p90": 1.67,
          "stdev": 0.0
        },
        "constraint_count": {
          "count": 2,
          "mean": 3.0,
          "median": 3.0,
          "min": 3.0,
          "max": 3.0,
          "p25": 3.0,
          "p75": 3.0,
          "p90": 3.0,
          "stdev": 0.0
        },
        "interference_count": {
          "count": 2,
          "mean": 0.0,
          "median": 0.0,
          "min": 0.0,
          "max": 0.0,
          "p25": 0.0,
          "p75": 0.0,
          "p90": 0.0,
          "stdev": 0.0
        },
        "est_D": {
          "count": 2,
          "mean": 0.28,
          "median": 0.28,
          "min": 0.28,
          "max": 0.28,
          "p25": 0.28,
          "p75": 0.28,
          "p90": 0.28,
          "stdev": 0.0
        }
      },
      "BP-002": {
        "count": 2,
        "test_ids": [
          "TEST-003",
          "TEST-004"
        ],
        "passed_rate": 1.0,
        "difficulty_distribution": {
          "expert": 2
        },
        "difficulty_score": {
          "count": 2,
          "mean": 2.33,
          "median": 2.33,
          "min": 2.33,
          "max": 2.33,
          "p25": 2.33,
          "p75": 2.33,
          "p90": 2.33,
          "stdev": 0.0
        },
        "constraint_count": {
          "count": 2,
          "mean": 4.0,
          "median": 4.0,
          "min": 4.0,
          "max": 4.0,
          "p25": 4.0,
          "p75": 4.0,
          "p90": 4.0,
          "stdev": 0.0
        },
        "interference_count": {
          "count": 2,
          "mean": 1.0,
          "median": 1.0,
          "min": 1.0,
          "max": 1.0,
          "p25": 1.0,
          "p75": 1.0,
          "p90": 1.0,
          "stdev": 0.0
        },
        "est_D": {
          "count": 2,
          "mean": 0.67,
          "median": 0.67,
          "min": 0.67,
          "max": 0.67,
          "p25": 0.67,
          "p75": 0.67,
          "p90": 0.67,
          "stdev": 0.0
        }
      },
      "BP-003": {
        "count": 2,
        "test_ids": [
          "TEST-005",
          "TEST-006"
        ],
        "passed_rate": 1.0,
        "difficulty_distribution": {
          "expert": 2
        },
        "difficulty_score": {
          "count": 2,
          "mean": 2.33,
          "median": 2.33,
          "min": 2.33,
          "max": 2.33,
          "p25": 2.33,
          "p75": 2.33,
          "p90": 2.33,
          "stdev": 0.0
        },
        "constraint_count": {
          "count": 2,
          "mean": 4.0,
          "median": 4.0,
          "min": 4.0,
          "max": 4.0,
          "p25": 4.0,
          "p75": 4.0,
          "p90": 4.0,
          "stdev": 0.0
        },
        "interference_count": {
          "count": 2,
          "mean": 1.0,
          "median": 1.0,
          "min": 1.0,
          "max": 1.0,
          "p25": 1.0,
          "p75": 1.0,
          "p90": 1.0,
          "stdev": 0.0
        },
        "est_D": {
          "count": 2,
          "mean": 0.67,
          "median": 0.67,
          "min": 0.67,
          "max": 0.67,
          "p25": 0.67,
          "p75": 0.67,
          "p90": 0.67,
          "stdev": 0.0
        }
      }
    },
    "by_primary_asset": {
      "KB-001": {
        "count": 6,
        "test_ids": [
          "TEST-001",
          "TEST-002",
          "TEST-003",
          "TEST-004",
          "TEST-005",
          "TEST-006"
        ],
        "passed_rate": 1.0,
        "difficulty_distribution": {
          "advanced": 2,
          "expert": 4
        },
        "difficulty_score": {
          "count": 6,
          "mean": 2.11,
          "median": 2.33,
          "min": 1.67,
          "max": 2.33,
          "p25": 1.83,
          "p75": 2.33,
          "p90": 2.33,
          "stdev": 0.34
        },
        "constraint_count": {
          "count": 6,
          "mean": 3.67,
          "median": 4.0,
          "min": 3.0,
          "max": 4.0,
          "p25": 3.25,
          "p75": 4.0,
          "p90": 4.0,
          "stdev": 0.52
        },
        "interference_count": {
          "count": 6,
          "mean": 0.67,
          "median": 1.0,
          "min": 0.0,
          "max": 1.0,
          "p25": 0.25,
          "p75": 1.0,
          "p90": 1.0,
          "stdev": 0.52
        },
        "est_D": {
          "count": 6,
          "mean": 0.54,
          "median": 0.67,
          "min": 0.28,
          "max": 0.67,
          "p25": 0.38,
          "p75": 0.67,
          "p90": 0.67,
          "stdev": 0.2
        }
      }
    }
  },
  "dataset_meta": {
    "version": "1.0",
    "domain": "纪检材料智能审查",
    "business_goal": "为纪检监察员提供党纪法规、总书记讲话、理论文章、实务案例的 AI 语义检索与文书纠错辅助",
    "success_metric": "纪检监察员在3分钟内获得准确党纪依据或定性量纪建议的比率 ≥ 90%",
    "created_at": "2026-05-07T23:06:31+08:00",
    "total_items": 6,
    "difficulty_distribution": {
      "advanced": 2,
      "expert": 4
    },
    "source_channel": "design_doc"
  }
}
```

## 下一阶段校验清单
- [x] 所有 TEST 的 passed=true
- [x] 覆盖矩阵盲区 severity=high 数 = 0
- [ ] 独立性评分 ≥ 0.5
- [x] dataset.json 结构校验通过
- [x] dataset.xlsx 已生成且关键 sheet 存在

## 备注与遗留问题
（无）
