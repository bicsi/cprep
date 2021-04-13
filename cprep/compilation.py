from typing import List
import subprocess 
import os 
from loguru import logger 
import time
import hashlib

from cprep.base import File, EvalResult


def compile(f: File, compile_args: List[str], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f.name)
    cache_path = os.path.join(output_dir, 'cache.txt')
    compile_args = [
        arg.format(exec_path=output_path, src_path=f.src_path)
        for arg in compile_args]

    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as stream:
            for line in stream:
                if line:
                    k, v = line.strip().split()
                    cache[k] = v
    assert os.path.exists(f.src_path), f"File '{f.src_path}' does not exist."
    with open(f.src_path, 'r') as stream:
        sha = hashlib.sha256(stream.read().encode('utf-8')).hexdigest()
    if cache.get(f.name) == sha and os.path.isfile(output_path):
        f.exec_path = output_path
        return True, True

    try:
        subprocess.run(compile_args, check=True, capture_output=True)
        f.exec_path = output_path
        cache[f.name] = sha 
        with open(cache_path, 'w') as stream:
            for k, v in cache.items(): 
                stream.write(f"{k} {v}\n")
        return True, False
    except subprocess.CalledProcessError as ex:
        return False, False 


def run(f: File, args: List[str]):
    assert f.compiled, f"File '{f.src_path}' not compiled"
    output = subprocess.run([f.exec_path] + args, check=True, capture_output=True)
    return output.stdout






