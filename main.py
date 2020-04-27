#!/usr/bin/env python3

import os
import sys
import importlib

import incremental_atg.discover as atg_discover
import incremental_atg.process_project as atg_processor
import incremental_atg.build_manage as build_manage
import incremental_atg.default_parser as default_parser


def incremental_atg(options):
    """
    Performs ATG
    """

    config_py = options.config_py.replace(os.sep, ".").replace(".py", "")
    configuration_module = importlib.import_module(config_py)

    assert hasattr(configuration_module, "get_configuration")
    assert hasattr(configuration_module, "persist_changes")

    configuration = configuration_module.get_configuration()
    assert "repository_path" in configuration
    assert "manage_vcm_path" in configuration
    assert "final_tst_path" in configuration
    assert "scm_analysis_class" in configuration
    assert "current_sha" in configuration
    assert "new_sha" in configuration

    repository_path = configuration["repository_path"]
    manage_vcm_path = configuration["manage_vcm_path"]
    final_tst_path = configuration["final_tst_path"]
    scm_analysis_class = configuration["scm_analysis_class"]
    current_sha = configuration["current_sha"]
    new_sha = configuration["new_sha"]

    # Create an scm analysis object
    scm_analyser = scm_analysis_class(repository_path, options.allow_moves)

    # Calculate preserved files
    preserved_files = scm_analyser.calculate_preserved_files(current_sha, new_sha)

    # Create
    manage_builder = build_manage.ManageBuilder(
        manage_vcm_path, cleanup=options.cleanup, skip_build=options.skip_build
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

    if options.dry_run:
        import incremental_atg.debug_report as atg_debug_report

        atg_debug_report.debug_report(
            repository_path,
            current_sha,
            new_sha,
            scm_analyser,
            preserved_files,
            options.limit_unchanged,
            manage_vcm_path,
            manage_builder,
            manage_dependencies,
            impacted_envs,
        )

    else:
        # Create an incremental ATG object
        ia = atg_processor.ProcessProject(
            impacted_envs,
            manage_dependencies.envs_to_units,
            options.timeout,
            options.baseline_iterations,
            final_tst_path,
        )

        # Process our environments
        ia.process()

        #
        # TODO: get the changed files and pass them in to the persistence
        # module
        #
        updated_files = []
        configuration_module.persist_changes(updated_files)

    return 0


def main():
    parser = default_parser.get_default_parser()
    options = parser.parse_args()
    return incremental_atg(options)


if __name__ == "__main__":
    sys.exit(main())

# EOF
