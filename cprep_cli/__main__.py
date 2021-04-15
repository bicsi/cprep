#!/usr/bin/env python3
import argparse
import os
import yaml
from colorama import Fore
import sys
import shutil
from pathlib import Path

from . import commands
from cprep.config import Config
from . import USER_CONFIG_DIR
import os
from dataclasses import is_dataclass
from typing import List


def parse_args():
    parser = argparse.ArgumentParser(
        description="Cprep - preparing contests made easy")
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


def load_config(args):
    cfg = {}

    def merge_rec(d1: dict, d2: dict):
        for k, v in d2.items():
            child = d1.get(k, {})
            if isinstance(v, dict):
                merge_rec(child, v)
            else:
                child = v
            d1[k] = child

    def load_rec(typ, d):
        if is_dataclass(typ):
            assert isinstance(d, dict), f"Format error: '{d}'"
            kwargs = {}
            fields = typ.__dataclass_fields__
            for k, v in d.items():
                kwargs[k] = load_rec(fields[k].type, v)
            return typ(**kwargs)
        elif isinstance(typ, List):
            assert False
        return d

    def load_path(path):
        if not path.exists():
            return False
        with open(path, 'r') as f:
            d = yaml.load(f, Loader=yaml.FullLoader)
            if d:
                merge_rec(cfg, d)
        return True

    assert load_path(Path(__file__).parent / 'config.yaml')
    user_path = Path(USER_CONFIG_DIR).expanduser() / 'config.yaml'
    if not user_path.exists():
        os.makedirs(user_path.parent, exist_ok=True)
        shutil.copy(Path(__file__).parent / 'userdata' /
                    'config.yaml', user_path)
    assert load_path(user_path)
    if (not load_path(Path('.') / 'config.yaml') and
            args.command not in ['create', 'config']):
        print()
        print(
            f"{Fore.RED}[E]: You don't seem to be inside a problem directory (file 'config.yaml' not found){Fore.RESET}")
        print(f"Note: If using an older version, "
              "please rename and reconfigure 'problem.yaml' file to match "
              f"the structure of `{sys.argv[0].split('/')[-1]} config`")
        exit(6)
    return Config(**cfg)


def main():
    args = parse_args()
    cfg = load_config(args)
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
