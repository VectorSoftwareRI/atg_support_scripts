#!/usr/bin/env python3

import os
import sys

import incremental_atg.discover as atg_discover
import incremental_atg.process_project as atg_processor
import incremental_atg.misc as atg_misc
import incremental_atg.scm_hooks as atg_scm_hooks
import incremental_atg.build_manage as build_manage


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
    repo_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/atg_workflow_vc/src")
    )

    # What's the path to our Manage vcm file?
    vcm_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/atg_workflow_vc/vcast/atg_workflow_vc.vcm")
    )

    manage_path = os.path.dirname(vcm_path)

    # What's the path to our Manage root folder?
    final_tst_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/atg_workflow_vc/vcast_generated")
    )
    final_tst_path = os.path.join(manage_path, "atg_workflow_vc", "environment")

    # Set the environment variable needed for the environments to build
    os.environ["ATG_WORKFLOW_VC_SRC_PATH"] = repo_path

    # What two shas do we want to analyse?
    current_sha, new_sha = atg_misc.parse_git_for_hashes(repo_path)

    # How long for ATG?
    timeout = 2

    return repo_path, vcm_path, final_tst_path, current_sha, new_sha, timeout


def main():
    (
        repository_path,
        manage_vcm_path,
        final_tst_path,
        current_sha,
        new_sha,
        timeout,
    ) = do_atg_workflow()

    git_analysis = atg_scm_hooks.GitImpactedObjectFinder(repository_path)
    preserved_files = git_analysis.calculate_preserved_files(current_sha, new_sha)

    manage_builder = build_manage.ManageBuilder(manage_vcm_path, skip_build=True)
    manage_builder.process()

    manage_dependencies = atg_discover.DiscoverManageDependencies(
        repository_path, manage_builder.environments
    )
    manage_dependencies.process()

    # Mapping from files to environments that use those files
    envs_to_fnames = manage_dependencies.envs_to_fnames

    # Our set of impacted environments
    impacted_envs = set()

    for environment, dependencies in envs_to_fnames.items():
        uses_only_preserved_files = dependencies.issubset(preserved_files)
        if not uses_only_preserved_files:
            impacted_envs.add(environment)

    # Debug: show the environments we're going to process
    print("Envs to process:")
    for env in impacted_envs:
        print(env)

    # Debug
    print("ATG will have {:d} seconds per routine".format(timeout))

    baseline_iterations = 1

    # Create an incremental ATG object
    ia = atg_processor.ProcessProject(
        impacted_envs,
        manage_dependencies.envs_to_units,
        timeout,
        baseline_iterations,
        final_tst_path,
    )

    # Process our environments
    ia.process()


if __name__ == "__main__":
    main()

# EOF
