#!/usr/bin/env python3

import os
import sys
import logging

import atg_execution.build_manage as build_manage
import atg_execution.debug_report as atg_debug_report
import atg_execution.default_parser as default_parser
import atg_execution.discover as atg_discover
import atg_execution.process_project as atg_processor
import atg_execution.misc as atg_misc
import atg_execution.configuration as atg_config

from multiprocessing_logging import install_mp_handler
from runpy import run_path


def process_options(options):
    #  Logging
    if options.logging:

        if options.log_file:
            logging.basicConfig(
                filename=options.log_file, filemode="w", level=logging.DEBUG
            )
        else:
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
            install_mp_handler()

    # verbosity
    atg_misc.be_verbose = options.verbose


def load_configuration(options):
    configuration_module = run_path(options.config_py)
    assert "get_configuration" in configuration_module
    configuration = configuration_module["get_configuration"](options)
    if not isinstance(configuration, atg_config.configuration):
        configuration = atg_config.parse_configuration(configuration, options)

    return configuration


def atg_execution(options):
    """
    Performs ATG
    """

    process_options(options)
    configuration = load_configuration(options)

    if configuration.find_unchanged_files is not None:
        if options.verbose:
            atg_misc.print_msg(
                "'unchanged_files' was configured; finding unchanged files"
            )
        unchanged_files = configuration.find_unchanged_files()
    else:
        if options.verbose:
            atg_misc.print_msg(
                "'unchanged_files' was not configured; all files will be processed"
            )
        unchanged_files = set()

    # Create our Manage project
    manage_builder = build_manage.ManageBuilder(configuration)
    manage_builder.process()

    # Discover the environments (not neccessarily tied to Manage!)
    environment_dependencies = atg_discover.DiscoverEnvironmentDependencies(
        configuration, manage_builder
    )
    environment_dependencies.process()

    # Our set of impacted environments
    impacted_envs = set()

    # For each environment with its dependencies ...
    for environment, dependencies in environment_dependencies.envs_to_fnames.items():

        # ... check it if *only* uses preserved files
        uses_only_unchanged_files = dependencies.issubset(unchanged_files)

        # If not ...
        if not uses_only_unchanged_files:
            # ... flag it as impacted!
            impacted_envs.add(environment)

    # Dry run or reporting
    if options.dry_run or options.report:

        # Generate the report
        atg_debug_report.debug_report(
            configuration,
            unchanged_files,
            manage_builder,
            environment_dependencies,
            impacted_envs,
        )

    if options.dry_run:
        # If we're dry run, finish here
        return 0

    # Create an incremental ATG object
    ia = atg_processor.ProcessProject(
        configuration, impacted_envs, environment_dependencies,
    )

    # Process our environments
    ia.process()

    # Store files
    configuration.store_updated_tests(ia.updated_files)

    return 0


def main():
    parser = default_parser.get_default_parser()
    options = parser.parse_args()
    if default_parser.validate_options(options):
        return atg_execution(options)
    else:
        return -1


if __name__ == "__main__":
    sys.exit(main())

# EOF
