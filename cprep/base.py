from dataclasses import dataclass
import os
from typing import List


@dataclass
class File:
    src_path: str
    kind: str
    exec_path: str = None

    @property
    def compiled(self):
        return self.exec_path is not None

    @property
    def ext(self):
        return os.path.splitext(self.src_path)[-1].lower()[1:]

    @property
    def name(self):
        return self.src_path.split('/')[-1].split('.')[0]


@dataclass
class EvalResult:
    verdict: str
    input: str = None
    output: str = None
    stderr: str = None
    time_exec_ms: int = -1
    memory_used: int = None
    info: str = None


@dataclass
class TestCase:
    args: List[str]
    special_args: List[str]
    input_text: str
    answer_text: str
    group_idx: int
    idx: int
    generator_name: str
    info: str

    @property
    def generated(self):
        return self.input_text and self.answer_text
