from collections import namedtuple

configuration = namedtuple(
    "configuration",
    [
        "repository_path",
        "manage_vcm_path",
        "final_tst_path",
        "find_unchanged_files",
        "options",
    ],
)


def parse_configuration(configuration_dict, options):
    assert "repository_path" in configuration_dict
    assert "manage_vcm_path" in configuration_dict

    repository_path = configuration_dict["repository_path"]
    manage_vcm_path = configuration_dict["manage_vcm_path"]
    final_tst_path = configuration_dict.get("final_tst_path", None)
    find_unchanged_files = configuration_dict.get("find_unchanged_files", None)

    return configuration(
        repository_path, manage_vcm_path, final_tst_path, find_unchanged_files, options
    )


# EOF
