from abc import ABC, abstractmethod


class BaseLoader(ABC):
    @abstractmethod
    def load(self, source: str) -> list[str]:
        ...

    @abstractmethod
    def supports(self, source: str) -> bool:
        ...