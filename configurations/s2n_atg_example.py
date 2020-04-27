import os

import incremental_atg.scm_hooks as atg_scm_hooks


def get_configuration():
    # What's the path to our repo?
    repository_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/s2n_vc/src/s2n")
    )

    # What's the path to our Manage root folder?
    manage_vcm_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/s2n_vc/vcast/s2n_vc.vcm")
    )

    # Path to the Manage artefacts
    manage_path = os.path.splitext(manage_vcm_path)[0]

    # What's the path to our Manage root folder?
    final_tst_path = os.path.join(manage_path, "environment")

    # What's the path to root src tree?
    src_path = os.path.dirname(repository_path)

    # Set the environment variable needed for the environments to build
    os.environ["S2N_VC_SRC_PATH"] = src_path

    # What two shas do we want to analyse?
    current_id = "c158f0c8cb190b5121702fbe0e2b16547c5b63b4"
    new_id = "4caa406c233b57e6f0bb7d5a62c83aca237b7e31"

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
