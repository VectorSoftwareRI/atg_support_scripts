import os

def find_all_files_from_root(root, exts=[]):

    all_files = set()

    for root, _, files in os.walk(root):
        for fname in files:
            for ext in exts:
                if fname.lower().endswith(ext):
                    all_files.add(os.path.join(root, fname))

    return set(sorted(all_files))


def debug_report(
    configuration,
    unchanged_files,
    manage_builder,
    environment_dependencies,
    impacted_envs,
):

    repository_path = configuration.repository_path
    all_files = find_all_files_from_root(repository_path, exts=[".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hxx"])
    assert unchanged_files.issubset(all_files)
    current_id = "None"
    new_id = "None"
    scm_analyser = "None"
    limit_unchanged = configuration.options.limit_unchanged
    manage_vcm_path = configuration.manage_vcm_path

    change_str = "(with changes)" if configuration.find_unchanged_files is not None else "(without changes)"

    print("#" * 80)
    print(
            "After analysing {repo:s} {change:s}".format(
            repo=repository_path, change=change_str,
        )
    )
    print(
        "   There were {total:d} total files".format(
            total=len(all_files)
        )
    )
    print(
        "   There were {changed:d} changed files".format(
            changed=len(all_files - unchanged_files)
        )
    )
    print(
        "   We calculated that the following {unchanged:d} files:".format(
            unchanged=len(unchanged_files)
        )
    )
    for preserved_file in list(unchanged_files):
        print("      {:s}".format(preserved_file))
    print("#" * 80)
    print("#" * 80)
    print(
        "After building {vcm:s}, we found {envs:d} environments:".format(
            vcm=manage_vcm_path, envs=len(manage_builder.all_environments)
        )
    )
    for env in manage_builder.all_environments:
        status = "BUILT" if env in manage_builder.built_environments else "NOT BUILT"
        print("      {:s} (status: {:s})".format(env[0], status))
    print("#" * 80)
    print("#" * 80)
    print(
        "After processing {vcm:s}, we found the following routine counts:".format(
            vcm=manage_vcm_path
        )
    )
    for env_path, units in environment_dependencies.envs_to_units.items():
        rout_count = 0
        for _, functions in units.items():
            rout_count += len(functions)
        env = os.path.basename(env_path)
        print("      {:s} had {:d} routines".format(env, rout_count))
    print("#" * 80)
    print("#" * 80)
    print(
        "After processing {vcm:s}, we found the following used {files:d} files:".format(
            vcm=manage_vcm_path, files=len(environment_dependencies.fnames_to_envs)
        )
    )
    for fname in environment_dependencies.fnames_to_envs:
        suffix = "UNCHANGED" if fname in unchanged_files else "CHANGED"
        env_counts = len(environment_dependencies.fnames_to_envs[fname])
        print(
            "      {fname:s} {suffix:s} (used in {count:d} envs)".format(
                fname=fname, suffix=suffix, count=env_counts
            )
        )
    print("#" * 80)
    print("#" * 80)
    print("After processing the changes, we will re-run these environments")
    for env_path in impacted_envs:
        env = os.path.basename(env_path)
        used_files = environment_dependencies.envs_to_fnames[env_path]
        impacted_deps = used_files - unchanged_files
        units = environment_dependencies.envs_to_units[env_path]
        rout_count = 0
        for _, functions in units.items():
            rout_count += len(functions)
        print(
            "    {env:s} ({rout_count:d} routines) due to {files:s}".format(
                env=env, rout_count=rout_count, files=", ".join(impacted_deps)
            )
        )
    print("#" * 80)


# EOF
