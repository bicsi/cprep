import argparse
import shutil 


parser = argparse.ArgumentParser(add_help=False)


def run(cfg, args):
    shutil.rmtree(cfg.temp_dir)
    shutil.rmtree(cfg.tests.tests_dir)

    