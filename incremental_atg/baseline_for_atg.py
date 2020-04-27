#!/usr/bin/env python3

import os
import shutil
import filecmp
import incremental_atg.merge_display_attributes as atg_merge_attrs
import incremental_atg.misc as atg_misc


FILE_BL = "bl.tst"
FILE_ATG = "atg.tst"
FILE_MERGED = "merged.tst"
FILE_EXPECTEDS = "expecteds.tst"
FILE_INTERMEDIATE = "intermediate.tst"
FILE_STRIPPED = "stripped.tst"
FILE_FINAL = "final.tst"

SCRIPTS_HOME_DIR = os.path.dirname(__file__)
ENV_EXT = ".env"
VC_PATH = os.getenv("VECTORCAST_DIR")


@atg_misc.for_all_methods(atg_misc.log_entry_exit)
class Baseline:
    def __init__(self, env_file, verbose=1):
        self.env_file = os.path.basename(env_file)
        self.env_dir = os.path.splitext(self.env_file)[0]
        self.workdir = os.path.dirname(os.path.abspath(env_file))
        self.call_count = dict()
        self.verbose = verbose

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
        # Run the .tst, generate the expecteds and then re-generate the .tst
        #
        self.run_clicast(["-e", self.env_dir, "test", "script", "run", FILE_MERGED])
        self.run_clicast(
            ["-e", self.env_dir, "execute", "batch", "--update_coverage_data"]
        )
        self.run_clicast(["-e", self.env_dir, "TESt", "ACtuals_to_expected"])
        self.run_clicast(
            ["-e", self.env_dir, "test", "script", "create", FILE_EXPECTEDS]
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


def get_env_file():
    """
    Finds the first .env file in the current directory
    """
    env_file = None
    for f in os.listdir("."):
        if f.endswith(ENV_EXT):
            env_file = f
    assert env_file is not None
    return env_file


def main():
    b = Baseline(env_file=get_env_file())
    b.run(run_atg=True)


if __name__ == "__main__":
    main()

# EOF
