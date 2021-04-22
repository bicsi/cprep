from .base import File 
from . import config
import glob 
import os 


KINDS = ['generator', 'validator', 'solution', 'tests']


def _discover(patterns, base_dir="", **kwargs):
    result = []
    for p in patterns:
        kind = p.kind
        if kind not in KINDS:
            # logger.warning(f"Unknown kind: {kind}. Skipping pattern...")
            continue
        files = glob.glob(os.path.join(base_dir, p.pattern.format(**kwargs)))
        for filepath in files:
            if not any(f.src_path == filepath for f in result):
                result.append(File(src_path=filepath, kind=kind))
    result.sort(key=lambda x: x.src_path)
    return result



class Files:
    def __init__(self, base_dir, patterns, model_solution=None, **pattern_kwargs):
        self.files = _discover(patterns, base_dir, **pattern_kwargs)
        self.model_sol_path = model_solution
            
    def _all(self, kind: str):
        return [f for f in self.files if f.kind == kind]

    def _get(self, kind: str, path: str = None):
        files = self._all(kind)
        if path:
            files = [f for f in files if f.src_path == path]

        assert len(files) <= 1, f"Multiple {kind}s found: {files}"
        return files[0] if files else None 

    @property
    def generators(self): 
        return self._all('generator')
    
    @property
    def validators(self):
        return self._all('validator')
    
    @property
    def solutions(self):
        return self._all('solution')
    
    @property 
    def checker(self):
        return self._get('checker')

    @property
    def tests(self):
        return self._all('tests')

    @property
    def model_solution(self):
        return self._get('solution', path=self.model_sol_path)

