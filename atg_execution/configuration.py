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
