import argparse
from lib import pipelines, tests
import os 
from lib.base import ProblemCfg
import yaml 


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("solutions", nargs="*", help="Solution source files (default: all matching)")


def run(cfg, args):
    
    files = pipelines.discover_files(cfg, solutions=args.solutions)
    
    pipelines.compile_files(files, cfg['temp_dir'], cfg['compiler'])
    
    test_cases = tests.load_tests(files, cfg['tests_dir'], cfg['problem'])
    
    pipelines.compute_evaluation_results(
        files, test_cases, cfg['problem'])

    