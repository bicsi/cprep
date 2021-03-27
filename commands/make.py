import argparse 
import yaml
from colorama import Style, Fore
from dataclasses import dataclass
import os 
import string 
import time 

from lib import discovery, compiler, evaluation
from lib.base import ProblemCfg, File, TestCase
import re 
import contextlib 
import base64 
import random 


NON_DETERMINISTIC_WARNING = """\
WARNING: Generator '{name}' seems to be non-deterministic. 
While this is supported, it may cause problems with reproductibility.
Please make your generator deterministic, by setting the random seed either as constant, or as command argument.
   Example: `int seed = stoi(argv[1]); srand(seed);`
"""




def pad(s: str, n: int = 25):
    in_c = False
    char_pos = []
    for i, c in enumerate(s):
        # print(repr(c))
        if c == '\x1b':
            in_c = True
        if not in_c:
            char_pos.append(i)
        if c == 'm':
            in_c = False 
        
    if len(char_pos) > n:
        while len(char_pos) > n - 3:
            s = s[:char_pos[-1]] + s[(char_pos[-1] + 1):]
            char_pos.pop(-1)
        return s + '...'
    return s + ' ' * (n - len(char_pos))


def discover_files(base_dir, cfg):
    files = discovery.discover(
        base_dir=base_dir, 
        patterns=cfg['patterns'])
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
    

def generate_test_case(idx: int, group_idx: int, cmd: str, files, cfg):
    args = cmd.split()
    special = None
    if ' #' in cmd:
        base_cmd, special = cmd.split(' #', 1)
        special = special[1:].split() if special[0] == '!' else None 
        args = base_cmd.split()
    
    # Get generator.
    gen_name = args.pop(0).split('/')[-1]
    gen_files = [f for f in files if f.kind == 'generator' and f.name == gen_name]
    assert len(gen_files) == 1, f"Bad generator name: '{gen_name}'"
    [gen_file] = gen_files
    
    # Generate input and answer text from model solution.
    model_sol_name = cfg['problem'].model_solution
    model_sol_files = [f for f in files if f.kind == 'solution' and f.name == model_sol_name]
    assert len(model_sol_files) == 1, f"Did not find model solution: '{model_sol_name}'"
    [model_sol_file] = model_sol_files
    info = None

    if special is None:
        input_text = compiler.run(gen_file, args)
        model_eval_result = evaluation.run_solution(
            model_sol_file, input_text, cfg=cfg['problem'])
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
            curr_input_text = compiler.run(gen_file, [*args, salt])
            model_eval_result = evaluation.run_solution(
                model_sol_file, curr_input_text, cfg=cfg['problem'])
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
        cmd = " ".join([base_cmd.strip(), best_salt.decode('ascii')])
        info = str(round(best_value))
    else:
        raise ValueError(f"Unrecognized special kind: '{special[0]}'")

    # Write tests to disk.
    tests_dir = os.path.join(cfg['base_dir'], cfg['tests_dir'])
    os.makedirs(tests_dir, exist_ok=True)
    with open(os.path.join(tests_dir, 
            cfg['problem'].input_pattern.format(idx=idx)), 'wb') as f:
        f.write(input_text)
    with open(os.path.join(tests_dir, 
            cfg['problem'].answer_pattern.format(idx=idx)), 'wb') as f:
        f.write(answer_text)
        
    return TestCase(
        generator_name=gen_file.name,
        cmd=cmd, 
        input_text=input_text, 
        answer_text=answer_text, 
        group_idx=group_idx, 
        idx=idx,
        info=info)


def generate_test_cases(files, cfg):
    print("Generating test cases...")
    tests_files = [f for f in files if f.kind == 'tests']
    
    assert tests_files, "No tests files in problem directory."

    test_groups = [[]]

    for test_file in tests_files:
        with open(test_file.src_path) as f:
            first_line = True
            for line in f:
                if line.startswith('###') or first_line:
                    if test_groups[-1]:
                        test_groups.append([])
                first_line = False
                if line.startswith('#'):
                    continue 
                test_groups[-1].append(line.strip())
    if not test_groups[-1]:
        test_groups.pop()
    
    result = []
    idx = 1
    print(" ", end="")
    last_group_idx = 0
    for group_idx, group in enumerate(test_groups):
        if group_idx != last_group_idx:
            print("| ", end="")
        for cmd in group:
            tc = generate_test_case(idx, group_idx, cmd, files, cfg)
            result.append(tc)
            idx += 1
            output = f'{Fore.GREEN}\u2713{Fore.RESET}'
            if tc.info:
                output += " " + tc.info
            print(output, end=" ", flush=True)
    print()
    print()
    return result

def make_tests(files, cfg):
    tick = time.time()
    test_cases = generate_test_cases(files, cfg)
    tock = time.time()
    if cfg['run_deterministic_check']:
        time.sleep(max(0.1, 1.1 - (tock - tick)))
        with contextlib.redirect_stdout(open(os.devnull, 'w')):
            chk_test_cases = generate_test_cases(files, cfg)
        nd_generators = set()
        for tc1, tc2 in zip(test_cases, chk_test_cases):
            if tc1.generator_name in nd_generators or tc1.input_text == tc2.input_text:
                continue
            print(Fore.YELLOW + Style.BRIGHT + NON_DETERMINISTIC_WARNING.format(
                name=tc1.generator_name) + Fore.RESET + Style.RESET_ALL)
            input("Press [ENTER] to continue: ")
            print()
            nd_generators.add(tc1.generator_name)

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
            res = evaluation.evaluate_solution(
                sol, tc.input_text, tc.answer_text, cfg=cfg['problem'])
            verdict = res.verdict
            time_limit_ms = cfg['problem'].time_limit_ms
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


def run_make(cfg, args):
    # problem = args.problem
    with open(os.path.join(cfg['base_dir'], 'config.yaml')) as f:
        cfg['problem'] = ProblemCfg(**yaml.load(f, Loader=yaml.FullLoader))
    
    files = discover_files(cfg['base_dir'], cfg['discovery'])

    compile_files(files, cfg['compiler'])

    make_tests(files, cfg)
        


