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

pointer_deref_matcher = re.compile("\[\d*\]")


class TstLine:
    """
    .tst line inspector
    """

    def __init__(self, line):
        self.line = line

    @property
    def is_expected(self):
        return self.line.startswith("TEST.EXPECTED:")

    @property
    def is_attribute(self):
        return self.line.startswith("TEST.ATTRIBUTES:")

    @property
    def line_key(self):
        assert self.is_attribute or self.is_expected or self.is_value
        return self.line.split(":")[1].strip()

    @property
    def line_value(self):
        assert self.is_attribute or self.is_expected or self.is_value
        return self.line.split(":")[2].strip()

    @property
    def attribute_line_key(self):
        assert self.is_attribute
        return self.line_key

    @property
    def expected_line_key(self):
        assert self.is_expected
        return self.line_key

    @property
    def expected_line_value(self):
        assert self.is_expected
        return self.line_value

    @property
    def is_value(self):
        return self.line.startswith("TEST.VALUE:")

    @property
    def value_line_key(self):
        assert self.is_value
        return self.line_key

    @property
    def value_line_value(self):
        assert self.is_value
        return self.line_value

    def is_line_for_subprog(self, subprog):
        assert self.is_value or self.is_expected or self.is_attribute
        key_subprog = self.line_key.split(".")[1].strip()
        if subprog == key_subprog:
            return True
        return False

    @property
    def has_deref(self):
        assert self.is_value or self.is_expected
        if pointer_deref_matcher.search(self.line_key):
            return True

        return False

    @property
    def has_alloc_status(self):
        assert self.is_value or self.is_expected
        val = self.line_value.strip().lower()
        if val.startswith("<<malloc") or val == "<<null>>":
            return True
        return False

    @property
    def is_global(self):
        if not self.is_value and not self.is_expected:
            return False
        return "<<GLOBAL>>" in self.line_key

    @property
    def is_return(self):
        if not self.is_value and not self.is_expected:
            return False
        line_key = self.line_key
        # <unit>.<subprog>.<param>
        if line_key.split(".")[2].strip() == "return":
            return True
        return False


@atg_misc.for_all_methods(atg_misc.log_entry_exit)
class TstFileProcessor:

    TEST_START_MARKER = "TEST.UNIT"
    TEST_END_MARKER = "TEST.END"

    def process_test_line(self, line):
        """
        Processes each test line

        Line gets ignored if this method returns None
        """
        return line

    def test_start_process(self):
        pass

    def test_end_process(self):
        """
        Gets called after we read an entire test

        Here self.current_test can be modified before
        it gets written to the output file
        """
        pass

    def process(self, input_file, output_file):

        with open(input_file, "r") as fin, open(output_file, "w") as fout:

            in_test = False
            skip_line = False

            for line in fin:

                if not in_test and line.startswith(self.TEST_START_MARKER):

                    self.test_start_process()

                    in_test = True
                    subprogram_match = False
                    pattern_match = False
                    self.subprogram = None
                    self.current_test = []
                    self.test_name = None

                if in_test:

                    if line.startswith("TEST.SUBPROGRAM:"):
                        self.subprogram = line.split(":")[1].strip()

                    if line.startswith("TEST.NAME:"):
                        self.test_name = line.split(":")[1].strip()

                    line = self.process_test_line(line)
                    if line:
                        self.current_test.append(line)

                if in_test and line.strip() == self.TEST_END_MARKER:

                    self.test_end_process()

                    # Write current test
                    for cur_test_line in self.current_test:
                        fout.write(cur_test_line)

                    in_test = False
                    skip_line = True

                if not in_test:
                    if not skip_line:
                        fout.write(line)
                    else:
                        skip_line = False


class ProcForUnchanged(TstFileProcessor):
    """
    Processing for unchanged
    """

    @classmethod
    def strip_unchanged(cls, in_file, out_file):
        p = cls()
        return p.process(in_file, out_file)

    def __init__(self):
        self.internal_inputs = {}

    def test_start_process(self):
        self.internal_inputs = {}

    def get_base_key(self, key):
        if "[" in key:
            basekey = key.split("[")[0]
            return basekey
        else:
            return key

    def mark_internal(self, key):
        self.internal_inputs.setdefault(self.get_base_key(key), True)

    def mark_external(self, key):
        self.internal_inputs[self.get_base_key(key)] = False

    def is_internal(self, key):
        basekey = self.get_base_key(key)
        ret = self.internal_inputs.get(basekey, False)
        return ret

    def process_test_line(self, line):
        """
        Process each test line right after we read it from the .tst file

            internal -- will be removed
        """
        tst_line = TstLine(line)
        if tst_line.is_value or tst_line.is_expected:
            if tst_line.is_line_for_subprog(self.subprogram):
                if tst_line.has_alloc_status:
                    self.mark_external(tst_line.line_key)
                elif tst_line.has_deref:
                    self.mark_external(tst_line.line_key)
                elif tst_line.is_global:
                    self.mark_external(tst_line.line_key)
                elif tst_line.is_return:
                    self.mark_external(tst_line.line_key)
                else:
                    self.mark_internal(tst_line.line_key)
        return line

    def test_end_process(self):
        """
        Modify the test case in memory according to the data collected
        while reading the file
        """
        modified_test = []
        for line in self.current_test:
            tst_line = TstLine(line)
            if tst_line.is_attribute and self.is_internal(tst_line.attribute_line_key):
                pass  # removing
            elif tst_line.is_expected and self.is_internal(tst_line.expected_line_key):
                pass  # removing
            else:
                modified_test.append(line)

        self.current_test = modified_test


def main():
    sf = ProcForUnchanged()
    sf.process("expecteds.tst", "proc.tst")


if __name__ == "__main__":
    main()

# EOF
