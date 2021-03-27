import subprocess
from lib.base import EvalResult, File, ProblemCfg
from typing import Optional
import time 


def check_output(input: str, output: str, answer: str, 
        checker_file: Optional[File] = None):
    assert checker_file is None, "Checkers are not supported."

    output = output.splitlines()
    answer = answer.splitlines()
    if len(output) != len(answer):
        return False  
    for l1, l2 in zip(output, answer):
        if l1.rstrip() != l2.rstrip():
            return False 
    return True



def run_solution(sol_file: File, input: str, cfg: ProblemCfg, run_twice: bool = True):
    if not sol_file.compiled:
        return EvalResult(verdict='CE') 
        
    timeout_ms = cfg.time_limit_ms * 3
    res = EvalResult(verdict='AC')

    n_iters = 2 if run_twice else 1

    time_exec_ms = timeout_ms
    for i in range(n_iters):
        tick = time.time()
        try:
            presult = subprocess.run(
                [sol_file.exec_path], 
                check=True, capture_output=True, 
                timeout=timeout_ms/1000, 
                input=input)
            res.output = presult.stdout
        except subprocess.CalledProcessError as ex:
            res.verdict = 'RE'
            res.info = str(ex)
        except subprocess.TimeoutExpired as ex:
            res.verdict = 'TLE'
        tock = time.time()
        time_exec_ms = min(time_exec_ms, (tock - tick) * 1000.)

    if res.verdict == 'AC' and time_exec_ms > cfg.time_limit_ms:
        res.verdict = 'TLE'
    res.time_exec_ms = time_exec_ms
    return res 
    

def evaluate_solution(
        sol_file: File, input: str, answer: str, 
        cfg: ProblemCfg, 
        checker_file: Optional[File] = None):
    res = run_solution(sol_file, input, cfg)
    if (res.verdict == 'AC' and not check_output(
            input, res.output, answer, checker_file)):
        res.verdict = 'WA'
    return res
