#!/usr/bin/env python3

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


def main():

    if len(sys.argv) - 1 < 4:
        print("{:s} <input> <output> <subprograms> <regex>")
        sys.exit(1)

    input_file, output_file, subprograms_str, pattern = sys.argv[1:]

    tst_file = TstFile(input_file, output_file)
    tst_file.remove(subprograms_str, pattern)


if __name__ == "__main__":
    main()

# EOF
