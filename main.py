#!/usr/bin/env python3

import os

import incremental_atg.discover as atg_discover
import incremental_atg.process_project as atg_processor
import incremental_atg.build_manage as build_manage

def main():
    process_s2n = False

    if process_s2n:
        from examples import s2n_atg_example
        example = s2n_atg_example
    else:
        from examples import small_atg_example
        example = small_atg_example

    (repository_path, manage_vcm_path, final_tst_path, scm_analysis_class, current_sha, new_sha,) = example.get_configuration_object()

    timeout = 1
    verbose = True
    baseline_iterations = 1
    cleanup = False
    skip_build = True
    limit_unchanged = 100

    # Create an scm analysis object
    scm_analyser = scm_analysis_class(repository_path)

    # Calculate preserved files
    preserved_files = scm_analyser.calculate_preserved_files(current_sha, new_sha)

    # Create 
    manage_builder = build_manage.ManageBuilder(
        manage_vcm_path, cleanup=cleanup, skip_build=skip_build
    )
    manage_builder.process()

    manage_dependencies = atg_discover.DiscoverManageDependencies(
        repository_path, manage_builder.environments
    )
    manage_dependencies.process()

    # Our set of impacted environments
    impacted_envs = set()

    for environment, dependencies in manage_dependencies.envs_to_fnames.items():
        uses_only_preserved_files = dependencies.issubset(preserved_files)
        if not uses_only_preserved_files:
            impacted_envs.add(environment)

    if verbose:
        import incremental_atg.debug_report as atg_debug_report
        atg_debug_report.debug_report(
            repository_path,
            current_sha,
            new_sha,
            scm_analyser,
            preserved_files,
            limit_unchanged,
            manage_vcm_path,
            manage_builder,
            manage_dependencies,
            impacted_envs,
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
