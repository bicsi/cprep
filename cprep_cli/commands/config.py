import yaml
import argparse


parser = argparse.ArgumentParser(add_help=False)


def run(cfg, args):
    print(yaml.dump(cfg.dict()))