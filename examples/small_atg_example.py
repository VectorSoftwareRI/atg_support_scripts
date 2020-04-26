import os

import incremental_atg.misc as atg_misc
import incremental_atg.scm_hooks as atg_scm_hooks

def get_configuration_object():
    # What's the path to our repo?
    repo_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/atg_workflow_vc/src")
    )

    # What's the path to our Manage vcm file?
    vcm_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/atg_workflow_vc/vcast/atg_workflow_vc.vcm")
    )

    # Path to the Manage artefacts
    manage_path = os.path.splitext(vcm_path)[0]

    # What's the path to our Manage root folder?
    final_tst_path = os.path.join(manage_path, "environment")

    # Set the environment variable needed for the environments to build
    os.environ["ATG_WORKFLOW_VC_SRC_PATH"] = repo_path

    # What two shas do we want to analyse?
    current_sha, new_sha = atg_misc.parse_git_for_hashes(repo_path)

    # Create an scm analysis object
    scm_analysis_class = atg_scm_hooks.GitImpactedObjectFinder

    return repo_path, vcm_path, final_tst_path, scm_analysis_class, current_sha, new_sha

# EOF
