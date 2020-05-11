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
import filecmp
import atg_execution.merge_display_attributes as atg_merge_attrs
import atg_execution.strip_unchanged_attributes as atg_proc_unchanged
import atg_execution.misc as atg_misc


FILE_BL = "bl.tst"
FILE_ATG = "atg.tst"
FILE_MERGED = "merged.tst"
FILE_UNCHANGED_REMOVED = "stripped_unch.tst"
FILE_EXPECTEDS = "expecteds.tst"
FILE_INTERMEDIATE = "intermediate.tst"
FILE_STRIPPED = "stripped.tst"
FILE_FINAL = "final.tst"

SCRIPTS_HOME_DIR = os.path.dirname(__file__)
ENV_EXT = ".env"
VC_PATH = os.getenv("VECTORCAST_DIR")


@atg_misc.for_all_methods(
    atg_misc.log_entry_exit, exclude_methods=["get_incr_call_count"]
)
class Baseline:
    def __init__(self, env_file, verbose=1):
        self.env_file = os.path.basename(env_file)
        self.env_dir = os.path.splitext(self.env_file)[0]
        self.workdir = os.path.dirname(os.path.abspath(env_file))
        self.call_count = dict()
        self.verbose = verbose

    def __repr__(self):
        return str({"env_file": self.env_file})

    def get_incr_call_count(self, label):
        self.call_count.setdefault(label, 0)
        self.call_count[label] += 1
        return self.call_count[label]

    def copyfile(self, f1, f2):
        f1 = os.path.join(self.workdir, f1)
        f2 = os.path.join(self.workdir, f2)
        shutil.copyfile(f1, f2)

    def rmtree(self, f1):
        f1 = os.path.join(self.workdir, f1)
        shutil.rmtree(f1)

    def filecmp(self, f1, f2):
        f1 = os.path.join(self.workdir, f1)
        f2 = os.path.join(self.workdir, f2)
        return filecmp.cmp(f1, f2)

    def run_cmd(self, cmd, label=None):
        """
        Command execution
        """
        if self.verbose:
            print("## {:s}".format(" ".join(cmd)))

        if not label:
            label = os.path.basename(cmd[0])

        # What's the count for this command?
        ccount = self.get_incr_call_count(label)

        # What's the log name?
        log_file_prefix = os.path.join(
            self.workdir, "{:s}_out_{:d}".format(label, ccount)
        )

        # Run the command
        atg_misc.run_cmd(
            cmd, cwd=self.workdir, log_file_prefix=log_file_prefix, shell=False
        )

    def merge_attributes(self, atg_file):
        file_bl = os.path.join(self.workdir, FILE_BL)
        file_atg = os.path.join(self.workdir, atg_file)
        file_merged = os.path.join(self.workdir, FILE_MERGED)
        atg_merge_attrs.MergeDisplayAttributes.merge(file_bl, file_atg, file_merged)

    def strip_unchanged(self):
        file_merged = os.path.join(self.workdir, FILE_MERGED)
        file_unchanged_removed = os.path.join(self.workdir, FILE_UNCHANGED_REMOVED)
        atg_proc_unchanged.ProcForUnchanged.strip_unchanged(
            file_merged, file_unchanged_removed
        )

    def strip_failures(self, file_1, file_2):
        vpython = os.path.join(VC_PATH, "vpython")
        strip_fail_script = os.path.join(SCRIPTS_HOME_DIR, "strip_failures.py")
        self.run_cmd([vpython, strip_fail_script, file_1, file_2])

    def run_clicast(self, args, label="clicast"):
        clicast = os.path.join(VC_PATH, "clicast")
        self.run_cmd([clicast] + args, label=label)

    def run(
        self,
        run_atg=True,
        atg_file=FILE_ATG,
        max_iter=8,
        check_fixedpoint=True,
        copy_out_manage=True,
    ):

        atg_misc.print_msg(
            "Generating baseline test-cases for environment {:s}".format(self.env_dir)
        )

        assert (
            max_iter > 0
        ), "max iters must be greater than zero, otherwise the tst will not be correctly stripped for ATTRIBUTES"

        #
        # Build the env, the baselining tests and the ATG tests
        #
        try:
            self.rmtree(self.env_dir)
        except FileNotFoundError:
            pass

        self.run_clicast(["-l", "c", "ENVironment", "script", "run", self.env_file])
        self.run_clicast(["-e", self.env_dir, "tools", "auto_baseline_test", FILE_BL])

        if run_atg:
            self.run_clicast(["-e", self.env_dir, "tools", "auto_atg_test", atg_file])

        #
        # Merge baselining with ATG
        #
        self.merge_attributes(atg_file)

        #
        # Strip unchanged
        #
        self.strip_unchanged()

        atg_misc.print_msg(
            "Executing test-cases for environment {:s}".format(self.env_dir)
        )

        #
        # Run the .tst, generate the expecteds and then re-generate the .tst
        #
        self.run_clicast(
            ["-e", self.env_dir, "test", "script", "run", FILE_UNCHANGED_REMOVED]
        )
        self.run_clicast(
            ["-e", self.env_dir, "execute", "batch", "--update_coverage_data"]
        )
        self.run_clicast(["-e", self.env_dir, "TESt", "ACtuals_to_expected"])
        self.run_clicast(
            ["-e", self.env_dir, "test", "script", "create", FILE_EXPECTEDS]
        )

        atg_misc.print_msg(
            "Generating expected values for environment {:s}".format(self.env_dir)
        )

        #
        # Rebuild the environment and import our tst with expected values --
        # execute it to get pass/fail data and then re-create the .tst
        #
        try:
            self.rmtree(self.env_dir)
        except Exception as e:
            print(e)
            return

        self.run_clicast(["-l", "c", "ENVironment", "script", "run", self.env_file])
        self.run_clicast(["-e", self.env_dir, "test", "script", "run", FILE_EXPECTEDS])
        self.run_clicast(
            ["-e", self.env_dir, "execute", "batch", "--update_coverage_data"]
        )
        self.run_clicast(
            ["-e", self.env_dir, "test", "script", "create", FILE_INTERMEDIATE]
        )

        self.copyfile(FILE_INTERMEDIATE, "stripped_1.tst")

        terminate = False
        for i in range(1, max_iter + 1):
            now = "stripped_{:d}.tst".format(i)
            next_file = "stripped_{:d}.tst".format(i + 1)

            self.strip_failures(now, next_file)

            if check_fixedpoint and self.filecmp(now, next_file):
                if self.verbose:
                    print(
                        "Files are the same, will terminate in this iteration (i={:d}).".format(
                            i
                        )
                    )
                terminate = True

            try:
                self.rmtree(self.env_dir)
            except Exception as e:
                print(e)
                return

            self.run_clicast(["-l", "c", "ENVironment", "script", "run", self.env_file])
            self.run_clicast(["-e", self.env_dir, "test", "script", "run", next_file])
            self.run_clicast(
                ["-e", self.env_dir, "execute", "batch", "--update_coverage_data"]
            )
            self.run_clicast(
                ["-e", self.env_dir, "test", "script", "create", next_file]
            )

            if terminate:
                break

        self.copyfile(next_file, FILE_FINAL)
        if copy_out_manage:
            self.copyfile(
                FILE_FINAL,
                os.path.join(
                    "..", "..", "environment", "{env_dir:s}", "{env_dir:s}.tst"
                ).format(env_dir=self.env_dir),
            )


# EOF
