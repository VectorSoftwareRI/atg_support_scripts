from collections import namedtuple

configuration = namedtuple(
    "configuration",
    ["repository_path", "manage_vcm_path", "final_tst_path", "unchanged_files"],
)


def parse_configuration(configuration_dict):
    assert "repository_path" in configuration_dict
    assert "manage_vcm_path" in configuration_dict

    repository_path = configuration_dict["repository_path"]
    manage_vcm_path = configuration_dict["manage_vcm_path"]
    final_tst_path = configuration_dict.get("final_tst_path", None)
    unchanged_files = configuration_dict.get("unchanged_files", None)

    return configuration(
        repository_path, manage_vcm_path, final_tst_path, unchanged_files
    )


# EOF
