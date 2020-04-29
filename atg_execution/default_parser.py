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

    return parser


def boolean_string(s):
    if s not in {"False", "True"}:
        raise ValueError("Not a valid boolean string")
    return s == "True"


def validate_options(options):
    """
    Checks if option combinations are valid
    """

    options_are_value = True
    msg = None

    if options.skip_build == options.clean_up:
        if not options.skip_build:
            # skip_build = False, clean_up = False
            msg = "you must clean-up if you're *not* skipping the build"
        else:
            # skip_build = True, clean_up = True
            msg = "you cannot skip the build if you've cleaned-up"
        options_are_value = False

    if not isinstance(options.verbose, bool):
        msg = "Verbose must be a bool"
        options_are_value = False

    if not options_are_value:
        assert msg is not None
        print("INVALID CONFIGURATION -- {:s}".format(msg))

    return options_are_value


# EOF