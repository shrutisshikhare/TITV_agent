from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs) -> dict[str, Any]:
        pass

    def to_tool_spec(self) -> dict:
        """Returns the tool spec in OpenAI function-calling format."""
        raise NotImplementedError("Subclasses must define to_tool_spec()")
