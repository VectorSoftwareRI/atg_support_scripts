#!/usr/bin/env python3

import os
import shutil
import tempfile

import incremental_atg.misc as atg_misc


@atg_misc.for_all_methods(atg_misc.log_entry_exit)
class ManageBuilder(atg_misc.ParallelExecutor):
    def __init__(
        self,
        manage_vcm_path,
        cleanup=False,
        skip_build=False,
        allow_broken_environments=False,
    ):

        # Call the super constructor
        super().__init__()

        self.manage_vcm_path = manage_vcm_path

        # Manage file must exist
        assert os.path.exists(self.manage_vcm_path) and os.path.isfile(
            self.manage_vcm_path
        )

        self.manage_root_dir, suffix = os.path.splitext(self.manage_vcm_path)

        # It should really have a VCM suffix
        assert suffix == ".vcm"

        # Make sure we have a Manage folder
        assert os.path.isdir(self.manage_root_dir)

        # We really should have this!
        enviromments_folder = os.path.join(self.manage_root_dir, "environment")
        assert os.path.isdir(enviromments_folder)

        # What's the name of the build folder?
        self.build_folder = os.path.join(self.manage_root_dir, "build")

        # Should we skip doing the build?
        self.skip_build = skip_build

        # Do we allow for broken environments?
        self.allow_broken_environments = allow_broken_environments

        if self.skip_build:
            assert not cleanup
            assert os.path.isdir(self.build_folder)
        else:
            # We do not expect to see a build folder!
            if os.path.exists(self.build_folder) or os.path.isdir(self.build_folder):

                # If we haven't asked to do clean-up, then we error-out
                if not cleanup:
                    raise RuntimeError(
                        "{:s} already exists, not proceeding".format(self.build_folder)
                    )

                # Otherwise, remove the build folder
                shutil.rmtree(self.build_folder)

        # What's our project name?
        self.project_name = os.path.splitext(os.path.basename(self.manage_vcm_path))[0]

        # Where are we going to run commands?
        self.cwd = os.path.dirname(self.manage_root_dir)

        # What's the name of the Manage executable?
        self.manage_exe = os.path.expandvars(os.path.join("$VECTORCAST_DIR", "manage"))

        # What's the name of the clicast executable?
        self.clicast_exe = os.path.expandvars(
            os.path.join("$VECTORCAST_DIR", "clicast")
        )

        # The set of all environments in this Manage project
        self.all_environments = set()

        # Build environments
        self.built_environments = set()

    def __repr__(self):
        return str({"manage_vcm_path", self.manage_vcm_path})

    def run_manage_command(self, cmd_suffix):
        """
        Helper to run part of a Manage command
        """

        # Build-up the full command
        full_cmd = "{manage:s} -p {project:s} {cmd_suffix:s}".format(
            manage=self.manage_exe, project=self.project_name, cmd_suffix=cmd_suffix
        )

        # Run it
        _, _, returncode = atg_misc.run_cmd(full_cmd, self.cwd)

        # Manage sure it didn't fail
        assert not returncode

    def add_script(self, script_path, script_name):
        """
        Add our build script to the Manage project
        """

        # Add the script to the Python repository
        add_script = "--python-repository --add {script:s}".format(script=script_path)
        self.run_manage_command(add_script)

        # Set it as the build script
        build_script = "--build-script {script:s}".format(script=script_name)
        self.run_manage_command(build_script)

    def populate_build_folder(self):
        """
        'Populates' Manages build folder
        """

        # Build the project
        build_project = "--build"
        self.run_manage_command(build_project)

        # Make sure we now have a build folder!
        assert os.path.isdir(self.build_folder)

    def remove_script(self, script_name):
        """
        Remove our tempoary build script
        """

        # Set the build script to be nothing (removes the option)
        build_script = "--build-script {script:s}".format(script='""')
        self.run_manage_command(build_script)

        # Remove our temporary script
        delete_script = "--python-repository --remove {script:s}".format(
            script=script_name
        )
        self.run_manage_command(delete_script)

    def discover_environments(self):
        """
        Walk the Manage build folder and discover the VectorCAST environments
        """

        # Walk the root
        for root, _, files in os.walk(self.build_folder):

            # For each file
            for fname in files:

                # If the file ends with '.env'
                if fname.lower().endswith(".env"):

                    # What's the environment name?
                    env_name = os.path.splitext(fname)[0]

                    # What's the build folder?
                    build_dir = os.path.abspath(root)

                    #
                    # We only want to process environments that have a
                    # CCAST_.CFG next to them.
                    #
                    # For example, the 'environment' folder in Manage _does
                    # not_ have this.
                    #
                    if os.path.exists(os.path.join(build_dir, "CCAST_.CFG")):

                        # If we have 'CCAST_.CFG', store this folder
                        self.all_environments.add((env_name, build_dir))

    def build_environments(self):
        # Build the environments in parallel
        self.run_routine_parallel(self.build_env, self.all_environments)

    def check_built_environments(self):
        # Build the environments in parallel
        self.run_routine_parallel(self.check_env, self.all_environments)

    def process(self):
        """
        Processes the Manage project
        """

        if not self.skip_build:
            # Get a temporary file with a Python suffix
            with tempfile.NamedTemporaryFile(suffix=".py") as temp_file:

                # Full path
                full_temp_file = temp_file.name

                # Basename
                basename = os.path.basename(full_temp_file)

                # Add the script
                self.add_script(full_temp_file, basename)

                # Populate Manage's build folder
                self.populate_build_folder()

                # Remove the script
                self.remove_script(basename)

        # Find all of the build environments (starting from our Manage project root)
        self.discover_environments()

        if not self.skip_build:
            # Build all found environments
            self.build_environments()
        else:
            # Find those that have already built
            self.check_built_environments()

    def check_env(self, env_name, env_location, returncode=False):

        built_env = os.path.join(env_location, env_name)

        if self.check_success_build(returncode, built_env):
            self.built_environments.add((env_name, env_location))
        elif not self.allow_broken_environments:
            raise RuntimeError(
                "{env:s} did not build. Cowardly aborting.".format(env=built_env)
            )

    def build_env(self, env_name, env_location):
        """
        Builds a given environment name in the given location
        """

        # What's our env going to be called?
        env_script = "{env:s}.env".format(env=env_name)

        # Calculate the full path
        full_script = os.path.join(env_location, env_script)

        # Check it exists
        assert os.path.exists(full_script) and os.path.isfile(full_script)

        # Where is the environment going to be when it is built?
        built_env = os.path.join(env_location, env_name)

        # Check it doesn't exist
        assert not os.path.exists(built_env)

        # Clicast command to build on environment
        cmd = "{clicast:s} -lc environment script run {env_script:s}".format(
            clicast=self.clicast_exe, env_script=env_script
        )

        # Log to the file 'rebuild'
        output_prefix = os.path.join(env_location, "rebuild")

        # Run our command
        _, _, returncode = atg_misc.run_cmd(
            cmd, env_location, log_file_prefix=output_prefix
        )

        self.check_env(env_name, env_location, returncode=returncode)

    def check_success_build(self, returncode, built_env):

        # Make sure it didn't fail
        zero_return_code = not returncode

        # We should now have a built environment
        folder_exists = os.path.exists(built_env) and os.path.isdir(built_env)

        # Check the files we expect to exist
        needed_files = ["cover.db", "include_dependencies.xml"]

        # Did we find all of our files?
        found_all = all(
            [
                os.path.exists(os.path.join(built_env, fname))
                and os.path.isfile(os.path.join(built_env, fname))
                for fname in needed_files
            ]
        )

        build_log = os.path.join(built_env, "environment_builder.log")
        if os.path.exists(build_log):
            build_log_content = open(build_log).read()
            build_success = "Environment built Successfully" in build_log_content
        else:
            build_success = False

        # Environment is good if we have all of these
        return all([zero_return_code, folder_exists, found_all, build_success])


if __name__ == "__main__":
    manage_vcm_path = "/home/avj/clones/atg_workflow_vc/vcast/atg_workflow_vc.vcm"
    ManageBuilder(manage_vcm_path, cleanup=True).process()


# EOF
