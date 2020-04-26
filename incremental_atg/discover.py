#!/usr/bin/env python3

import os
import git
import whatthepatch
import sqlite3

import incremental_atg.misc as atg_misc


class DiscoverChangedFiles(object):
    """
    Class to return the list of file changes for a given repo
    """

    def __init__(self, repo_path):

        # What's the path to the repo?
        self.repo_path = repo_path

        # Create our git class
        self.repo = git.Repo(repo_path)

    @atg_misc.log_entry_exit
    def get_changed_files(self, current_sha, new_sha):
        """
        Given two git hashes, calculates the list of changed files
        """

        # Grab the raw git diff
        diff_text = self.repo.git.diff(current_sha, new_sha)

        # parse the diff
        parsed_diff = whatthepatch.parse_patch(diff_text)

        # our list of changed files
        changed_files = set()

        # Iterate over the diff -- one 'diff' per file
        for diff in parsed_diff:

            # Temporarily detect if the file has moved
            if diff.header.old_path != diff.header.new_path:
                # TODO: need to handle this case

                # Inside of a git diff, file moves start with 'a' (for old) and 'b'" for new
                git_old_path = diff.header.old_path
                old_leading_dir = git_old_path.split(os.path.sep, 1)[0]
                assert old_leading_dir == "a"

                git_new_path = diff.header.new_path
                new_leading_dir, new_path = git_new_path.split(os.path.sep, 1)
                assert new_leading_dir == "b"

                #
                # TODO: we need to flag to the user that the Manage project
                # needs updating and things _will not work_ because the units
                # have moved
                #

                # Make it clear that this is further refined by interrogating Manage

            else:
                new_path = diff.header.new_path

            # Currently, environments depend on the new files and the old files
            changed_files.add(new_path)

        # Return our set of changed files
        return changed_files


class DiscoverManageDependencies(object):
    """
    Helper class to help identify:

        * The source files each environment depends on

        * The unit names for each environment

            + Currently only one unit per env

        * The routines for each environment
    """

    def __init__(self, project_root, repo_root):

        # Where's the starting point of our Manage project?
        self.project_root = project_root

        # What's the top-level of our source repo
        self.repo_root = repo_root

        # The set of discovered environments
        self.environments = set()

        # For each _file_, which environments depend on this file?
        self.fnames_to_envs = {}

        # For each environment, what are the units, and for those units, what are the routines?
        self.envs_to_units = {}

    def find_files(self, env_path):
        """
        Given an environment folder, finds the set of files this environment
        depends on
        """

        # Create a connection to 'master.db'
        conn = sqlite3.connect(os.path.join(env_path, "master.db"))

        # Grab a cursor
        cursor = conn.cursor()

        # Our query
        for row in cursor.execute("select path from sourcefiles"):

            # We expect one element per row (as per the select)
            assert len(row) == 1

            # What's the file name?
            fname = row[0]

            # Does the file path originate from our repository?
            if fname.startswith(self.repo_root):

                #
                # Obtain a _relative_ name -- this allows us to match to the
                # git diff!
                #
                rel_fname = os.path.relpath(fname, self.repo_root)

                # If we haven't seen this file name before ...
                if rel_fname not in self.fnames_to_envs:
                    # ... initialise the dictionary
                    self.fnames_to_envs[rel_fname] = set()

                # Store that this environment depends on this file
                self.fnames_to_envs[rel_fname].add(env_path)

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

    @atg_misc.log_entry_exit
    def calculate_deps(self):
        """
        Calculates the 'interesting information' for a given Manage project
        """

        # Find all of the environments
        self.find_envs()

        # For each environment/build directory
        for env_name, build_dir in self.environments:

            # Calculate the full path to the environment
            env_path = os.path.join(build_dir, env_name)

            # We expect that this environment has been built!
            assert os.path.exists(env_path) and os.path.isdir(env_path)

            # Process that environment
            self.process_env(env_path)


def wrap_class_method(args):
    """
    You cannot pass a class method into pool.map -- so we use a helper function
    to call our really class method
    """
    func, args = args
    func(*args)


# EOF
