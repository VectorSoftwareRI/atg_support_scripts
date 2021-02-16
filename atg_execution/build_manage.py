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
import tempfile

import atg_execution.misc as atg_misc


def run_manage_command(manage_obj, cmd_suffix):
    """
    Helper to run part of a Manage command
    """

    # Build-up the full command
    full_cmd = "{manage:s} -p {project:s} {cmd_suffix:s}".format(
        manage=manage_obj.manage_exe,
        project=manage_obj.project_name,
        cmd_suffix=cmd_suffix,
    )

    # Run it
    out, _, returncode = atg_misc.run_cmd(full_cmd, manage_obj.cwd)

    # Did we get a non-zero return code?
    if returncode:

        # string that suggests there's a licensing failure
        license_string = "icens"

        # What's our base message?
        base_error = "Command '{:s}' failed".format(full_cmd)

        # What's our suffix?
        if license_string in out:
            suffix = " -- missing license?"
        else:
            suffix = ""

        # Raise an error
        raise RuntimeError("{:s}{:s}".format(base_error, suffix))


def prepare_manage_structure(manage_data_obj):
    """
    Populate the Manage folder structure
    """

    # Get a temporary file with a Python suffix
    with tempfile.NamedTemporaryFile(suffix=".py") as temp_file:

        # Full path
        full_temp_file = temp_file.name

        # Basename
        basename = os.path.basename(full_temp_file)

        # Add the script
        add_script(manage_data_obj, full_temp_file, basename)

        # Populate Manage's build folder
        populate_build_folder(manage_data_obj)

        # Remove the script
        remove_script(manage_data_obj, basename)


def populate_build_folder(manage_obj):
    """
    'Populates' Manages build folder
    """

    # Build the project
    if manage_obj.compiler_node:
        build_project = "--level {:s}".format(manage_obj.compiler_node)
    else:
        build_project = ""

    build_project = "{:s} --build".format(build_project)

    run_manage_command(manage_obj, build_project)

    # Make sure we now have a build folder!
    assert os.path.isdir(manage_obj.build_folder)


def add_script(manage_obj, script_path, script_name):
    """
    Add our build script to the Manage project
    """

    # Add the script to the Python repository
    add_script = "--python-repository --add {script:s}".format(script=script_path)
    run_manage_command(manage_obj, add_script)

    # Set it as the build script
    build_script = "--build-script {script:s}".format(script=script_name)
    run_manage_command(manage_obj, build_script)


def remove_script(manage_obj, script_name):
    """
    Remove our tempoary build script
    """

    # Set the build script to be nothing (removes the option)
    build_script = "--build-script {script:s}".format(script='""')
    run_manage_command(manage_obj, build_script)

    # Remove our temporary script
    delete_script = "--python-repository --remove {script:s}".format(script=script_name)
    run_manage_command(manage_obj, delete_script)


def discover_environments(manage_obj):
    """
    Walk the Manage build folder and discover the VectorCAST environments
    """

    all_environments = set()

    # Walk the root
    for root, _, files in os.walk(manage_obj.build_folder):

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
                    all_environments.add((env_name, build_dir))

    return all_environments


def build_env(manage_obj, env_name, env_location):
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
        clicast=manage_obj.clicast_exe, env_script=env_script
    )

    # Log to the file 'rebuild'
    output_prefix = os.path.join(env_location, "rebuild")

    # Run our command
    _, _, returncode = atg_misc.run_cmd(
        cmd, env_location, log_file_prefix=output_prefix
    )

    return returncode


def check_success_build(manage_obj, returncode, built_env):

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


class ManageDataObj:
    def __init__(self, configuration):

        # Path to our Manage project
        self.manage_vcm_path = configuration.manage_vcm_path

        # Compiler node
        self.compiler_node = configuration.compiler_node

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
        self.skip_build = configuration.options.skip_build

        # Should we clean-up?
        self.clean_up = configuration.options.clean_up

        # Do we allow for broken environments?
        self.allow_broken_environments = configuration.options.allow_broken_environments

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


@atg_misc.for_all_methods(atg_misc.log_entry_exit)
class ManageBuilder(atg_misc.ParallelExecutor):
    def __init__(self, configuration):

        # Call the super constructor
        super().__init__(configuration, display_progress_bar=True)

        self.manage_data_obj = ManageDataObj(configuration)

        if self.manage_data_obj.skip_build:
            assert not self.manage_data_obj.clean_up
            assert os.path.isdir(self.manage_data_obj.build_folder)
        else:
            # We do not expect to see a build folder!
            if os.path.exists(self.manage_data_obj.build_folder) or os.path.isdir(
                self.manage_data_obj.build_folder
            ):

                # If we haven't asked to do clean-up, then we error-out
                if not self.manage_data_obj.clean_up:
                    raise RuntimeError(
                        "{:s} already exists, not proceeding".format(
                            self.manage_data_obj.build_folder
                        )
                    )

                # Otherwise, remove the build folder
                shutil.rmtree(self.manage_data_obj.build_folder)

        # The set of all environments in this Manage project
        self.all_environments = set()

        # Build environments
        self.built_environments = set()

    def __repr__(self):
        return str({"manage_vcm_path": self.manage_data_obj.manage_vcm_path})

    def discover_environments(self):
        self.all_environments = discover_environments(self.manage_data_obj)

    def build_environments(self):
        # Build the environments in parallel
        atg_misc.print_msg("Building Manage environments ...")
        self.run_routine_parallel(self.build_env, self.all_environments)

    def check_built_environments(self):
        # Build the environments in parallel
        self.run_routine_parallel(self.check_env, self.all_environments)

    def process(self):
        """
        Processes the Manage project
        """
        atg_misc.print_msg("Processing Manage project")

        if not self.manage_data_obj.skip_build:

            # Prepare the Manage folder structure
            prepare_manage_structure(self.manage_data_obj)

        # Find all of the build environments (starting from our Manage project root)
        self.discover_environments()

        if not self.manage_data_obj.skip_build:
            # Build all found environments
            self.build_environments()
        else:
            # Find those that have already built
            self.check_built_environments()

        atg_misc.print_msg("Manage project processed")

    def check_env(self, env_name, env_location, returncode=False):

        built_env = os.path.join(env_location, env_name)

        success = False

        if self.check_success_build(returncode, built_env):
            self.built_environments.add((env_name, env_location))
            success = True
        elif not self.allow_broken_environments:
            raise RuntimeError(
                "{env:s} did not build. Cowardly aborting.".format(env=built_env)
            )

        return success

    def build_env(self, env_name, env_location):
        returncode = build_env(self.manage_data_obj, env_name, env_location)

        self.check_env(env_name, env_location, returncode=returncode)

        # Update the progress bar
        self.move_progress_bar()

    def check_success_build(self, returncode, built_env):
        success = check_success_build(self.manage_data_obj, returncode, built_env)

        # Update the progress bar
        self.move_progress_bar()

        return success


# EOF
