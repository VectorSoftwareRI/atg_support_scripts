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
import sqlite3
import xmltodict
import pathlib

import atg_execution.misc as atg_misc


@atg_misc.for_all_methods(atg_misc.log_entry_exit)
class DiscoverEnvironmentDependencies(atg_misc.ParallelExecutor):
    """
    Helper class to help identify:

        * The source files each environment depends on

        * The unit names for each environment

        * The routines for each unit (in each environment)
    """

    def __init__(self, configuration, manage_builder):

        # Call the super constructor
        super().__init__(configuration)

        # What's the directory that contains our source files?
        self.repository_path = pathlib.Path(configuration.repository_path)

        # What are our environments?
        self.environments = manage_builder.built_environments

        # For each _file_, which environments depend on this file?
        self.fnames_to_envs = {}

        # For each environment, which files are used in this environment?
        self.envs_to_fnames = {}

        # For each environment, what are the units, and for those units, what are the routines?
        self.envs_to_units = {}

    def __repr__(self):
        return str({"repository_path": self.repository_path})

    def find_files(self, env_path):
        """
        Given an environment folder, finds the set of files this environment
        depends on
        """

        # Open-up the dependencies XML
        xml_path = os.path.join(env_path, "include_dependencies.xml")

        # Parse it
        parsed = xmltodict.parse(open(xml_path).read(), force_list=["unit", "file"])

        # For each unit
        for val in parsed["includedeps"]["unit"]:

            # If we don't have a 'file' attribute, then we can skip it
            if "file" not in val:
                continue

            # Otherwise, walk each dependency file
            for dependency in val["file"]:

                # Get the filename?
                fname = pathlib.Path(dependency["#text"])

                # Does the file path originate from our repository?
                if self.repository_path in fname.parents:

                    #
                    # Obtain a _relative_ name -- this allows us to match to the
                    # git diff!
                    #
                    rel_fname = os.path.relpath(fname, self.repository_path)

                    # We're about to update the shared state, so grab the lock
                    with self.update_shared_state():

                        # If we haven't seen this file name before ...
                        if rel_fname not in self.fnames_to_envs:
                            # ... initialise the dictionary
                            self.fnames_to_envs[rel_fname] = set()

                        # Store that this environment depends on this file
                        self.fnames_to_envs[rel_fname].add(env_path)

                        # If we haven't seen the env before ...
                        if env_path not in self.envs_to_fnames:
                            # ... add it to our dict
                            self.envs_to_fnames[env_path] = set()

                        # Store the files used inside of this environment
                        self.envs_to_fnames[env_path].add(rel_fname)

    def find_units_functions(self, env_path):
        """
        Given an environment folder, finds the name of the main unit
        """

        # We expect this environment not to have been processed
        assert env_path not in self.envs_to_units

        # Open-up a connection to 'cover.db'
        conn = sqlite3.connect(os.path.join(env_path, "cover.db"))

        # Grab a cursor
        cursor = conn.cursor()

        query = """
SELECT source_files.path,
       functions.name
FROM   functions 
       JOIN instrumented_files 
         ON instrumented_files.id = functions.instrumented_file_id 
       JOIN source_files 
         ON source_files.id = instrumented_files.source_file_id; 
""".strip()

        # Execute our query
        rows = cursor.execute(query)

        # Store our units
        units_to_functions = {}

        for row in rows:
            # Get the source file name and the function name
            source_file_path, function_name = row

            # Initialise the function dict
            if source_file_path not in units_to_functions:
                units_to_functions[source_file_path] = []

            # Store this function
            units_to_functions[source_file_path].append(function_name)

        # We're about to update the shared state, so grab the lock
        with self.update_shared_state():

            # Store details for this env
            self.envs_to_units[env_path] = units_to_functions

    def process_env(self, env_path):
        """
        Given an environment, expects the information we need
        """

        # Calcuate the map between files and environments
        self.find_files(env_path)

        # Calulate the map between environments and TUs
        self.find_units_functions(env_path)

    def process(self):
        """
        Calculates the 'interesting information' for a given set of environments
        """

        atg_misc.print_msg("Discovering environment dependencies")

        execution_context = []

        # For each environment/build directory
        for env_name, build_dir in self.environments:

            # Calculate the full path to the environment
            env_path = os.path.join(build_dir, env_name)

            # We expect that this environment has been built!
            assert os.path.exists(env_path) and os.path.isdir(env_path)

            execution_context.append([env_path])

        self.run_routine_parallel(self.process_env, execution_context)

        atg_misc.print_msg("Environment dependencies discovered")


# EOF
