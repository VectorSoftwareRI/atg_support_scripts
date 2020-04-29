import os

import atg_execution.scm_hooks as atg_scm_hooks
from functools import partial


def store_updated_tests(changed_files):
    print(changed_files)


def get_configuration(options):
    # What's the path to our repo?
    repository_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/s2n_vc/src/s2n")
    )

    # What's the path to our Manage root folder?
    manage_vcm_path = os.path.abspath(
        os.path.expandvars("${HOME}/clones/s2n_vc/vcast/s2n_vc.vcm")
    )

    # What two shas do we want to analyse?
    current_id = "c158f0c8cb190b5121702fbe0e2b16547c5b63b4"
    new_id = "4caa406c233b57e6f0bb7d5a62c83aca237b7e31"

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
        "store_updated_tests": store_updated_tests,
    }

    return configuration


# EOF


# EOF
