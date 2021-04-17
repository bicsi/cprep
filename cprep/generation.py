from .base import TestCase, File
from .config import TestsConfig, ProblemConfig, GenerationConfig
from typing import List, Optional
import os
from . import compilation, evaluation
import base64 
import random
import functools 
import multiprocessing
from .files import Files 


def _clean_text(text: str):
    if not text:
        return text
    lines = []
    for line in text.splitlines():
        lines.append(line.rstrip())
    return b"".join(line + b'\n' for line in lines)


def _generate_test_case(
        gen_file: File, 
        model_sol_file: File, 
        valid_files: List[File],
        cfg: ProblemConfig,
        args: List[str],
        salt: str = None):
    if salt:
        args = args + [salt]
    input_text = compilation.run(gen_file, args)
    for valid_file in valid_files:
        if not validate_test_case(input_text, valid_file, cfg):
            return None
    model_eval_result = evaluation.run_solution(
        model_sol_file, input_text, cfg, timeout_ms=cfg.time_limit_ms*3)
    model_eval_result.input = _clean_text(model_eval_result.input)
    model_eval_result.output = _clean_text(model_eval_result.output)
    return model_eval_result


def _evaluate(
        sol: File, checker: Optional[File], cfg: ProblemConfig,
        input: str, answer: str, timeout_ms: Optional[float] = None):
    return evaluation.evaluate_solution(
        sol, input, answer, cfg,
        timeout_ms=timeout_ms, 
        checker_file=checker)


def _chunk(iterable, k):
    ret = []
    for x in iterable:
        ret.append(x)
        if len(ret) == k:
            yield ret 
            ret.clear()
    if ret:
        yield ret 


def _generate_stress_goal(
        generate: callable, 
        goal: str, n_iters: int, num_workers: int):
    goal_idx = int(goal[1:])
    best_value, best_salt = -2e100, None
    input_text, answer_text = None, None

    salts = [str(i) for i in range(n_iters)]

    pool = multiprocessing.Pool(num_workers)
    for chunk_salts in _chunk(salts, num_workers):
        results = pool.map(generate, chunk_salts)
        for salt, res in zip(chunk_salts, results):
            if not res:
                continue 
            # print(res.input.decode('utf-8'))
            assert res.verdict == 'AC', "Model solution did not run successfully"
            stderr_lines = res.stderr.splitlines()
            assert stderr_lines, "Model solution did not output values on stderr for stress-test optimization"
            obj_values = list(map(float, stderr_lines[-1].split()))
            assert len(obj_values) > goal_idx, f"Model solution did not output any value for {goal}"
            obj_value = obj_values[goal_idx]
            if best_value < obj_value:
                best_value = obj_value 
                input_text = res.input
                answer_text = res.output
                best_salt = salt
    return best_value, best_salt, input_text, answer_text


def _generate_stress_fail(
        generate: callable,
        evaluate: callable,
        n_iters: int, 
        num_workers: int):

    best_time, best_verdict, best_salt = 1e9, 'AC', None
    input_text, answer_text = None, None 
    def key(verdict):
        return (0 if verdict == 'AC' else 1 if verdict == 'TLE' else 2)

    salts = (str(i) for i in range(n_iters))
    
    pool = multiprocessing.Pool(num_workers)

    for chunk_salts in _chunk(salts, num_workers):
        print(chunk_salts)
        if key(best_verdict) > 1:
            break
        model_results = pool.map(generate, chunk_salts)
        sol_results = pool.starmap(evaluate, [
            (m_res.input, m_res.output) 
            for m_res in model_results if m_res])

        for salt, m_res in zip(chunk_salts, model_results):
            if not m_res:
                continue
            assert m_res.verdict == 'AC', "Model solution did not run successfully"
            s_res = sol_results.pop(0)
            
            print(m_res.input, s_res)

            if (key(best_verdict), best_time < key(s_res.verdict), s_res.time_exec_ms):
                best_verdict, best_time = s_res.verdict, s_res.time_exec_ms
                best_salt = salt 
                input_text, answer_text = m_res.input, m_res.output
            if key(best_verdict) > 1:
                break

    return best_verdict, best_time, best_salt, input_text, answer_text



def generate_test_case(
        tc: TestCase, files: Files, 
        gen_cfg: GenerationConfig, 
        problem_cfg: ProblemConfig):
    num_workers = gen_cfg.num_workers

    gen_files = [f for f in files.generators if f.name == tc.generator_name]
    assert len(gen_files) == 1, f"Did not find generator: '{tc.generator_name}'"
    [gen_file] = gen_files

    model_sol_file = files.model_solution
    assert model_sol_file, f"Did not find model solution: '{files.model_sol_name}'"

    valid_files = files.validators
    checker_file = files.checker
    
    tc.input_text, tc.answer_text = None, None 

    # Generate input and answer text from model solution.
    info = None
    special = tc.special_args
    generate = functools.partial(
        _generate_test_case, 
        gen_file, model_sol_file, 
        valid_files, problem_cfg, tc.args,
    )

    if not special:
        result = generate()
        if result: 
            assert result.verdict == 'AC', "Model solution did not run successfully"
            tc.input_text, tc.answer_text = result.input, result.output

    elif special[0] == 'stress-goal':
        [_, goal, n_iters] = special 
        n_iters = int(n_iters)
        best_value, best_salt, tc.input_text, tc.answer_text = \
            _generate_stress_goal(generate, goal, n_iters, num_workers)    
        tc.info = str(round(best_value))

    elif special[0] == 'stress-fail':
        [_, target, n_iters] = special 
        n_iters = int(n_iters)
        
        target_sols = [f for f in files.solutions if f.name == target]
        assert len(target_sols) == 1, f"Target solution: '{target}' not found."
        [target_sol] = target_sols
        
        evaluate = functools.partial(_evaluate, target_sol, checker_file, problem_cfg)
        
        best_verdict, best_time, best_salt, tc.input_text, tc.answer_text = \
            _generate_stress_fail(generate, evaluate, n_iters, num_workers)    
        tc.info = f"{best_verdict} ({round(best_time)})"
    
    else:
        raise ValueError(f"Unrecognized special kind: '{special[0]}'")
    
    return tc.generated


def validate_test_case(input_text: str, valid_file: File, cfg: ProblemConfig):
    assert valid_file.compiled, "Validator is not compiled."
    result = evaluation.run_solution(
        valid_file, input_text, cfg, run_twice=False)
    return result.verdict == 'AC'
