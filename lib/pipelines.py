import subprocess
from lib.base import EvalResult, File, ProblemCfg, TestCase
from typing import Optional, List
import time 
from lib import discovery, compiler, evaluation
from lib.utils import pad 
from colorama import Style, Fore 
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


def discover_files(base_dir, cfg, solutions=None):
    files = discovery.discover(
        base_dir=base_dir, 
        patterns=cfg['patterns'])
    # If solutions are specified, discard the discovered solutions
    # and use the provided ones instead.
    if solutions:
        files = [f for f in files if f.kind != 'solution']
        for src_path in solutions:
            files.append(File(src_path=src_path, kind='solution'))
        
    print("Discovered files: ")
    pad_len = max(len(f.src_path) for f in files)
    for f in files:
        print(f" - {pad(f.src_path, pad_len)} {Style.BRIGHT}({f.kind}){Style.RESET_ALL}")
    print()
    return files


def compile_files(files, cfg):
    print("Compiling all cpp files...")
    files = [f for f in files if f.ext == 'cpp']
    pad_len = max(len(f.name) for f in files)
    for f in files:
        print(f" - {pad(f.name, pad_len)} ", end='', flush=True)
        base_dir = os.path.dirname(f.src_path)
        compiled, used_cache = compiler.compile(f, 
            gcc_path=cfg['g++'], gcc_args=cfg['args'], 
            output_dir=os.path.join(base_dir, cfg['output_dir']))

        if compiled:
            line = f'{Fore.GREEN}\u2713{Fore.RESET}'
        else:
            line = f'{Fore.RED}\u00d7{Fore.RESET}'
        if used_cache:
            line += f" {Style.DIM}(cached){Style.RESET_ALL}"
        print(line)
    print()


def compute_evaluation_results(
        files: List[File], 
        test_cases: List[TestCase], 
        cfg: ProblemCfg):
    solution_files = [f for f in files if f.kind == 'solution']

    col_len = 15
    header_str = ' '.join([' ' + pad('#', 3)] + [pad(f.name, col_len) for f in solution_files])
    table_len = len(header_str)

    print("Evaluation results:")
    print(header_str)
    print('=' * table_len)

    last_group_idx = 0
    for tc in test_cases:
        if last_group_idx != tc.group_idx:
            print('-' * table_len)
        last_group_idx = tc.group_idx

        print(' ' + pad(str(tc.idx), 3), end=' ', flush=True)

        # Evaluate and print results for each solution.
        for sol in solution_files:
            if not tc.generated:
                print(pad(f"{Style.DIM}-{Style.RESET_ALL}", col_len), end=' ', flush=True)
                continue
            res = evaluation.evaluate_solution(
                sol, tc.input_text, tc.answer_text, cfg=cfg)
            verdict = res.verdict
            time_limit_ms = cfg.time_limit_ms
            while len(verdict) < 3:
                verdict += ' '
            if res.verdict in ['TLE', 'AC'] and time_limit_ms * 0.8 < res.time_exec_ms < time_limit_ms * 1.2:
                verdict = Fore.YELLOW + verdict + Fore.RESET
            elif res.verdict == 'AC':
                verdict = Fore.GREEN + verdict + Fore.RESET
            else:
                verdict = Fore.RED + verdict + Fore.RESET
            cell_text = f"{verdict}"
            if res.time_exec_ms >= 0:
                cell_text += f" {Style.DIM}({round(res.time_exec_ms)} ms){Style.RESET_ALL}"
            print(pad(cell_text, col_len), end=' ', flush=True)
        print()
    print('=' * table_len)
    print()