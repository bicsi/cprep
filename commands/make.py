import argparse 
import yaml
from colorama import Style, Fore
from dataclasses import dataclass
import os 
import string 
import time 

from lib import discovery, compiler, evaluation, pipelines, tests
from lib.utils import pad 

from lib.base import ProblemCfg, File, TestCase
import re 
import contextlib 
import base64 
import random 
from typing import List 



NON_DETERMINISTIC_WARNING = """\
WARNING: Generator '{name}' seems to be non-deterministic. 
While this is supported, it may cause problems with reproductibility.
Please make your generator deterministic, by setting the random seed either as constant, or as command argument.
   Example: `int seed = stoi(argv[1]); srand(seed);`
"""
    

def generate_test_case(tc: TestCase, gen_file: File, model_sol_file: File, tests_dir: str, cfg: ProblemCfg):
    # Generate input and answer text from model solution.
    info = None
    special = tc.special_args

    if not special:
        input_text = compiler.run(gen_file, tc.args)
        model_eval_result = evaluation.run_solution(
            model_sol_file, input_text, cfg=cfg)
        assert model_eval_result.verdict == 'AC', "Model solution did not run successfully"
        answer_text = model_eval_result.output

    elif special[0] == 'stress-goal':
        [_, goal, n_iters] = special 
        n_iters = int(n_iters)
        goal_idx = int(goal[1])
        best_value = -2e100
        best_salt = None
        for it in range(n_iters):
            salt = base64.b64encode(random.randbytes(8))
            curr_input_text = compiler.run(gen_file, [*tc.args, salt])
            model_eval_result = evaluation.run_solution(
                model_sol_file, curr_input_text, cfg=cfg)
            assert model_eval_result.verdict == 'AC', "Model solution did not run successfully"
            stderr_lines = model_eval_result.stderr.splitlines()
            assert stderr_lines, "Model solution did not output values on stderr for stress-test optimization"
            obj_values = list(map(float, stderr_lines[-1].split()))
            assert len(obj_values) > goal_idx, f"Model solution did not output any value for {goal}"
            obj_value = obj_values[goal_idx]
            if best_value < obj_value:
                best_value = obj_value 
                input_text = curr_input_text
                answer_text = model_eval_result.output
                best_salt = salt
        cmd = " ".join([*tc.args, best_salt.decode('ascii')])
        info = str(round(best_value))
    else:
        raise ValueError(f"Unrecognized special kind: '{special[0]}'")

    # Write tests to disk.
    os.makedirs(tests_dir, exist_ok=True)
    with open(os.path.join(tests_dir, 
            cfg.input_pattern.format(idx=tc.idx)), 'wb') as f:
        f.write(input_text)
    with open(os.path.join(tests_dir, 
            cfg.answer_pattern.format(idx=tc.idx)), 'wb') as f:
        f.write(answer_text)

    tc.input_text = input_text
    tc.info = info 
    tc.answer_text = answer_text


def generate_test_cases(test_cases: List[TestCase], files: List[File], tests_dir: str, cfg: ProblemCfg):
    print("Generating test cases...")

    model_sol_name = cfg.model_solution
    model_sol_files = [f for f in files if f.kind == 'solution' and f.name == model_sol_name]
    assert len(model_sol_files) == 1, f"Did not find model solution: '{model_sol_name}'"
    [model_sol_file] = model_sol_files
    print(f"Model solution: {Style.BRIGHT}{model_sol_file.src_path}{Style.RESET_ALL}")

    idx = 1
    print(" ", end="")
    last_group_idx = 0
    for tc in test_cases:
        if tc.group_idx != last_group_idx:
            print("| ", end="")
        last_group_idx = tc.group_idx
        
        gen_files = [f for f in files if f.kind == 'generator' 
                and f.name == tc.generator_name]
        assert len(gen_files) == 1, f"Did not find generator: '{tc.generator_name}'"
        [gen_file] = gen_files

        generate_test_case(tc, gen_file, model_sol_file, tests_dir, cfg)
        output = f'{Fore.GREEN}\u2713{Fore.RESET}'
        if tc.info:
            output += " " + tc.info
        print(output, end=" ", flush=True)
    print()
    print()
    return test_cases


def make_tests(files, cfg):
    test_cases = tests.load_tests(files, cfg['tests_dir'], cfg['problem'])
    tick = time.time()
    generate_test_cases(test_cases, files, cfg['tests_dir'], cfg['problem'])
    tock = time.time()
    if cfg['run_deterministic_check']:
        time.sleep(max(0.1, 1.1 - (tock - tick)))
        chk_test_cases = test_cases.copy()
        with contextlib.redirect_stdout(open(os.devnull, 'w')):
            generate_test_cases(test_cases, model_sol_file, cfg['tests_dir'], cfg['problem'])
        nd_generators = set()
        for tc1, tc2 in zip(test_cases, chk_test_cases):
            if tc1.generator_name in nd_generators or tc1.input_text == tc2.input_text:
                continue
            print(Fore.YELLOW + Style.BRIGHT + NON_DETERMINISTIC_WARNING.format(
                name=tc1.generator_name) + Fore.RESET + Style.RESET_ALL)
            input("Press [ENTER] to continue: ")
            print()
            nd_generators.add(tc1.generator_name)
    return test_cases
    


def run_make(cfg, args):
    # problem = args.problem
    with open(os.path.join(cfg['base_dir'], 'config.yaml')) as f:
        cfg['problem'] = ProblemCfg(**yaml.load(f, Loader=yaml.FullLoader))
    
    files = pipelines.discover_files(cfg['base_dir'], cfg['discovery'])
    pipelines.compile_files(files, cfg['compiler'])

    test_cases = make_tests(files, cfg)
    pipelines.compute_evaluation_results(
        files, test_cases, cfg['problem'])


