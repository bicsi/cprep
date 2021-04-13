#!/usr/bin/env python3
import argparse
import os 
import yaml 
from colorama import Fore 
import sys 

from . import commands 
from cprep import config


def parse_args():
    parser = argparse.ArgumentParser(description="Cprep - preparing contests made easy")
    subparsers = parser.add_subparsers(help='commands', dest='cmd')
    subparsers.required = True
    
    for command_module in [
            commands.runall, commands.create, 
            commands.evaluate, commands.generate, 
            commands.clean, commands.config]:
        name = command_module.__name__.split('.')[-1]
        subparser = subparsers.add_parser(
            name, parents=[command_module.parser])
        subparser.set_defaults(
            run=command_module.run, 
            command=name)

    return parser.parse_args()


def main():
    args = parse_args()
    dicts = []
    for config_path in [
            os.path.join(os.path.dirname(__file__), 'config.yaml'), 
            os.path.expanduser(os.path.join('~', '.cprep.yaml')),
            "config.yaml"]:
        if not os.path.exists(config_path):
            if config_path == 'config.yaml' and args.command not in ['create', 'config']:
                print()
                print(f"{Fore.RED}[E]: You don't seem to be inside a problem directory (file 'config.yaml' not found){Fore.RESET}")
                print(f"Note: If using an older version, "
                    "please rename and reconfigure 'problem.yaml' file to match "
                    f"the structure of `{sys.argv[0].split('/')[-1]} config`")
                exit(6)
            continue
        with open(config_path, 'r') as f:
            dicts.append(yaml.load(f, Loader=yaml.FullLoader))
    cfg = config.load(*dicts)
    if cfg.debug:
        print(yaml.dump(cfg.dict()))

    try:
        args.run(cfg, args)
    except AssertionError as ex:
        print()
        print(f"{Fore.RED}[E]: {ex}{Fore.RESET}")
        exit(6)


if __name__ == "__main__":
    main()