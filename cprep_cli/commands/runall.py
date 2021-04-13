import argparse 
import yaml
import os 
from .. import pipelines


parser = argparse.ArgumentParser(add_help=False)


def run(cfg, args):

    files = pipelines.discover_files(cfg)
    
    pipelines.compile_files(files, cfg)

    test_cases = pipelines.load_tests(files, cfg)

    pipelines.generate_test_cases(test_cases, files, cfg)
    
    pipelines.compute_evaluation_results(files, test_cases, cfg)


