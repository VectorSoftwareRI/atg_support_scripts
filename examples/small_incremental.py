import os

import atg_execution.misc as atg_misc
import atg_execution.scm_hooks as atg_scm_hooks
from functools import partial


def get_configuration(options):
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

    # What two shas do we want to analyse?
    current_id, new_id = atg_misc.parse_git_for_hashes(repository_path)

    # Build-up an impact object
    impact_object = atg_scm_hooks.GitImpactedObjectFinder(
        repository_path, allow_moves=options.allow_moves
    )

    # Create a 'future' for the unchanged function call
    find_unchanged_files = partial(
        impact_object.calculate_preserved_files, current_id=current_id, new_id=new_id
    )

    configuration = {
        "repository_path": repository_path,
        "manage_vcm_path": manage_vcm_path,
        "find_unchanged_files": find_unchanged_files,
    }

    return configuration


# EOF
