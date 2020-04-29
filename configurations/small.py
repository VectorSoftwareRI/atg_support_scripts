import os


def get_configuration():
    # What's the path to our repo?
    repository_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/atg_workflow_vc/src")
    )

    # What's the path to our Manage vcm file?
    manage_vcm_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/atg_workflow_vc/vcast/atg_workflow_vc.vcm")
    )

    # Set the environment variable needed for the environments to build
    os.environ["ATG_WORKFLOW_VC_SRC_PATH"] = repository_path

    configuration = {
        "repository_path": repository_path,
        "manage_vcm_path": manage_vcm_path,
    }

    return configuration


# EOF
