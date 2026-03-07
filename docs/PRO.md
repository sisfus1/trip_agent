模块,最终技术选型,核心工程点
感知层,MCP + 实时 API,通过 MCP Server 屏蔽异构 API 差异，提供标准化实时气象与交通数据 [cite: 2026-03-07]。
记忆层,ChromaDB,实现用户出行偏好的向量化存储，支持基于上下文的长效个性化推荐 [cite: 2026-03-07]。
交互层,Gemini Live + Vue3,支持实时语音通话（Gemini Live）与 极简 Web 交互界面的无缝切换 [cite: 2026-03-07]。
决策层,A2A 协商 (LangGraph),Planner 与 Budget 智能体在多约束条件（如：低预算 vs 高品质）下自主博弈 [cite: 2026-03-07]。
部署层,HuggingFace,利用 Docker 封装，部署至 HuggingFace 边缘节点，实现轻量化上线 [cite: 2026-03-07]。