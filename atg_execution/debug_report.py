# The MIT License
#
# Copyright (c) 2020 Vector Informatik, GmbH. http://vector.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
from terminaltables import AsciiTable
from textwrap import wrap


def find_all_files_from_root(root, exts=[]):

    all_files = set()

    for root, _, files in os.walk(root):
        if root.startswith(".git"):
            continue

        for fname in files:
            if fname.startswith(".git"):
                continue

            for ext in exts:
                if fname.lower().endswith(ext):
                    all_files.add(os.path.join(root, fname))
            else:
                all_files.add(os.path.join(root, fname))

    return set(sorted(all_files))


def join_wrap_list(alist, max_width=20):
    wrapped = "\n".join(wrap(", ".join(alist), max_width, fix_sentence_endings=True))
    wrapped = ",".join(alist)
    if len(wrapped) > max_width:
        suffix = " ..."
        suffix_len = len(suffix)
        wrapped = wrapped[: max_width - suffix_len] + suffix
    return wrapped


def files_report(configuration, unchanged_files, environment_dependencies):
    print("*" * 10 + " Files report " + "*" * 10)
    repository_path = configuration.repository_path
    all_files = find_all_files_from_root(repository_path)
    rel_all_files = set(
        [os.path.relpath(fname, repository_path) for fname in all_files]
    )
    changed_files = rel_all_files - unchanged_files

    exts = [".c", ".h"]
    src_files = [
        fname for fname in rel_all_files if any([fname.endswith(ext) for ext in exts])
    ]

    changed_src_files = changed_files.intersection(src_files)
    unchanged_src_files = unchanged_files.intersection(src_files)

    count_all_files = len(rel_all_files)
    count_src_files = len(src_files)
    count_changed_src_files = len(changed_src_files)
    count_unchanged_src_files = len(unchanged_src_files)

    environment_stats_data = [
        ["Category", "Count"],
        ["All files", count_all_files],
        ["Sources files", count_src_files],
        ["Source files needing processing", count_changed_src_files],
        ["Source files not needing processing", count_unchanged_src_files],
    ]
    print(AsciiTable(environment_stats_data).table)

    environment_details_data = [
        ["Filename", "Needs\nprocessing?", "Used by\n(count)", "Used by"],
    ]
    for rel_fname in sorted(rel_all_files):
        impacted = rel_fname in changed_files
        used_by = environment_dependencies.fnames_to_envs.get(rel_fname, [])
        if not used_by:
            continue
        used_by_count = len(used_by)
        used_by_str = join_wrap_list([os.path.basename(env) for env in used_by])
        environment_details_data.append(
            [rel_fname, impacted, used_by_count, used_by_str]
        )
    print(AsciiTable(environment_details_data).table)


def environments_report(
    configuration,
    unchanged_files,
    manage_builder,
    environment_dependencies,
    impacted_envs,
):
    print("*" * 10 + " Environments report " + "*" * 10)
    failed_envs = manage_builder.all_environments - manage_builder.built_environments

    count_all_envs = len(manage_builder.all_environments)
    count_built_envs = len(manage_builder.built_environments)
    count_failed_envs = len(failed_envs)
    count_impacted_envs = len(impacted_envs)

    file_stat_data = [
        ["Category", "Count"],
        ["All environments", count_all_envs],
        ["Environments successfully built", count_built_envs],
        ["Environments not built", count_failed_envs],
        ["Environments needing processing", count_impacted_envs],
    ]
    print(AsciiTable(file_stat_data).table)

    file_details_data = [
        [
            "Environment",
            "Path",
            "Built?",
            "Needs\nprocessing?",
            "Units",
            "Routines",
            "All dependencies\n(count)",
            "All dependencies",
            "Impacted\ndependencies",
        ],
    ]
    for env, path in sorted(manage_builder.all_environments):
        env_path = os.path.join(path, env)
        needs_processing = env_path in impacted_envs
        used_files = environment_dependencies.envs_to_fnames.get(env_path, set())
        used_files_count = len(used_files)
        units = environment_dependencies.envs_to_units.get(env_path, {})

        built = (env, path) in manage_builder.built_environments

        path = join_wrap_list([path])
        deps = join_wrap_list(used_files)

        used_changed = used_files.difference(unchanged_files)
        used_changed_str = join_wrap_list(used_changed)

        rout_count = 0
        for _, functions in units.items():
            rout_count += len(functions)

        file_details_data.append(
            [
                env,
                path,
                built,
                needs_processing,
                len(units),
                rout_count,
                used_files_count,
                deps,
                used_changed_str,
            ]
        )

    print(AsciiTable(file_details_data).table)


def debug_report(
    configuration,
    unchanged_files,
    manage_builder,
    environment_dependencies,
    impacted_envs,
):

    files_report(configuration, unchanged_files, environment_dependencies)

    environments_report(
        configuration,
        unchanged_files,
        manage_builder,
        environment_dependencies,
        impacted_envs,
    )


# EOF
