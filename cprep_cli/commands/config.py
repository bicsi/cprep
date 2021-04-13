import yaml
import argparse
import json


parser = argparse.ArgumentParser(
    add_help=False, 
    description="Dumps the current configuration",
)


def run(cfg, args):
    # We do this line only to replace tuples by lists.
    d = json.loads(json.dumps(cfg.dict()))
    print(yaml.dump(d))