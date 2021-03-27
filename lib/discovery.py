from collections import OrderedDict
import glob 
import os 
from loguru import logger
from lib.base import File 


KINDS = ['generator', 'validator', 'solution', 'tests']


def discover(base_dir, patterns):
    result = []
    for p in patterns:
        kind = p['kind']
        if kind not in KINDS:
            logger.warning(f"Unknown kind: {kind}. Skipping pattern...")
            continue
        files = glob.glob(os.path.join(base_dir, p['pattern']))
        for filepath in files:
            if not any(f.src_path == filepath for f in result):
                result.append(File(src_path=filepath, kind=kind))
    result.sort(key=lambda x: x.src_path)
    return result


