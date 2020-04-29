import os


def get_configuration(options):
    # What's the path to our repo?
    repository_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/s2n_vc/src/s2n")
    )

    # What's the path to our Manage root folder?
    manage_vcm_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/s2n_vc/vcast/s2n_vc.vcm")
    )

    # Set the environment variable needed for the environments to build
    os.environ["S2N_VC_SRC_PATH"] = repository_path

    configuration = {
        "repository_path": repository_path,
        "manage_vcm_path": manage_vcm_path,
    }

    return configuration


# EOF
