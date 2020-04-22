#!/usr/bin/env python3

import os
import sys

from incremental_atg.discover import *
from incremental_atg.incremental_atg import *


def main():
    # What's the path to our repo?
    s2n_repo_path = os.path.abspath(os.path.expandvars("${HOME}/clones/s2n_vc/src/s2n"))

    # What's the path to our Manage root folder?
    s2n_manage_path = os.path.abspath(os.path.expandvars("${HOME}/clones/s2n_vc/vcast"))

    # What's the path to root src tree?
    s2n_src_path = os.path.dirname(s2n_repo_path)

    # Set the environment variable needed for the environments to build
    os.environ["S2N_VC_SRC_PATH"] = s2n_src_path

    # What two shas do we want to analyse?
    current_sha = "c158f0c8cb190b5121702fbe0e2b16547c5b63b4"
    new_sha = "4caa406c233b57e6f0bb7d5a62c83aca237b7e31"

    # Use our class to find the changed files for a given repo
    dcf = DiscoverChangedFiles(s2n_repo_path)

    # Get the changed files between our two commits
    changed_files = dcf.get_changed_files(current_sha, new_sha)

    debugging = False

    if debugging:
        for a_file in changed_files:
            print(a_file)

    #
    # Use our class to find the relationship between files/VectorCAST
    # environments
    #
    dmd = DiscoverManageDependencies(s2n_manage_path, s2n_repo_path)
    dmd.calculate_deps()

    # Mapping from files to environments that use those files
    fnames_to_envs = dmd.fnames_to_envs

    # Mapping from environments to the routines in those environments
    envs_to_routines = dmd.envs_to_routines

    # Mapping from environments to the name of the unit for that environment
    envs_to_units = dmd.envs_to_units

    # Find all of the used files across the whole of the Manage project
    dep_files = set(fnames_to_envs.keys())

    #
    # Calculate the intersection between the _used_ files and the _changed_
    # files
    #
    changed_used_files = changed_files.intersection(dep_files)

    # Our set of impacted environments
    impacted_envs = set()

    # For each _used and changed_ file ...
    for changed_file in changed_used_files:
        # ... we want to process the environments using those files
        impacted_envs.update(fnames_to_envs[changed_file])

    # Debug: show the environments we're going to process
    print("Envs to process:")
    for env in impacted_envs:
        print(env)

    # How much time do we want to give ATG?
    timeout = int(sys.argv[1])

    # Debug
    print("ATG will have {:d} seconds per routine".format(timeout))

    # Create an incremental ATG objec
    ia = IncrementalATG(
        s2n_manage_path, impacted_envs, envs_to_routines, envs_to_units, timeout
    )

    # Process our environments
    ia.process()


if __name__ == "__main__":
    main()

# EOF
