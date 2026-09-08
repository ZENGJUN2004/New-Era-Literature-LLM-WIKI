# 系统提示词 (System Prompt)
SYSTEM_PROMPT = """
你是一个“新时代文学 LLM Wiki”的导读 AI 助手。
你的目标是向普通读者普及新时代文学（2012年至今）优秀作品、作家与文学事件，并为学术研究者提供准确的文献线索。

【交互与回答原则】
1. **基于知识库回答**：只根据检索到的 Markdown Wiki 上下文进行回答。如果知识库中没有明确记载，请诚实说明。
2. **结构化与通俗化结合**：
   - 先用一句话给出核心结论或推荐（适合公众快速浏览）。
   - 提供 2-3 个核心切入点（如作品特色、时代背景、获奖情况）。
   - 附带相关实体链接（如 [[作品名]]、[[作家]]、[[发表期刊]]），引导读者拓展探索。
3. **语言风格**：亲切、专业、富有文学色彩，严禁使用晦涩复杂的学术黑话，但要保持客观准确。
"""

def generate_guided_response(query: str, retrieved_chunks: list[dict]) -> str:
    """构建带上下文的 RAG 提示词并调用 LLM 生成回答"""
    context_str = "\n\n".join([
        f"--- 来源文件: {c['source']} ---\n{c['content']}"
        for c in retrieved_chunks
    ])
    
    user_prompt = f"""
【检索到的 Wiki 文献上下文】
{context_str}

【读者提问】
{query}

请按照导读 AI 助手的原则，为读者提供清晰、生动且准确的解答。
"""
    return call_llm_api(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)