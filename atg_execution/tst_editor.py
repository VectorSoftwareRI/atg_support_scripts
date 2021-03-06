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

import sys
import re

import atg_execution.misc as atg_misc


@atg_misc.for_all_methods(atg_misc.log_entry_exit)
class TstFile(object):

    TEST_START_MARKER = "TEST.UNIT"
    TEST_END_MARKER = "TEST.END"

    def __init__(self, input_file, output_file):
        self.in_path = input_file
        self.out_path = output_file

    def __repr__(self):
        return str({"in_path": self.in_path, "out_path": self.out_path})

    def remove(self, subprogram_regex, re_pattern):
        with open(self.out_path, "w") as output_file:
            self.process(self.in_path, output_file, subprogram_regex, re_pattern)

    def process(self, filepath, output_file, subprogram_regex, re_pattern):

        content_matcher = re.compile(re_pattern)
        subprogram_matcher = re.compile(subprogram_regex)

        with open(filepath, "r") as f:

            in_test = False
            skip_line = False

            for line in f:

                if not in_test and line.startswith(self.TEST_START_MARKER):

                    in_test = True
                    subprogram_match = False
                    pattern_match = False
                    self.current_test = []

                if in_test:

                    self.current_test.append(line)

                    if line.startswith("TEST.SUBPROGRAM:"):
                        subprogram = line.split(":")[1].strip()

                        subprogram_match = subprogram_matcher.search(subprogram)

                    pattern_match = pattern_match or content_matcher.search(line)

                if in_test and line.strip() == self.TEST_END_MARKER:

                    # Write current test
                    if not (pattern_match and subprogram_match):
                        for cur_test_line in self.current_test:
                            output_file.write(cur_test_line)

                    in_test = False
                    skip_line = True

                if not in_test:
                    if not skip_line:
                        output_file.write(line)
                    else:
                        skip_line = False


# EOF
