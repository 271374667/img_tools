from abc import ABC, abstractmethod


class BaseProcessor(ABC):
    @abstractmethod
    def process_dir(self, *args, **kwargs): ...

    @abstractmethod
    def process(self, *args, **kwargs): ...
