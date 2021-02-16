#!/usr/bin/env python3

# The MIT License
#
# Copyright (c) 2020 Vector Informatik, GmbH. http://vector.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import sys
import logging
import multiprocessing

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

    # verbosity
    atg_misc.be_quiet = options.quiet

    # If None or 0
    if not options.workers:
        options.workers = multiprocessing.cpu_count()


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

    # Do a dance to ensure that we update the environment variables correctly
    if configuration.env_vars:
        env_copy = os.environ.copy()
        env_copy.update(configuration.env_vars)
        os.environ = env_copy

    if configuration.find_unchanged_files is not None:
        atg_misc.print_warn(
            "Finding unchanged files was configured, discovering changed files"
        )
        unchanged_files = configuration.find_unchanged_files()
    else:
        atg_misc.print_warn(
            "Finding unchanged files was not configured, all files will be processed"
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

    atg_misc.print_warn(
        "{impacted:d} environments need processing (total: {total:d} environments)".format(
            impacted=len(impacted_envs), total=len(manage_builder.all_environments)
        )
    )

    # Dry run or reporting
    if options.report:

        # Generate the report
        atg_debug_report.debug_report(
            configuration,
            unchanged_files,
            manage_builder,
            environment_dependencies,
            impacted_envs,
        )

    if options.dry_run:

        # Let the user know something has happened
        atg_misc.print_warn("Dry-run mode: analysis only, no tests generated")

        # If we're dry run, finish here
        return 0

    # Create an incremental ATG object
    ia = atg_processor.ProcessProject(
        configuration,
        impacted_envs,
        environment_dependencies,
    )

    # Process our environments
    ia.process()

    # Store files
    configuration.store_updated_tests(ia.project_data_obj.updated_files)

    atg_misc.print_msg("Processing completed!")

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
