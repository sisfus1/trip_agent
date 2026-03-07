# VTP 项目背景与开发者画像
# 此文件用于为 AI 提供研发上下文，请勿删除 [cite: 2026-03-07]

## 1. 开发者信息
- **姓名**：朱奇
- **背景**：数字媒体技术专业大三在读，擅长 Python 异步编程及音视频底层重构。
- **代表作**：Auto-Media-Agent (解决了 asyncio/gevent 死锁及 MoviePy 渲染 Bug)。

## 2. 当前项目：Vibe-Travel-Pilot (VTP)
- **目标**：冲击字节、英伟达实习的高质量 Agent 项目。
- **核心架构**：基于 MCP 协议的数据层 + LangGraph 驱动的多智能体 A2A 协商层 [cite: 2026-03-07]。
- **交互方式**：语音 (Gemini Live) 与文本 UI 双模切换。
- **存储方案**：使用 ChromaDB 作为向量数据库，构建具备“时间锚点”的 RAG 记忆流 [cite: 2026-03-07]。
- **部署目标**：HuggingFace Spaces (Serverless)。
## 3. 项目核心路线图 (Ref: /docs/PRD.md)
- **当前阶段**：MVP 开发（实现 MCP 基础连接与 A2A 基础对话） [cite: 2026-03-07]。
- **核心功能约束**：
  - 必须支持 Gemini Live 与文本 UI 的双模切换。
  - 存储必须使用 ChromaDB 进行向量化索引。
- **详见文档**：请在需要深入理解业务逻辑时，主动阅读项目根目录下的 `docs/PRD.md`。