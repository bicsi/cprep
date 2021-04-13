from typing import List
import os

from .base import File, TestCase
from .config import ProblemConfig, TestsConfig
from .files import Files


def load_tests(files: Files, cfg: TestsConfig):
    tests_dir = cfg.tests_dir
    input_pattern = cfg.input_pattern
    answer_pattern = cfg.answer_pattern

    tests_files = files.tests

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
    test_cases = []
    idx = 1
    for group_idx, group in enumerate(test_groups):
        for cmd in group:
            if not cmd.strip():
                continue 
            args = cmd.split()
            special = None
            if ' #' in cmd:
                base_cmd, special = cmd.split(' #', 1)
                special = special[1:].split() if special[0] == '!' else None 
                args = base_cmd.split()
            
            # Get generator.
            gen_name = args.pop(0).split('/')[-1]
            gen_files = [f for f in files.generators if f.name == gen_name]
            assert len(gen_files) == 1, f"Bad generator name: '{gen_name}'"
            [gen_file] = gen_files

            # Read input and answer.
            input_path = os.path.join(tests_dir, input_pattern.format(idx=idx, gen=gen_file.name))
            answer_path = os.path.join(tests_dir, answer_pattern.format(idx=idx, gen=gen_file.name))
            input_text, answer_text = None, None
            if os.path.exists(input_path):
                with open(input_path, 'rb') as f:
                    input_text = f.read()
            if os.path.exists(answer_path):
                with open(answer_path, 'rb') as f:
                    answer_text = f.read()

            test_cases.append(TestCase(
                args=args, special_args=special, 
                input_text=input_text, answer_text=answer_text, 
                group_idx=group_idx, idx=idx,  
                generator_name=gen_file.name, info=None,
            ))
            idx += 1
    return test_cases
    
