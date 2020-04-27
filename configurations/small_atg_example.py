import os

import incremental_atg.misc as atg_misc
import incremental_atg.scm_hooks as atg_scm_hooks


def get_configuration():
    # What's the path to our repo?
    repository_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/atg_workflow_vc/src")
    )

    # What's the path to our Manage vcm file?
    manage_vcm_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/atg_workflow_vc/vcast/atg_workflow_vc.vcm")
    )

    # Path to the Manage artefacts
    manage_path = os.path.splitext(manage_vcm_path)[0]

    # What's the path to our Manage root folder?
    final_tst_path = os.path.join(manage_path, "environment")

    # Set the environment variable needed for the environments to build
    os.environ["ATG_WORKFLOW_VC_SRC_PATH"] = repository_path

    # What two shas do we want to analyse?
    current_id, new_id = atg_misc.parse_git_for_hashes(repository_path)

    # Create an scm analysis object
    scm_analysis_class = atg_scm_hooks.GitImpactedObjectFinder

    configuration = {
        "repository_path": repository_path,
        "manage_vcm_path": manage_vcm_path,
        "final_tst_path": final_tst_path,
        "scm_analysis_class": scm_analysis_class,
        "current_id": current_id,
        "new_id": new_id,
    }

    return configuration


def persist_changes(changed_files):
    if changed_files:
        print("Persisting ...")
        for fname in changed_files:
            print("    {:s}".format(fname))
    else:
        print("No changes?")


# EOF
