# 提示词优化器
class PromptOptimizer:
    def optimize_prompt(self, original_prompt: str) -> str:
        """
        Optimize the given prompt following OpenAI's best practices.
        """
        # 1. Add clear context and role
        optimized_prompt = f"""You are a helpful AI assistant. Please respond to the following request:

{original_prompt}

Please provide your response following these guidelines:
1. Be specific and detailed in your answer
2. If relevant, break down complex tasks into steps
3. Format your response appropriately
4. If you're unsure about anything, ask for clarification
"""
        
        # 2. Add system-level instructions
        optimized_prompt = self._add_system_instructions(optimized_prompt)
        
        return optimized_prompt

    def _add_system_instructions(self, prompt: str) -> str:
        """Add system-level instructions to guide response format and quality."""
        system_instructions = """
Important:
- Provide step-by-step explanations when applicable
- Use markdown formatting for better readability
- Include examples when helpful
- If you need any clarification, please ask
"""
        return f"{prompt}\n{system_instructions}"