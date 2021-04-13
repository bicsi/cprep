import shutil
import argparse
from colorama import Fore, Style
import os 
import sys 


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("name")


DIRECTORY_EXISTS_MESSAGE = """\
There is already a file/directory at '{dst_path}'. Testutil will not overwrite it.
If you do want to overwrite the existing data, manually delete the directory 
and run `{cmd}` again. \
"""


def run(cfg, args):
    problem_config_file = 'config.yaml'
    src_path = os.path.join(os.path.dirname(__file__), '..', 'skel')
    dst_path = os.path.join('.', args.name)
    proc_name = sys.argv[0].split('/')[-1]
    if os.path.exists(dst_path):
        print(Fore.RED + DIRECTORY_EXISTS_MESSAGE.format(
            dst_path=dst_path, cmd=' '.join([proc_name, *sys.argv[1:]])) + Fore.RESET)
    else:
        shutil.copytree(src_path, dst_path)
        print(f"To edit metadata about the problem, look for `{problem_config_file}` inside the folder.")
        print(f"To make the tests, make sure you are inside the directory and run `{proc_name} generate`")
        print(f"To evaluate the solutions, run `{proc_name} evaluate`")
        print(Fore.GREEN + f"Problem '{args.name}' created successfully!" + Fore.RESET)