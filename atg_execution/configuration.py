import os
from collections import namedtuple

configuration = namedtuple(
    "configuration",
    [
        "repository_path",
        "manage_vcm_path",
        "final_tst_path",
        "find_unchanged_files",
        "store_updated_tests",
        "options",
    ],
)


def parse_configuration(configuration_dict, options):
    assert "repository_path" in configuration_dict
    assert "manage_vcm_path" in configuration_dict

    repository_path = configuration_dict["repository_path"]
    manage_vcm_path = configuration_dict["manage_vcm_path"]
    if "final_tst_path" not in configuration_dict:
        manage_dir = os.path.dirname(manage_vcm_path)
        manage_project = os.path.splitext(os.path.basename(manage_vcm_path))[0]
        final_tst_path = os.path.join(manage_dir, manage_project, "environment")
    else:
        final_tst_path = configuration_dict["final_tst_path"]

    if "store_updated_tests" not in configuration_dict:
        store_updated_tests = lambda files: None
    else:
        store_updated_tests = configuration_dict["store_updated_tests"]

    find_unchanged_files = configuration_dict.get("find_unchanged_files", None)

    return configuration(
        repository_path,
        manage_vcm_path,
        final_tst_path,
        find_unchanged_files,
        store_updated_tests,
        options,
    )


# EOF
