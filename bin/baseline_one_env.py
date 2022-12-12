#!/usr/bin/env python

# Standard includes
import pathlib
import sys
import os

# Get our parent dir
parent_dir = pathlib.Path(__file__).parent.parent.resolve()

# Add it to the front of path
sys.path.insert(0, str(parent_dir))

# Grab the baseliner
from atg_execution.baseline_for_atg import Baseline


def baseline(env_script):
    """
    Baselines the given script 'env_script'
    """
    os.environ["VCAST_ATG_BASELINING"] = "1"
    bl = Baseline(env_file=str(env_script), verbose=True, disable_failures=False)

    # If you don't want to iterate at all
    #
    # FIXME: this is temporary and you don't really want this
    max_iter = 1
    bl.run(copy_out_manage=False, max_iter=max_iter)

    return 0


def main():
    """
    Main to help run a baseliner
    """

    # Correct number of args?
    if len(sys.argv) != 2:
        this_script = pathlib.Path(__file__).name
        print("Incorrect arguments:")
        print("")
        print(f"    {this_script} <env name>")
        print("")
        return -1

    # Correct type of first arg?
    env_script = pathlib.Path(sys.argv[1])
    if (not env_script.exists()) or env_script.suffix != ".env":
        print(f"Provided env script {env_script} is not valid")
        return -1

    # Llets run!
    return baseline(env_script)


if __name__ == "__main__":
    sys.exit(main())

# EOF
