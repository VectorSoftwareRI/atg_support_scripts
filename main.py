#!/usr/bin/env python3

import os
import sys
import importlib

import incremental_atg.build_manage as build_manage
import incremental_atg.debug_report as atg_debug_report
import incremental_atg.default_parser as default_parser
import incremental_atg.discover as atg_discover
import incremental_atg.process_project as atg_processor
import incremental_atg.misc as atg_misc

import logging
from multiprocessing_logging import install_mp_handler


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
    assert "current_id" in configuration
    assert "new_id" in configuration

    repository_path = configuration["repository_path"]
    manage_vcm_path = configuration["manage_vcm_path"]
    final_tst_path = configuration["final_tst_path"]
    scm_analysis_class = configuration["scm_analysis_class"]
    current_id = configuration["current_id"]
    new_id = configuration["new_id"]

    #  Logging
    if options.logging:

        if options.log_file:
            logging.basicConfig(filename=options.log_file, filemode="w", level=logging.DEBUG)
        else:
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
            install_mp_handler()

    if options.verbosity:
        atg_misc.be_verbose = True
    else:
        atg_misc.be_verbose = False

    # Create an scm analysis object
    scm_analyser = scm_analysis_class(repository_path, options.allow_moves)

    # Calculate preserved files
    preserved_files = scm_analyser.calculate_preserved_files(current_id, new_id)

    # Create our Manage project
    manage_builder = build_manage.ManageBuilder(
        manage_vcm_path,
        cleanup=options.cleanup,
        skip_build=options.skip_build,
        allow_broken_environments=options.allow_broken_environments,
    )
    manage_builder.process()

    # Discover the environments (not neccessarily tied to Manage!)
    manage_dependencies = atg_discover.DiscoverEnvironmentDependencies(
        repository_path, manage_builder.built_environments
    )
    manage_dependencies.process()

    # Our set of impacted environments
    impacted_envs = set()

    # For each environment with its dependencies ...
    for environment, dependencies in manage_dependencies.envs_to_fnames.items():

        # ... check it if *only* uses preserved files
        uses_only_preserved_files = dependencies.issubset(preserved_files)

        # If not ...
        if not uses_only_preserved_files:
            # ... flag it as impacted!
            impacted_envs.add(environment)

    # Dry run or reporting
    if options.dry_run or options.report:

        # Generate the report
        atg_debug_report.debug_report(
            repository_path,
            current_id,
            new_id,
            scm_analyser,
            preserved_files,
            options.limit_unchanged,
            manage_vcm_path,
            manage_builder,
            manage_dependencies,
            impacted_envs,
        )

    if options.dry_run:
        # If we're dry run, finish here
        return 0

    # Create an incremental ATG object
    ia = atg_processor.ProcessProject(
        impacted_envs,
        manage_dependencies.envs_to_units,
        options.timeout,
        options.baseline_iterations,
        final_tst_path,
    )

    print("Processing ... ", end="", flush=True)
    # Process our environments
    ia.process()
    print("Done!", flush=True)

    #
    # TODO: get the changed files and pass them in to the persistence
    # module
    #
    configuration_module.persist_changes(ia.updated_files)

    return 0


def main():
    parser = default_parser.get_default_parser()
    options = parser.parse_args()
    return incremental_atg(options)


if __name__ == "__main__":
    sys.exit(main())

# EOF
