#!/usr/bin/env python3

import os
import sys

import incremental_atg.discover as atg_discover
import incremental_atg.process_project as atg_processor
import incremental_atg.misc as atg_misc
import incremental_atg.scm_hooks as atg_scm_hooks

def do_s2n():
    # What's the path to our repo?
    repo_path = os.path.abspath(os.path.expandvars("${HOME}/clones/vc/src/s2n"))

    # What's the path to our Manage root folder?
    manage_path = os.path.abspath(os.path.expandvars("${HOME}/clones/vc/vcast"))

    # What's the path to root src tree?
    src_path = os.path.dirname(repo_path)

    # Set the environment variable needed for the environments to build
    os.environ["S2N_VC_SRC_PATH"] = src_path

    # What two shas do we want to analyse?
    current_sha = "c158f0c8cb190b5121702fbe0e2b16547c5b63b4"
    new_sha = "4caa406c233b57e6f0bb7d5a62c83aca237b7e31"

    # How long for ATG?
    timeout = 2

    return repo_path, manage_path, current_sha, new_sha, timeout

def do_atg_workflow():
    # What's the path to our repo?
    repo_path = os.path.abspath(os.path.expandvars("${HOME}/clones/atg_workflow_vc/src"))

    # What's the path to our Manage root folder?
    manage_path = os.path.abspath(os.path.expandvars("${HOME}/clones/atg_workflow_vc/vcast"))

    # What's the path to our Manage root folder?
    final_tst_path = os.path.abspath(os.path.expandvars("${HOME}/clones/atg_workflow_vc/vcast_generated"))
    final_tst_path = os.path.join(manage_path, "atg_workflow_vc", "environment")

    # Set the environment variable needed for the environments to build
    os.environ["ATG_WORKFLOW_VC_SRC_PATH"] = repo_path

    # What two shas do we want to analyse?
    current_sha, new_sha = atg_misc.parse_git_for_hashes(repo_path)

    # How long for ATG?
    timeout = 2

    return repo_path, manage_path, final_tst_path, current_sha, new_sha, timeout

def main():
    repo_path, manage_path, final_tst_path, current_sha, new_sha, timeout = do_atg_workflow()

    git_analysis = atg_scm_hooks.GitImpactedObjectFinder(repo_path)
    git_analysis.calculate_preserved_files(current_sha, new_sha)


    import sys
    sys.exit(-1)

    # Use our class to find the changed files for a given repo
    dcf = atg_discover.DiscoverChangedFiles(repo_path)

    # Get the changed files between our two commits
    changed_files = dcf.get_changed_files(current_sha, new_sha)

    debugging = True

    if debugging:
        for a_file in changed_files:
            print(a_file)

    #
    # Use our class to find the relationship between files/VectorCAST
    # environments
    #
    dmd = atg_discover.DiscoverManageDependencies(manage_path, repo_path)
    dmd.calculate_deps()

    # Mapping from files to environments that use those files
    fnames_to_envs = dmd.fnames_to_envs

    # Mapping from environments to the name of the unit for that environment
    envs_to_units = dmd.envs_to_units

    # Find all of the used files across the whole of the Manage project
    dep_files = set(fnames_to_envs.keys())

    #
    # Calculate the intersection between the _used_ files and the _changed_
    # files
    #
    changed_used_files = changed_files.intersection(dep_files)
    print(changed_used_files)

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

    # Debug
    print("ATG will have {:d} seconds per routine".format(timeout))

    baseline_iterations = 1

    # Create an incremental ATG object
    ia = atg_processor.ProcessProject(
        manage_path, impacted_envs, envs_to_units, timeout, baseline_iterations,
        final_tst_path
    )

    # Process our environments
    ia.process()


if __name__ == "__main__":
    main()

# EOF
