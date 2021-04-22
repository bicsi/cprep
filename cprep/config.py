from dataclasses import dataclass, is_dataclass
from typing import Tuple, List, Dict, Optional
import yaml 
from pydantic import BaseModel 

class ProblemConfig(BaseModel):
    name: str
    input_file: str 
    output_file: str 
    time_limit_ms: float 


class GenerationConfig(BaseModel):
    run_deterministic_check: bool 
    run_duplicate_check: bool
    num_workers: int
    model_solution: str 
    

class EvaluationConfig(BaseModel):
    timeout_multiplier: float 
    tl_close_range: Tuple[float, float]


class TestsConfig(BaseModel):
    tests_dir: str 
    input_pattern: str 
    answer_pattern: str 
    

class LanguageConfig(BaseModel):
    exts: List[str]
    compile: Optional[str]
    run: str

    
class CompilationConfig(BaseModel):
    exec_dir: str
    languages: Dict[str, LanguageConfig]


class Pattern(BaseModel):
    kind: str 
    pattern: str 


class DiscoveryConfig(BaseModel):
    patterns: List[Pattern]

    

class Config(BaseModel):
    debug: bool 
    temp_dir: str 
    discovery: DiscoveryConfig
    compilation: CompilationConfig
    problem: ProblemConfig
    generation: GenerationConfig 
    tests: TestsConfig
    evaluation: EvaluationConfig
    problem: ProblemConfig
   
