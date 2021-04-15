import shutil
import argparse
from colorama import Fore, Style
from pathlib import Path
import sys 
from .. import USER_CONFIG_DIR

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("name")


DIRECTORY_EXISTS_MESSAGE = """\
There is already a file/directory at '{dst_path}'. Testutil will not overwrite it.
If you do want to overwrite the existing data, manually delete the directory 
and run `{cmd}` again. \
"""


def run(cfg, args):
    problem_config_file = 'config.yaml'
    src_path = Path(USER_CONFIG_DIR).expanduser() / 'template'
    if not src_path.exists():
        print("Using default template.")
        src_path = Path(__file__).parent.parent / 'userdata' / 'template'
    else:
        print(Style.BRIGHT + f"Using custom template at: {src_path}" + Style.RESET_ALL)
    
    dst_path = Path('.') / args.name 
    proc_name = sys.argv[0].split('/')[-1]
    if dst_path.exists():
        print(Fore.RED + DIRECTORY_EXISTS_MESSAGE.format(
            dst_path=dst_path, cmd=' '.join([proc_name, *sys.argv[1:]])) + Fore.RESET)
    else:
        shutil.copytree(src_path, dst_path)
        print(f"To edit metadata about the problem, look for `{problem_config_file}` inside the folder.")
        print(f"To make the tests, make sure you are inside the directory and run `{proc_name} generate`")
        print(f"To evaluate the solutions, run `{proc_name} evaluate`")
        print(Fore.GREEN + f"Problem '{args.name}' created successfully!" + Fore.RESET)