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
import configargparse

DEFAULT_CONFIG = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.txt")
)


def get_default_parser():

    parser = configargparse.ArgParser(default_config_files=[DEFAULT_CONFIG])
    parser.add(
        "-c",
        "--config-file",
        required=False,
        is_config_file=True,
        help="config file path",
    )
    parser.add(
        "-p", "--config_py", required=True, help="Python configuration object", type=str
    )
    parser.add("-t", "--timeout", required=True, help="timeout", type=int)
    parser.add("-r", "--report", required=True, help="report", type=boolean_string)
    parser.add("-dr", "--dry_run", required=True, help="dry-run", type=boolean_string)
    parser.add(
        "-bli",
        "--baseline_iterations",
        required=True,
        help="baseline iterations",
        type=int,
    )
    parser.add("-k", "--clean_up", required=True, help="clean up", type=boolean_string)
    parser.add(
        "-sb", "--skip_build", required=True, help="skip build", type=boolean_string
    )
    parser.add("--limit_unchanged", required=True, help="limit unchanged", type=int)
    parser.add("--allow_moves", required=True, help="allow moves", type=boolean_string)
    parser.add(
        "--allow_broken_environments",
        required=True,
        help="allow broken environments",
        type=boolean_string,
    )
    parser.add("-l", "--logging", required=False, help="log calls", type=boolean_string)
    parser.add("-lf", "--log_file", required=False, help="log file", type=str)
    parser.add("-v", "--verbose", required=False, help="verbose", type=boolean_string)
    parser.add("-q", "--quiet", required=False, help="quiet", type=boolean_string)
    parser.add(
        "-sr",
        "--strict_rc",
        required=False,
        help="strict return code checking",
        type=boolean_string,
    )
    parser.add("-j", "--workers", required=False, help="workers", type=nullable_int)
    parser.add(
        "--atg_work_dir",
        required=False,
        help="set the ATG working directory",
        type=nullable_string,
    )
    parser.add(
        "--gen_fptrs",
        required=False,
        help="Generate function pointers",
        type=nullable_string,
    )

    return parser


def boolean_string(s):
    if s not in {"False", "True"}:
        raise ValueError("Not a valid boolean string")
    return s == "True"


def nullable_string(s):
    if s == "None":
        return None
    return s


def nullable_int(s):
    if s == "None":
        return None
    return int(s)


def validate_options(options):
    """
    Checks if option combinations are valid
    """

    options_are_valid = True
    msg = None

    if options.skip_build == options.clean_up:
        if not options.skip_build:
            # skip_build = False, clean_up = False
            msg = "you must clean-up if you're *not* skipping the build"
        else:
            # skip_build = True, clean_up = True
            msg = "you cannot skip the build if you've cleaned-up"
        options_are_valid = False

    if not isinstance(options.verbose, bool):
        msg = "Verbose must be a bool"
        options_are_valid = False

    if not isinstance(options.quiet, bool):
        msg = "Quiet must be a bool"
        options_are_valid = False

    if options.verbose and options.quiet:
        msg = "You cannot both be quiet and verbose"
        options_are_valid = False

    if options.report and options.quiet:
        msg = "Generating report and being quiet are not compatible"
        options_are_valid = False

    if not options_are_valid:
        assert msg is not None
        print("INVALID CONFIGURATION -- {:s}".format(msg))

    return options_are_valid


# EOF
