import argparse
from .. import pipelines
import os 
import yaml 


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("tests", nargs="*", 
    help="Test ids to generate (1-based; default: all)")


def run(cfg, args):
    files = pipelines.discover_files(cfg)

    pipelines.compile_files(files, cfg)
    
    test_cases = pipelines.load_tests(files, cfg)
    
    # Filter test cases depending on argument.
    if args.tests:
        new_test_cases = []
        for tc in test_cases:
            for t in args.tests:
                if '-' in t:
                    tb, te = map(int, t.split('-'))
                else:
                    tb, te = int(t), int(t)
                if tb <= tc.idx <= te:
                    new_test_cases.append(tc)
                    continue
        test_cases = new_test_cases

    pipelines.generate_test_cases(test_cases, files, cfg)

    