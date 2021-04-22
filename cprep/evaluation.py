import subprocess
from .base import EvalResult, File
from .config import ProblemConfig
from typing import Optional
import time
import os


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


def run_solution(
        sol_file: File, input: str, cfg: ProblemConfig,
        timeout_ms: float = None, run_twice: bool = True):
    if not sol_file.compiled:
        return EvalResult(verdict='CE')
    res = EvalResult(verdict='AC')

    n_iters = 2 if run_twice else 1

    time_exec_ms = timeout_ms
    exec_dir = os.path.dirname(sol_file.exec_path)
    input_path = os.path.join(exec_dir, cfg.input_file)
    output_path = os.path.join(exec_dir, cfg.output_file)

    for i in range(n_iters):
        res.verdict = 'AC'
        tick = time.time()

        with open(input_path, 'wb') as f:
            f.write(input)

        try:
            subprocess_result = subprocess.run(
                [os.path.join('.', os.path.basename(sol_file.exec_path))],
                cwd=exec_dir,
                check=True,
                shell=True,
                capture_output=True,
                timeout=(timeout_ms/1000 if timeout_ms else None),
                input=(input if cfg.input_file == 'stdin' else None))
            res.stderr = subprocess_result.stderr

            if cfg.output_file == 'stdout':
                res.output = subprocess_result.stdout
                with open(output_path, 'wb') as f:
                    f.write(res.output)
            else:
                with open(output_path, 'rb') as f:
                    res.output = f.read()

        except subprocess.CalledProcessError as ex:
            res.verdict = 'RE'
            res.info = str(ex)
        except subprocess.TimeoutExpired as ex:
            res.verdict = 'TLE'

        tock = time.time()
        time_exec_ms = (tock - tick) * 1000.

    res.time_exec_ms = time_exec_ms
    res.input = input
    return res


def evaluate_solution(
        sol_file: File, input: str, answer: str, cfg: ProblemConfig,
        timeout_ms: float = None, checker_file: Optional[File] = None,
        run_twice: bool = True):
    res = run_solution(
        sol_file, input, 
        cfg, timeout_ms=timeout_ms, 
        run_twice=run_twice)
    if res.verdict == 'AC' and res.time_exec_ms > cfg.time_limit_ms:
        res.verdict = 'TLE'
    if (res.verdict == 'AC' and not check_output(
            input, res.output, answer, checker_file)):
        res.verdict = 'WA'
    return res
