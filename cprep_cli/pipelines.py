import subprocess
from typing import Optional, List
import time
from colorama import Style, Fore
import os
import functools
import copy

from .utils import pad
from . import logger

from cprep import compilation, evaluation, generation, config, tests
from cprep.base import EvalResult, File, TestCase
from cprep.files import Files
from cprep.config import Config
import sys

RED_CROSS = (Fore.RED + (u'\u2717' if sys.stdout.encoding ==
                         'utf-8' else 'X') + Fore.RESET)

GREEN_TICK = (Fore.GREEN + (u'\u2713' if sys.stdout.encoding ==
                            'utf-8' else 'V') + Fore.RESET)

NON_DETERMINISTIC_WARNING = """\
Generator '{name}' seems to be non-deterministic.
While this is supported, it may cause problems with reproductibility.
Please make your generator deterministic, by setting the random seed either as constant, or as command argument.
   Example: `int seed = stoi(argv[1]); srand(seed);`"""

NO_VALIDATORS_FOUND_WARNING = "\
No validators found. It is recommended to \
have validators, to check generator output."


def discover_files(cfg: Config, solutions=None):
    patterns = cfg.discovery.patterns
    model_solution = cfg.generation.model_solution

    # If solutions are specified, discard the discovered solutions
    # and use the provided ones instead.
    files = Files("", patterns, model_solution=model_solution)
    if solutions:
        files.files = [f for f in files.files if f.kind != 'solution']
        for src_path in solutions:
            files.files.append(File(src_path=src_path, kind='solution'))

    print("Discovered files: ")
    pad_len = max(len(f.src_path) for f in files.files)
    for f in files.files:
        print(
            f" - {pad(f.src_path, pad_len)} {Style.BRIGHT}({f.kind}){Style.RESET_ALL}")
    print()

    return files


def compile_files(files: Files, cfg: Config):
    output_dir = os.path.join(cfg.temp_dir, cfg.compilation.exec_dir)
    print("Compiling all files...")
    ext_to_lang_config = {
        ext: lang_cfg
        for lang_cfg in cfg.compilation.languages.values()
        for ext in lang_cfg.exts}
    compile_files = [f for f in files.files if f.ext in ext_to_lang_config]
    pad_len = max(len(f.src_path) for f in compile_files)
    for f in compile_files:
        print(f" - {pad(f.src_path, pad_len)} ", end='', flush=True)
        lang_config = ext_to_lang_config[f.ext]
        compiled, used_cache = compilation.compile(f,
                                                   compile_args=lang_config.compile.split(),
                                                   output_dir=output_dir)
        line = GREEN_TICK if compiled else RED_CROSS
        if used_cache:
            line += f" {Style.DIM}(cached){Style.RESET_ALL}"
        print(line)
    print()


def compute_evaluation_results(
        files: Files,
        test_cases: List[TestCase],
        cfg: Config):
    time_limit_ms = cfg.problem.time_limit_ms
    timeout_multiplier = cfg.evaluation.timeout_multiplier
    tl_close_range = cfg.evaluation.tl_close_range
    problem_cfg = cfg.problem

    solution_files = files.solutions
    checker_file = files.checker

    col_len = 15
    header_str = ' '.join([' ' + pad('#', 3)] +
                          [pad(f.name, col_len) for f in solution_files])
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
                print(pad(f"{Style.DIM}-{Style.RESET_ALL}",
                          col_len), end=' ', flush=True)
                continue
            res = evaluation.evaluate_solution(
                sol, tc.input_text, tc.answer_text, problem_cfg,
                timeout_ms=time_limit_ms * timeout_multiplier,
                checker_file=checker_file)
            verdict = res.verdict
            while len(verdict) < 3:
                verdict += ' '
            if (res.verdict in ['TLE', 'AC'] and time_limit_ms
                    * tl_close_range[0] < res.time_exec_ms < time_limit_ms * tl_close_range[1]):
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


def _generate_test_cases(
        test_cases: List[TestCase],
        files: Files,
        cfg: Config):
    gen_cfg = cfg.generation
    problem_cfg = cfg.problem
    tests_dir = cfg.tests.tests_dir
    input_pattern = cfg.tests.input_pattern
    answer_pattern = cfg.tests.answer_pattern

    print(f"Generating {len(test_cases)} test cases...")
    print(
        f"Model solution: {Style.BRIGHT}{gen_cfg.model_solution}{Style.RESET_ALL}")

    checker_file = files.checker
    # print(f"Checker: {checker_file.name if checker_file else 'None'}")

    idx = 1
    # print(" ", end="")
    last_group_idx = 0
    for tc in test_cases:
        if tc.group_idx != last_group_idx:
            print("| ", end="")
        last_group_idx = tc.group_idx

        # Actual generation happens here.
        valid = generation.generate_test_case(
            tc, files, gen_cfg, problem_cfg)
        output = GREEN_TICK if valid else RED_CROSS
        if valid:
            if tc.info:
                output = f"[{output} {tc.info}]"
            # Write tests to disk.
            os.makedirs(tests_dir, exist_ok=True)
            with open(os.path.join(tests_dir, input_pattern.format(
                    idx=tc.idx, gen=tc.generator_name)), 'wb') as f:
                f.write(tc.input_text)
            with open(os.path.join(tests_dir, answer_pattern.format(
                    idx=tc.idx, gen=tc.generator_name)), 'wb') as f:
                f.write(tc.answer_text)
        else:
            tc.input_text = tc.answer_text = None

        print(output, end=" ", flush=True)

    print()
    print(f"Tests written to '{os.path.join('.', tests_dir, '')}'.")
    print()

    return test_cases


def generate_test_cases(
        test_cases: List[TestCase],
        files: Files,
        cfg: Config):
    run_deterministic_check = cfg.generation.run_deterministic_check
    run_duplicate_check = cfg.generation.run_duplicate_check

    generate = functools.partial(
        _generate_test_cases,
        test_cases, files, cfg)

    tick = time.time()
    generate()
    tock = time.time()

    if run_deterministic_check:
        time.sleep(max(0.1, 1.1 - (tock - tick)))
        nd_generators = set()
        for tc1 in test_cases:
            if tc1.generator_name in nd_generators:
                continue
            nd_generators.add(tc1.generator_name)
            tc2 = copy.deepcopy(tc1)
            generation.generate_test_case(
                tc2, files, cfg.generation, cfg.problem)
            if tc1.input_text != tc2.input_text:
                logger.warning(NON_DETERMINISTIC_WARNING.format(
                    name=tc1.generator_name))

    if run_duplicate_check:
        input_to_tcs = {}
        for tc in test_cases:
            tcs = input_to_tcs.get(tc.input_text, [])
            tcs.append(tc)
            input_to_tcs[tc.input_text] = tcs
        for tcs in input_to_tcs.values():
            if len(tcs) > 1:
                logger.warning(f"Found duplicate tests: [{', '.join(str(tc.idx) for tc in tcs)}]. "
                               "Please fix this by changing arguments or setting different seed values.")

    if not files.validators:
        logger.warning(NO_VALIDATORS_FOUND_WARNING)

    return test_cases


def load_tests(files: Files, cfg: Config):
    tests_cfg = cfg.tests
    return tests.load_tests(files, tests_cfg)
