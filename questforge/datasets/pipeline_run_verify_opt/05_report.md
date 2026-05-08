---
stage: 5
stage_name: validation_and_finalize
version: 1.0
upstream: 04_tests.md
downstream: 最终产物
domain: 纪检材料智能审查
created_at: 2026-05-08T00:46:22+08:00
created_by: agent-stage5
pass_gate: false
---

# Stage 5 · 验证报告 + benchmark

## 摘要
4 道题中 3 道通过 5 设计原则验证；覆盖矩阵高/中/低严重度问题分别为 0/0/0；先验区分度分级={'待改进': 1, '优秀': 3}；独立性评分 0.5。

## 5 设计原则验证
| TEST | 真实性 | 闭环性 | 可量化 | 区分度 | 预测力 | passed |
|---|---|---|---|---|---|---|
| TEST-001 | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| TEST-002 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TEST-003 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TEST-004 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## 覆盖矩阵对齐(实际 vs 蓝图)
| TEST | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 蓝图=重点 / 实际=覆盖✓ / 点数=3 | 蓝图=常规 / 实际=覆盖✓ / 点数=4 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 | 蓝图=常规 / 实际=覆盖✓ / 点数=2 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 |
| TEST-002 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 | 蓝图=重点 / 实际=覆盖✓ / 点数=4 | 蓝图=重点 / 实际=覆盖✓ / 点数=6 | 蓝图=常规 / 实际=覆盖✓ / 点数=2 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 |
| TEST-003 | 蓝图=重点 / 实际=覆盖✓ / 点数=3 | 蓝图=常规 / 实际=覆盖✓ / 点数=4 | 蓝图=重点 / 实际=覆盖✓ / 点数=7 | 蓝图=常规 / 实际=覆盖✓ / 点数=2 | 蓝图=常规 / 实际=覆盖✓ / 点数=3 |
| TEST-004 | 蓝图=重点 / 实际=覆盖✓ / 点数=4 | 蓝图=重点 / 实际=覆盖✓ / 点数=7 | 蓝图=重点 / 实际=覆盖✓ / 点数=6 | 蓝图=重点 / 实际=覆盖✓ / 点数=2 | 蓝图=重点 / 实际=覆盖✓ / 点数=3 |

## 盲区清单
（无）

## 先验区分度估计
| TEST | est_D | 分级 | 主要贡献项 |
|---|---|---|---|
| TEST-001 | 0.23 | 待改进 | 难度偏低但可作为基线题 |
| TEST-002 | 0.58 | 优秀 | 约束密度高 / 干扰设计强 / 跨资产整合 |
| TEST-003 | 0.58 | 优秀 | 约束密度高 / 干扰设计强 / 跨资产整合 |
| TEST-004 | 0.82 | 优秀 | 约束密度高 / 干扰设计强 / 跨资产整合 / 难度偏高 |

## 独立性评分
- 最高重合对:TEST-002 × TEST-003, overlap = 0.5
- independence_score = 0.5

| pair | asset | keyword | step | pair_overlap |
|---|---|---|---|---|
| TEST-002 × TEST-003 | 1.0 | 0.0 | 0.0 | 0.5 |
| TEST-001 × TEST-002 | 0.5 | 0.0 | 0.0 | 0.25 |
| TEST-001 × TEST-003 | 0.5 | 0.0 | 0.0 | 0.25 |
| TEST-001 × TEST-004 | 0.33 | 0.0 | 0.0 | 0.17 |
| TEST-002 × TEST-004 | 0.25 | 0.1 | 0.0 | 0.15 |
| TEST-003 × TEST-004 | 0.25 | 0.0 | 0.0 | 0.12 |

## 分群聚合统计
- 全集 4 道,passed_rate=0.75,难度分布={'basic': 1, 'advanced': 2, 'expert': 1}
- difficulty_score: mean=2.08 / median=2.17 / p25=2.04 / p75=2.21 / p90=2.28
- est_D: mean=0.55 / p25=0.49 / p75=0.64
- 完整数据见 `dataset_supplementary/aggregations.json`

**按难度分群**
| difficulty | count | passed_rate | diff_score.mean | 约束.mean | 干扰.mean | est_D.mean |
|---|---|---|---|---|---|---|
| advanced | 2 | 1.0 | 2.17 | 3.0 | 1.0 | 0.58 |
| basic | 1 | 0.0 | 1.67 | 2.0 | 0.0 | 0.23 |
| expert | 1 | 1.0 | 2.33 | 3.0 | 2.0 | 0.82 |

**按用户画像分群**(每道题可能命中多个 UG)
| user_group | count | passed_rate | diff_score.mean | est_D.mean |
|---|---|---|---|---|
| UG-001 | 4 | 0.75 | 2.08 | 0.55 |

## 最终产物清单
- `dataset.json` — /Users/sin/Documents/Data/ccic/0418_智能体评测实现/questforge/datasets/pipeline_run_verify_opt/dataset.json
- `dataset.xlsx` — /Users/sin/Documents/Data/ccic/0418_智能体评测实现/questforge/datasets/pipeline_run_verify_opt/dataset.xlsx
- `05_report.md` — /Users/sin/Documents/Data/ccic/0418_智能体评测实现/questforge/datasets/pipeline_run_verify_opt/05_report.md
- `traceability.json` — /Users/sin/Documents/Data/ccic/0418_智能体评测实现/questforge/datasets/pipeline_run_verify_opt/traceability.json
- `dataset_supplementary/` — /Users/sin/Documents/Data/ccic/0418_智能体评测实现/questforge/datasets/pipeline_run_verify_opt/dataset_supplementary

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
        "prediction_power": false,
        "passed": false,
        "notes": [
          "角色=纪检监察员",
          "真实性=2/2"
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
          "角色=纪检监察员",
          "真实性=4/4",
          "metric_hits=定性量纪建议/定性量纪建议书/量纪建议书/定性量纪/执纪执法指导性"
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
          "角色=纪检监察员",
          "真实性=4/4",
          "metric_hits=文书纠错/送达外国公民/邮寄送达外国/送达外国/制定审查调查"
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
          "角色=纪检监察员",
          "真实性=5/5",
          "metric_hits=党纪条款引用/纪检监察员/依据整合/政策依据"
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
          "points": 3
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
          "blueprint": "重点",
          "covered": true,
          "rich": true,
          "points": 4
        },
        "方案生成": {
          "blueprint": "重点",
          "covered": true,
          "rich": true,
          "points": 6
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
      "TEST-003": {
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
          "points": 4
        },
        "拆解问题": {
          "blueprint": "重点",
          "covered": true,
          "rich": true,
          "points": 7
        },
        "方案生成": {
          "blueprint": "重点",
          "covered": true,
          "rich": true,
          "points": 6
        },
        "执行落地": {
          "blueprint": "重点",
          "covered": true,
          "rich": true,
          "points": 2
        },
        "元认知": {
          "blueprint": "重点",
          "covered": true,
          "rich": true,
          "points": 3
        }
      }
    },
    "coverage_gaps": [],
    "discrimination_estimate": {
      "TEST-001": {
        "est_D": 0.23,
        "grade": "待改进",
        "difficulty_score_normalized": 0.33,
        "constraint_density_normalized": 0.5,
        "interference_density_normalized": 0.0,
        "cross_asset_degree_normalized": 0.0,
        "major_contributors": [
          "难度偏低但可作为基线题"
        ]
      },
      "TEST-002": {
        "est_D": 0.58,
        "grade": "优秀",
        "difficulty_score_normalized": 0.58,
        "constraint_density_normalized": 0.75,
        "interference_density_normalized": 0.5,
        "cross_asset_degree_normalized": 0.5,
        "major_contributors": [
          "约束密度高",
          "干扰设计强",
          "跨资产整合"
        ]
      },
      "TEST-003": {
        "est_D": 0.58,
        "grade": "优秀",
        "difficulty_score_normalized": 0.58,
        "constraint_density_normalized": 0.75,
        "interference_density_normalized": 0.5,
        "cross_asset_degree_normalized": 0.5,
        "major_contributors": [
          "约束密度高",
          "干扰设计强",
          "跨资产整合"
        ]
      },
      "TEST-004": {
        "est_D": 0.82,
        "grade": "优秀",
        "difficulty_score_normalized": 0.67,
        "constraint_density_normalized": 0.75,
        "interference_density_normalized": 1.0,
        "cross_asset_degree_normalized": 1.0,
        "major_contributors": [
          "约束密度高",
          "干扰设计强",
          "跨资产整合",
          "难度偏高"
        ]
      }
    },
    "independence_score": 0.5,
    "most_overlapping_pair": [
      "TEST-002",
      "TEST-003"
    ],
    "pair_details": [
      {
        "pair": [
          "TEST-002",
          "TEST-003"
        ],
        "asset_overlap": 1.0,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.5
      },
      {
        "pair": [
          "TEST-001",
          "TEST-002"
        ],
        "asset_overlap": 0.5,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.25
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
        "asset_overlap": 0.33,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.17
      },
      {
        "pair": [
          "TEST-002",
          "TEST-004"
        ],
        "asset_overlap": 0.25,
        "keyword_overlap": 0.1,
        "step_overlap": 0.0,
        "pair_overlap": 0.15
      },
      {
        "pair": [
          "TEST-003",
          "TEST-004"
        ],
        "asset_overlap": 0.25,
        "keyword_overlap": 0.0,
        "step_overlap": 0.0,
        "pair_overlap": 0.12
      }
    ]
  },
  "aggregations": {
    "global": {
      "count": 4,
      "test_ids": [
        "TEST-001",
        "TEST-002",
        "TEST-003",
        "TEST-004"
      ],
      "passed_rate": 0.75,
      "difficulty_distribution": {
        "basic": 1,
        "advanced": 2,
        "expert": 1
      },
      "difficulty_score": {
        "count": 4,
        "mean": 2.08,
        "median": 2.17,
        "min": 1.67,
        "max": 2.33,
        "p25": 2.04,
        "p75": 2.21,
        "p90": 2.28,
        "stdev": 0.29
      },
      "constraint_count": {
        "count": 4,
        "mean": 2.75,
        "median": 3.0,
        "min": 2.0,
        "max": 3.0,
        "p25": 2.75,
        "p75": 3.0,
        "p90": 3.0,
        "stdev": 0.5
      },
      "interference_count": {
        "count": 4,
        "mean": 1.0,
        "median": 1.0,
        "min": 0.0,
        "max": 2.0,
        "p25": 0.75,
        "p75": 1.25,
        "p90": 1.7,
        "stdev": 0.82
      },
      "est_D": {
        "count": 4,
        "mean": 0.55,
        "median": 0.58,
        "min": 0.23,
        "max": 0.82,
        "p25": 0.49,
        "p75": 0.64,
        "p90": 0.75,
        "stdev": 0.24
      }
    },
    "by_difficulty": {
      "advanced": {
        "count": 2,
        "test_ids": [
          "TEST-002",
          "TEST-003"
        ],
        "passed_rate": 1.0,
        "difficulty_distribution": {
          "advanced": 2
        },
        "difficulty_score": {
          "count": 2,
          "mean": 2.17,
          "median": 2.17,
          "min": 2.17,
          "max": 2.17,
          "p25": 2.17,
          "p75": 2.17,
          "p90": 2.17,
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
          "mean": 0.58,
          "median": 0.58,
          "min": 0.58,
          "max": 0.58,
          "p25": 0.58,
          "p75": 0.58,
          "p90": 0.58,
          "stdev": 0.0
        }
      },
      "basic": {
        "count": 1,
        "test_ids": [
          "TEST-001"
        ],
        "passed_rate": 0.0,
        "difficulty_distribution": {
          "basic": 1
        },
        "difficulty_score": {
          "count": 1,
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
          "count": 1,
          "mean": 2.0,
          "median": 2.0,
          "min": 2.0,
          "max": 2.0,
          "p25": 2.0,
          "p75": 2.0,
          "p90": 2.0,
          "stdev": 0.0
        },
        "interference_count": {
          "count": 1,
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
          "count": 1,
          "mean": 0.23,
          "median": 0.23,
          "min": 0.23,
          "max": 0.23,
          "p25": 0.23,
          "p75": 0.23,
          "p90": 0.23,
          "stdev": 0.0
        }
      },
      "expert": {
        "count": 1,
        "test_ids": [
          "TEST-004"
        ],
        "passed_rate": 1.0,
        "difficulty_distribution": {
          "expert": 1
        },
        "difficulty_score": {
          "count": 1,
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
          "count": 1,
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
          "count": 1,
          "mean": 2.0,
          "median": 2.0,
          "min": 2.0,
          "max": 2.0,
          "p25": 2.0,
          "p75": 2.0,
          "p90": 2.0,
          "stdev": 0.0
        },
        "est_D": {
          "count": 1,
          "mean": 0.82,
          "median": 0.82,
          "min": 0.82,
          "max": 0.82,
          "p25": 0.82,
          "p75": 0.82,
          "p90": 0.82,
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
        "passed_rate": 0.75,
        "difficulty_distribution": {
          "basic": 1,
          "advanced": 2,
          "expert": 1
        },
        "difficulty_score": {
          "count": 4,
          "mean": 2.08,
          "median": 2.17,
          "min": 1.67,
          "max": 2.33,
          "p25": 2.04,
          "p75": 2.21,
          "p90": 2.28,
          "stdev": 0.29
        },
        "constraint_count": {
          "count": 4,
          "mean": 2.75,
          "median": 3.0,
          "min": 2.0,
          "max": 3.0,
          "p25": 2.75,
          "p75": 3.0,
          "p90": 3.0,
          "stdev": 0.5
        },
        "interference_count": {
          "count": 4,
          "mean": 1.0,
          "median": 1.0,
          "min": 0.0,
          "max": 2.0,
          "p25": 0.75,
          "p75": 1.25,
          "p90": 1.7,
          "stdev": 0.82
        },
        "est_D": {
          "count": 4,
          "mean": 0.55,
          "median": 0.58,
          "min": 0.23,
          "max": 0.82,
          "p25": 0.49,
          "p75": 0.64,
          "p90": 0.75,
          "stdev": 0.24
        }
      }
    },
    "by_source_process": {
      "BP-001": {
        "count": 1,
        "test_ids": [
          "TEST-001"
        ],
        "passed_rate": 0.0,
        "difficulty_distribution": {
          "basic": 1
        },
        "difficulty_score": {
          "count": 1,
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
          "count": 1,
          "mean": 2.0,
          "median": 2.0,
          "min": 2.0,
          "max": 2.0,
          "p25": 2.0,
          "p75": 2.0,
          "p90": 2.0,
          "stdev": 0.0
        },
        "interference_count": {
          "count": 1,
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
          "count": 1,
          "mean": 0.23,
          "median": 0.23,
          "min": 0.23,
          "max": 0.23,
          "p25": 0.23,
          "p75": 0.23,
          "p90": 0.23,
          "stdev": 0.0
        }
      },
      "BP-002": {
        "count": 1,
        "test_ids": [
          "TEST-002"
        ],
        "passed_rate": 1.0,
        "difficulty_distribution": {
          "advanced": 1
        },
        "difficulty_score": {
          "count": 1,
          "mean": 2.17,
          "median": 2.17,
          "min": 2.17,
          "max": 2.17,
          "p25": 2.17,
          "p75": 2.17,
          "p90": 2.17,
          "stdev": 0.0
        },
        "constraint_count": {
          "count": 1,
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
          "count": 1,
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
          "count": 1,
          "mean": 0.58,
          "median": 0.58,
          "min": 0.58,
          "max": 0.58,
          "p25": 0.58,
          "p75": 0.58,
          "p90": 0.58,
          "stdev": 0.0
        }
      },
      "BP-003": {
        "count": 1,
        "test_ids": [
          "TEST-003"
        ],
        "passed_rate": 1.0,
        "difficulty_distribution": {
          "advanced": 1
        },
        "difficulty_score": {
          "count": 1,
          "mean": 2.17,
          "median": 2.17,
          "min": 2.17,
          "max": 2.17,
          "p25": 2.17,
          "p75": 2.17,
          "p90": 2.17,
          "stdev": 0.0
        },
        "constraint_count": {
          "count": 1,
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
          "count": 1,
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
          "count": 1,
          "mean": 0.58,
          "median": 0.58,
          "min": 0.58,
          "max": 0.58,
          "p25": 0.58,
          "p75": 0.58,
          "p90": 0.58,
          "stdev": 0.0
        }
      },
      "BP-004": {
        "count": 1,
        "test_ids": [
          "TEST-004"
        ],
        "passed_rate": 1.0,
        "difficulty_distribution": {
          "expert": 1
        },
        "difficulty_score": {
          "count": 1,
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
          "count": 1,
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
          "count": 1,
          "mean": 2.0,
          "median": 2.0,
          "min": 2.0,
          "max": 2.0,
          "p25": 2.0,
          "p75": 2.0,
          "p90": 2.0,
          "stdev": 0.0
        },
        "est_D": {
          "count": 1,
          "mean": 0.82,
          "median": 0.82,
          "min": 0.82,
          "max": 0.82,
          "p25": 0.82,
          "p75": 0.82,
          "p90": 0.82,
          "stdev": 0.0
        }
      }
    },
    "by_primary_asset": {
      "KB-001": {
        "count": 4,
        "test_ids": [
          "TEST-001",
          "TEST-002",
          "TEST-003",
          "TEST-004"
        ],
        "passed_rate": 0.75,
        "difficulty_distribution": {
          "basic": 1,
          "advanced": 2,
          "expert": 1
        },
        "difficulty_score": {
          "count": 4,
          "mean": 2.08,
          "median": 2.17,
          "min": 1.67,
          "max": 2.33,
          "p25": 2.04,
          "p75": 2.21,
          "p90": 2.28,
          "stdev": 0.29
        },
        "constraint_count": {
          "count": 4,
          "mean": 2.75,
          "median": 3.0,
          "min": 2.0,
          "max": 3.0,
          "p25": 2.75,
          "p75": 3.0,
          "p90": 3.0,
          "stdev": 0.5
        },
        "interference_count": {
          "count": 4,
          "mean": 1.0,
          "median": 1.0,
          "min": 0.0,
          "max": 2.0,
          "p25": 0.75,
          "p75": 1.25,
          "p90": 1.7,
          "stdev": 0.82
        },
        "est_D": {
          "count": 4,
          "mean": 0.55,
          "median": 0.58,
          "min": 0.23,
          "max": 0.82,
          "p25": 0.49,
          "p75": 0.64,
          "p90": 0.75,
          "stdev": 0.24
        }
      }
    }
  },
  "dataset_meta": {
    "version": "1.0",
    "domain": "纪检材料智能审查",
    "business_goal": "为纪检监察员提供党纪法规、总书记讲话、理论文章、实务案例的 AI 语义检索与文书纠错辅助",
    "success_metric": "纪检监察员在 3 分钟内获得准确的党纪条款引用、定性量纪建议或文书纠错反馈，准确率 ≥95%",
    "created_at": "2026-05-08T00:46:22+08:00",
    "total_items": 4,
    "difficulty_distribution": {
      "basic": 1,
      "advanced": 2,
      "expert": 1
    },
    "source_channel": "design_doc"
  }
}
```

## 下一阶段校验清单
- [ ] 所有 TEST 的 passed=true
- [x] 覆盖矩阵盲区 severity=high 数 = 0
- [x] 独立性评分 ≥ 0.5
- [x] dataset.json 结构校验通过
- [x] dataset.xlsx 已生成且关键 sheet 存在

## 备注与遗留问题
（无）
