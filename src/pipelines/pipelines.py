import logging
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from src.llm_manager import LLMManager
from src.context_manager import ContextManager
from src.text_search import TextSearch
from src.agents import AgenticAI

logger = logging.getLogger(__name__)

class CommandPipeline:
    def __init__(self, automation):
        self.llm_manager = LLMManager()
        self.context_manager = ContextManager()
        self.text_search = TextSearch()
        self.automation = automation  # Use the passed automation instance
        self.agentic_ai = AgenticAI()

    async def process(self, command: str, context=None):
        """Process command through modular pipeline."""
        if context is None:
            context = self.context_manager.get_context()

        # NLP intent detection with Spacy
        intent = self.classify_command_with_nlp(command)

        # Agentic AI for multi-step workflows
        if intent == "complex":
            return self.agentic_ai.execute_workflow(command)

        # General question answering
        action_type = self.classify_command(command)  # Use existing classify_command for now
        if action_type == "automation":
            result = self.automation.execute(command)
        else:
            result = await self.llm_manager.query(command, context)

        # Post-process (placeholder for plugins, as none are implemented yet)
        # result = self.plugins.post_process(result, command)  # Commented out as plugins are undefined
        return {"command": command, "result": result}

    def classify_command(self, command):
        """Classify command type for routing (temporary fallback to VoiceProcessor logic)."""
        if not command:
            return "unknown"
        command_lower = command.lower()
        if any(keyword in command_lower for keyword in ["open", "change", "reject", "order", "shut down"]):
            if "summarize" in command_lower and "http" in command_lower:
                return "web_summary"
            return "automation"
        elif any(keyword in command_lower for keyword in ["read", "summarize", "what"]):
            return "query"
        elif "search for" in command_lower:
            return "search"
        elif "reply to this" in command_lower:
            return "email_reply"
        logger.warning(f"Unrecognized command: {command}")
        return "unknown"

    def classify_command_with_nlp(self, command):
        """Use Spacy for intent detection (placeholder)."""
        # Implementation with Spacy (not implemented yet, using fallback)
        return "intent" if "complex" in command.lower() else self.classify_command(command)