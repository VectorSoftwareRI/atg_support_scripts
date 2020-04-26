import os


def debug_report(
    repository_path,
    current_sha,
    new_sha,
    scm_analyser,
    preserved_files,
    limit_unchanged,
    manage_vcm_path,
    manage_builder,
    manage_dependencies,
    impacted_envs,
):

    print("#" * 80)
    print(
        "After analysing {repo:s} between {before:s} and {after:s}".format(
            repo=repository_path, before=current_sha, after=new_sha
        )
    )
    print(
        "   There were {total:d} total files".format(
            total=len(scm_analyser._find_all_files())
        )
    )
    print(
        "   There were {changed:d} changed files".format(
            changed=len(scm_analyser._find_changed_files(current_sha, new_sha))
        )
    )
    print(
        "   We calculated that the following {unchanged:d} files were _unchanged_ (limited to {limit_unchanged:d}):".format(
            unchanged=len(preserved_files), limit_unchanged=limit_unchanged
        )
    )
    for preserved_file in list(preserved_files)[:limit_unchanged]:
        print("      {:s}".format(preserved_file))
    print("#" * 80)
    print("#" * 80)
    print(
        "After building {vcm:s}, we found {envs:d} environments:".format(
            vcm=manage_vcm_path, envs=len(manage_builder.environments)
        )
    )
    for env in manage_builder.environments:
        print("      {:s}".format(env[0]))
    print("#" * 80)
    print("#" * 80)
    print(
        "After processing {vcm:s}, we found the following routine counts:".format(
            vcm=manage_vcm_path
        )
    )
    for env_path, units in manage_dependencies.envs_to_units.items():
        rout_count = 0
        for unit, functions in units.items():
            rout_count += len(functions)
        env = os.path.basename(env_path)
        print("      {:s} had {:d} routines".format(env, rout_count))
    print("#" * 80)
    print("#" * 80)
    print(
        "After processing {vcm:s}, we found the following used {files:d} files:".format(
            vcm=manage_vcm_path, files=len(manage_dependencies.fnames_to_envs)
        )
    )
    for fname in manage_dependencies.fnames_to_envs:
        suffix = "UNCHANGED" if fname in preserved_files else "CHANGED"
        env_counts = len(manage_dependencies.fnames_to_envs[fname])
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
        used_files = manage_dependencies.envs_to_fnames[env_path]
        impacted_deps = used_files - preserved_files
        units = manage_dependencies.envs_to_units[env_path]
        rout_count = 0
        for unit, functions in units.items():
            rout_count += len(functions)
        print(
            "    {env:s} ({rout_count:d} routines) due to {files:s}".format(
                env=env, rout_count=rout_count, files=", ".join(impacted_deps)
            )
        )
    print("#" * 80)


# EOF
