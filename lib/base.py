from dataclasses import dataclass

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
        return self.src_path.rsplit('.', 1)[1].lower()
    
    @property 
    def name(self):
        return self.src_path.rsplit('/', 1)[1].split('.')[0]


@dataclass
class EvalResult:
    verdict: str
    output: str = None
    stderr: str = None
    time_exec_ms: int = -1
    memory_used: int = None
    info: str = None

  
@dataclass
class TestCase:
    cmd: str 
    input_text: str 
    answer_text: str 
    group_idx: int 
    idx: int
    generator_name: str
    info: str


@dataclass
class ProblemCfg:
    input_file: str 
    output_file: str 
    time_limit_ms: int
    model_solution: str 
    input_pattern: str 
    answer_pattern: str 
