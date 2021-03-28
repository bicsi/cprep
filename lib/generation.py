from lib.base import TestCase, File, ProblemCfg
from typing import List 
import os
from lib import compiler, evaluation
import base64 
import random


def generate_test_case(
        tc: TestCase, gen_file: File, 
        model_sol_file: File, tests_dir: str, cfg: ProblemCfg):
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

    tc.input_text = input_text
    tc.info = info 
    tc.answer_text = answer_text


def validate_test_case(tc: TestCase, valid_file: File, cfg: ProblemCfg):
    assert valid_file.compiled, "Validator is not compiled."
    result = evaluation.run_solution(
        valid_file, tc.input_text, cfg, run_twice=False)
    return result.verdict == 'AC'