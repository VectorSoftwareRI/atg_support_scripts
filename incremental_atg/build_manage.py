#!/usr/bin/env python3

import os
import shutil
import tempfile
import subprocess

import incremental_atg.misc as atg_misc


class ManageBuilder(atg_misc.ParallelExecutor):
    def __init__(self, manage_vcm_path, cleanup=False, skip_build=False):

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
                else:
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
        self.environments = set()

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

    @atg_misc.log_entry_exit
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

    @atg_misc.log_entry_exit
    def populate_build_folder(self):
        """
        'Populates' Manages build folder
        """

        # Build the project
        build_project = "--build"
        self.run_manage_command(build_project)

        # Make sure we now have a build folder!
        assert os.path.isdir(self.build_folder)

    @atg_misc.log_entry_exit
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

    @atg_misc.log_entry_exit
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
                        self.environments.add((env_name, build_dir))

    @atg_misc.log_entry_exit
    def build_environments(self):
        # Build the environments in parallel
        self.run_routine_parallel(self.build_env, self.environments)

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

        # Make sure it didn't fail
        assert not returncode

        # We should now have a built environment
        assert os.path.exists(built_env) and os.path.isdir(built_env)


if __name__ == "__main__":
    manage_vcm_path = "/home/avj/clones/atg_workflow_vc/vcast/atg_workflow_vc.vcm"
    ManageBuilder(manage_vcm_path, cleanup=True).process()


# EOF
