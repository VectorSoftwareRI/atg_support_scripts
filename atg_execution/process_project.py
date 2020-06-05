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
import shutil

import atg_execution.baseline_for_atg as baseline_for_atg
import atg_execution.misc as atg_misc
import atg_execution.tst_editor as tst_editor


@atg_misc.for_all_methods(atg_misc.log_entry_exit)
class ProcessProject(atg_misc.ParallelExecutor):
    """
    Given a Manage project and a set of environments, re-runs the "impacted"
    environments/routines
    """

    def __init__(
        self, configuration, impacted_environments, environment_dependencies,
    ):
        # Call the super constructor
        super().__init__(configuration, display_progress_bar=True)

        # Do we have a work directory?
        self.atg_work_dir = configuration.options.atg_work_dir

        # If it is non-None
        if self.atg_work_dir is not None:

            #  Clean-up
            if os.path.exists(self.atg_work_dir):
                shutil.rmtree(self.atg_work_dir)

            # Make it
            os.mkdir(self.atg_work_dir)

        # The set of environments to run
        self.impacted_environments = impacted_environments

        # Mapping from environments to units and their functions
        self.envs_to_units = environment_dependencies.envs_to_units

        # Mapping from environments to generated .tst files
        self.env_tsts = {}

        # Mapping from environments to names of the merged tsts
        self.merged_tsts = {}

        # Number of seconds to perform ATG
        self.timeout = configuration.options.timeout

        # Number of baseling iterations to perform?
        self.baseline_iterations = configuration.options.baseline_iterations

        # Where are the tsts going to go?
        self.final_tst_path = configuration.final_tst_path

        # Are we strictly checking return codes?
        self.strict_rc = configuration.options.strict_rc

        # Make our output path
        if not os.path.exists(self.final_tst_path):
            os.mkdir(self.final_tst_path)
        elif not os.path.isdir(self.final_tst_path):
            raise RuntimeError("your final path is a file")

        # Initialise the environment object
        for env in self.impacted_environments:
            self.env_tsts[env] = {}
            self.merged_tsts[env] = {}

            # Make working directories for each env
            if self.atg_work_dir is not None:
                env_name = os.path.basename(env)
                env_hash = os.path.basename(os.path.dirname(env))
                os.mkdir(os.path.join(self.atg_work_dir, env_hash))

        self.updated_files = set()

    def __repr__(self):
        return str({"merged_tsts": self.merged_tsts})

    def get_edg_flags(self, env_path):
        """
        Given an environment build folder, obtains the EDG flags
        """

        # Initial return value
        edg_flags = None

        # Open up the CCAST_.CFG
        lines = open(os.path.join(env_path, "..", "CCAST_.CFG")).readlines()

        # Iterate over the lines
        for line in lines:
            # If we see the EDG flags line ...
            if line.startswith("C_EDG_FLAGS:"):
                # ... grab the flags
                edg_flags = line.split(":", 1)[1].strip()

                # Stop iterating
                break

        # We expect to have found our flags
        assert edg_flags is not None

        # Return them
        return edg_flags

    def unit_to_tu_path(self, env_path, unit_name):
        """
        Converts a unit name (full path to original source) into a TU name
        inside of the environment
        """

        # Get the base name of our unit
        unit_base = os.path.basename(unit_name)

        # Strip off the suffix
        base, suffix = os.path.splitext(unit_base)

        # Create the TU name
        tu_path = os.path.join(env_path, "{:s}.tu{:s}".format(base, suffix))

        # Return it
        return tu_path

    def run_atg_one_routine(self, env_path, src_file, routine_name):
        """
        Runs a single routine in an environment via ATG
        """

        # What's the name of this environment?
        env = os.path.basename(env_path)

        # What's the unit name for the current subprogram?
        unit = os.path.splitext(os.path.basename(src_file))[0]

        # Where do we want the ATG artefacts to go?
        if self.atg_work_dir is not None:
            build_hash = os.path.basename(os.path.dirname(env_path))
            atg_output_location = os.path.join(self.atg_work_dir, build_hash)
        else:
            atg_output_location = env_path

        # What's the prefix of our all outputs?
        output_prefix = os.path.join(
            atg_output_location,
            "{env:s}_{unit:s}_{routine:s}".format(
                env=env, unit=unit, routine=routine_name
            ),
        )

        # Where is ATG going to write its log to?
        log_file = "{:s}.log".format(output_prefix)

        # Where is ATG going to write its tst to?
        tst_file = "{:s}.tst".format(output_prefix)

        # Where to log the PyEDG output to?
        pyedg_log_prefix = "{:s}_pyedg".format(output_prefix)

        # Build-up our environment object
        environ = os.environ.copy()

        # What's the ATG log?
        environ["VCAST_ATG_LOG_FILE_NAME"] = log_file

        # What's the routine to process?
        environ["VCAST_ATG_RESTRICT_SUBPROGRAM"] = routine_name

        # Where are we going to write our output?
        environ["VCAST_PYEDG_ATG_OUTPUT_FILE"] = tst_file

        # Tell ATG to generate display attributes
        environ["VCAST_ATG_BASELINING"] = "1"

        # What PyEDG script are we going to run?
        environ["VCAST_PYEDG_PATH"] = os.path.expandvars(
            "$VECTORCAST_DIR/python/vector/apps/atg_utils/run_atg.py"
        )

        # Find the EDG flags
        edg_flags = self.get_edg_flags(env_path)

        # Find the TU path
        tu_path = self.unit_to_tu_path(env_path, src_file)

        # We expect the TU to exist and be a file
        assert os.path.exists(tu_path) and os.path.isfile(tu_path)

        # Build-up our PyEDG command
        cmd = os.path.expandvars(
            "$VECTORCAST_DIR/pyedg {edg_flags:s} {tu:s}".format(
                edg_flags=edg_flags, tu=tu_path
            )
        )

        # Run PyEDG and get the return code
        _, _, returncode = atg_misc.run_cmd(
            cmd,
            cwd=env_path,
            environ=environ,
            timeout=self.timeout,
            log_file_prefix=pyedg_log_prefix,
        )

        # If we're using 'strict return codes' and we have a return code, then
        # that's a return code failure
        rc_failure = self.strict_rc and returncode

        # If we didn't have a 0 return code or we have no .tst, then we have no tst
        if rc_failure or not os.path.exists(tst_file) or not os.path.isfile(tst_file):
            tst_file = None

        # We're about to update the shared state, so grab the lock
        with self.update_shared_state():

            # Update the shared state
            self.env_tsts[env_path][(unit, routine_name)] = tst_file

        # Update the progress bar
        self.move_progress_bar()

    def run_atg(self):
        """
        Runs ATG in parallel, with parallelism at the routine level
        """

        # Product of environments with routines in that environment
        routine_contexts = []

        # For each impacted environment ...
        for env in self.impacted_environments:

            # For each source file ...
            for src_file in self.envs_to_units[env]:

                # For each routine ...
                for routine_name in self.envs_to_units[env][src_file]:

                    # Store this combination
                    routine_contexts.append((env, src_file, routine_name))

        # What Python routine do we want to call?
        routine = self.run_atg_one_routine

        atg_misc.print_msg("Generating baseline test-cases ...")

        # Run this routine in parallel given the provided contexts
        self.run_routine_parallel(routine, routine_contexts)

    def merge_one_environment(self, env_path):
        """
        Given an environment path, merges all of the routine tsts into a master
        'merged' tst
        """

        # Get all of the tsts for this environment
        genenerated_tsts = self.env_tsts[env_path]

        # What's the name of this environment?
        env_name = os.path.basename(env_path)

        # What folder was it built in?
        build_path = os.path.dirname(env_path)

        # What's our output name?
        merged_tst = os.path.join(build_path, "{:s}_atg.tst".format(env_name))

        # Open-up the merged .tst
        with open(merged_tst, "w") as merged_fd:

            # For each routine we generated (or tried) to generate tests for
            for generated_tst in sorted(genenerated_tsts.keys()):

                # Find the name of the tst for this routine
                routine_tst = genenerated_tsts[generated_tst]

                # Unpack our elements
                source_name, routine_name = generated_tst

                # Did we succeed or not?
                succeeded = "succeeded" if routine_tst is not None else "failed"

                # Write-out a message
                msg = "-- ATG {:s} for {:s} (in unit {:s}) --".format(
                    succeeded, routine_name, source_name
                )
                header = "-" * len(msg)
                output = [header, msg, header]
                for elem in output:
                    merged_fd.write("{:s}\n".format(elem))

                # If we succeed, copy the contents of the tst into our new file
                if routine_tst is not None:
                    merged_fd.write(open(routine_tst).read())

        # We're about to update the shared state, so grab the lock
        with self.update_shared_state():

            # Update the shared state
            self.merged_tsts[env_path] = merged_tst

        # Update the progress bar
        self.move_progress_bar()

    def baseline_one_environment(self, env_path):
        """
        Given an environment path, baselines the environment
        """
        merged_tst_name = self.merged_tsts[env_path]

        env_name = os.path.basename(env_path)
        build_dir = os.path.dirname(env_path)
        env_file = os.path.join(build_dir, "{:s}.env").format(env_name)

        baseliner = baseline_for_atg.Baseline(env_file=env_file, verbose=0)
        baseliner.run(
            run_atg=False,
            atg_file=merged_tst_name,
            max_iter=self.baseline_iterations,
            copy_out_manage=False,
            parallel_object=self,
        )

        tests_generated = open(merged_tst_name).read().count("TEST.NAME:")

    def prune_and_merge_one_environment(self, env_path):
        """
        Given an environment path, baselines the environment
        """
        env_name = os.path.basename(env_path)

        build_dir = os.path.dirname(env_path)

        merged_atg_file = os.path.join(build_dir, baseline_for_atg.FILE_FINAL)
        assert os.path.exists(merged_atg_file)

        manage_build_dir = os.path.dirname(build_dir)
        assert os.path.basename(manage_build_dir) == "build"

        manage_project_dir = os.path.dirname(manage_build_dir)
        manage_environment_dir = os.path.join(manage_project_dir, "environment")
        assert os.path.exists(manage_environment_dir) and os.path.isdir(
            manage_environment_dir
        )

        enviroment_artefacts = os.path.join(manage_environment_dir, env_name)
        assert os.path.exists(enviroment_artefacts) and os.path.isdir(
            enviroment_artefacts
        )

        existing_tst = os.path.join(enviroment_artefacts, "{env:s}.tst").format(
            env=env_name
        )
        assert os.path.exists(existing_tst) and os.path.isfile(existing_tst)

        no_atg_tst = os.path.join(build_dir, "no_atg.tst")
        tst_edit_instance = tst_editor.TstFile(
            input_file=existing_tst, output_file=no_atg_tst
        )
        match_all_subprograms = ".*"
        match_atg_tests = "^TEST.NAME:.*ATG"
        tst_edit_instance.remove(
            subprogram_regex=match_all_subprograms, re_pattern=match_atg_tests
        )

        #
        # TODO: this tst has two header blocks in it?
        #
        combined_atg_existing = os.path.join(build_dir, "combined_atg_existing.tst")
        with open(combined_atg_existing, "w") as combined_atg_existing_fd:
            combined_atg_existing_fd.write(open(no_atg_tst).read())
            combined_atg_existing_fd.write(open(merged_atg_file).read())

        final_folder = os.path.join(self.final_tst_path, env_name)
        if not os.path.exists(final_folder) or not os.path.isdir(final_folder):
            os.mkdir(final_folder)

        final_tst = os.path.join(final_folder, "{:s}.tst".format(env_name))
        shutil.copyfile(combined_atg_existing, final_tst)

        # Store the final tst
        self.updated_files.add(final_tst)

        # Update the progress bar
        self.move_progress_bar()

    def merge_atg_routine_tst(self):
        """
        Merges the routine-level tst files into one big file, with parallelism
        at the environment level
        """

        #
        # We want to process each environment (needs to be in a list, to avoid
        # unpacking the environment path into a list of strings)
        #
        routine_context = [[env] for env in self.env_tsts]

        # What Python routine do we want to call?
        routine = self.merge_one_environment

        atg_misc.print_msg("Merging all ATG test-cases ...")

        # Run this routine in parallel given the provided context
        self.run_routine_parallel(routine, routine_context)

    def baseline(self):
        """
        Performs baselining for each environment
        """

        #
        # We want to process each environment (needs to be in a list, to avoid
        # unpacking the environment path into a list of strings)
        #
        routine_context = [[env] for env in self.env_tsts]

        # What Python routine do we want to call?
        routine = self.baseline_one_environment

        steps_per_stage = 0
        # build environment + run build-in test-case generation
        steps_per_stage += 1
        # execute once and create expecteds
        steps_per_stage += 1
        # for each time we prune the expected results
        steps_per_stage += self.baseline_iterations
        # copy .tst to Manage folder
        steps_per_stage += 1

        atg_misc.print_msg(
            "Baselining all environments ({:d} steps per environment) ...".format(
                steps_per_stage
            )
        )

        # Run this routine in parallel given the provided context
        self.run_routine_parallel(
            routine, routine_context, steps_per_stage=steps_per_stage
        )

    def prune_and_merge(self):
        """
        Performs baselining for each environment
        """

        #
        # We want to process each environment (needs to be in a list, to avoid
        # unpacking the environment path into a list of strings)
        #
        routine_context = [[env] for env in self.env_tsts]

        # What Python routine do we want to call?
        routine = self.prune_and_merge_one_environment

        atg_misc.print_msg("Pruning test-cases ...")

        # Run this routine in parallel given the provided context
        self.run_routine_parallel(routine, routine_context)

    def process(self):
        """
        Performs a number of steps given a Manage project:

            * Run ATG in parallel over the units subprograms

            * Merge all the .tst files

            * Run the baselining stuff
        """

        # Run ATG
        self.run_atg()

        # Merge the seperate .tsts
        self.merge_atg_routine_tst()

        # Run baselining + stripping
        self.baseline()

        # Remove old ATG and merge with existing tests
        self.prune_and_merge()


# EOF
