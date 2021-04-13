import argparse
from .. import pipelines
import os 
import yaml 


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("solutions", nargs="*", help="Solution source files (default: all matching)")


def run(cfg, args):
    
    files = pipelines.discover_files(cfg, solutions=args.solutions)
    
    pipelines.compile_files(files, cfg)
    
    test_cases = pipelines.load_tests(files, cfg)
    
    pipelines.compute_evaluation_results(
        files, test_cases, cfg)

    