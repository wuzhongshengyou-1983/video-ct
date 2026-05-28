"""
fire_eye — 数据采集六族子包

战略文档：docs/01-战略/16-数据采集模块化架构.md

六族（Family）：
  F1 平台数据源      — TikHub / 抖音开放平台 / 快手 / B站
  F2 技术元数据源    — FFprobe / Qwen VL 画质评分
  F3 AI内容理解源    — ASR（SenseVoice）/ OCR / LLM摘要
  F4 趋势竞品源      — 竞品搜索 / LLM知识基准
  F5 LLM诊断后端    — CT诊断官 Agent
  F6 播放QoE源      — 前端埋点 / ClickHouse（v3启用）

当前状态（v2.5）：各族逻辑散落在 services/ 平级文件中，
本子包是统一入口，逐步将各族迁移至此。

入口：DataSourceRegistry（registry.py）
数据契约：VideoCTContext（contracts.py）
三步流水线：Pipeline（pipeline.py）
"""
