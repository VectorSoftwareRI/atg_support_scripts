#!/usr/bin/env python3

import os

import incremental_atg.discover as atg_discover
import incremental_atg.process_project as atg_processor
import incremental_atg.misc as atg_misc
import incremental_atg.scm_hooks as atg_scm_hooks
import incremental_atg.build_manage as build_manage
import incremental_atg.debug_report as atg_debug_report


def do_s2n():
    # What's the path to our repo?
    repo_path = os.path.abspath(os.path.expandvars("${HOME}/clones/s2n_vc/src/s2n"))

    # What's the path to our Manage root folder?
    vcm_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/s2n_vc/vcast/s2n_vc.vcm")
    )

    # Path to the Manage artefacts
    manage_path = os.path.splitext(vcm_path)[0]

    # What's the path to our Manage root folder?
    final_tst_path = os.path.join(manage_path, "environment")

    # What's the path to root src tree?
    src_path = os.path.dirname(repo_path)

    # Set the environment variable needed for the environments to build
    os.environ["S2N_VC_SRC_PATH"] = src_path

    # What two shas do we want to analyse?
    current_sha = "c158f0c8cb190b5121702fbe0e2b16547c5b63b4"
    new_sha = "4caa406c233b57e6f0bb7d5a62c83aca237b7e31"

    return repo_path, vcm_path, final_tst_path, current_sha, new_sha


def do_atg_workflow():
    # What's the path to our repo?
    repo_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/atg_workflow_vc/src")
    )

    # What's the path to our Manage vcm file?
    vcm_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/atg_workflow_vc/vcast/atg_workflow_vc.vcm")
    )

    # Path to the Manage artefacts
    manage_path = os.path.splitext(vcm_path)[0]

    # What's the path to our Manage root folder?
    final_tst_path = os.path.join(manage_path, "environment")

    # Set the environment variable needed for the environments to build
    os.environ["ATG_WORKFLOW_VC_SRC_PATH"] = repo_path

    # What two shas do we want to analyse?
    current_sha, new_sha = atg_misc.parse_git_for_hashes(repo_path)

    return repo_path, vcm_path, final_tst_path, current_sha, new_sha


def main():
    process_s2n = False

    if process_s2n:
        args = do_s2n()
    else:
        args = do_atg_workflow()

    (repository_path, manage_vcm_path, final_tst_path, current_sha, new_sha,) = args

    timeout = 1
    verbose = True
    baseline_iterations = 1
    cleanup = False
    skip_build = True
    limit_unchanged = 100

    git_analysis = atg_scm_hooks.GitImpactedObjectFinder(repository_path)
    preserved_files = git_analysis.calculate_preserved_files(current_sha, new_sha)

    manage_builder = build_manage.ManageBuilder(
        manage_vcm_path, cleanup=cleanup, skip_build=skip_build
    )
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

    if verbose:
        atg_debug_report.debug_report(
            repository_path,
            current_sha,
            new_sha,
            git_analysis,
            preserved_files,
            limit_unchanged,
            manage_vcm_path,
            manage_builder,
            manage_dependencies,
            impacted_envs,
            envs_to_fnames,
        )

    import sys

    sys.exit(-1)

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
