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

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
)

import glob
import os
import sys
import re
from vector.apps.DataAPI.unit_test_api import Api
from operator import attrgetter


class StripFailures(object):
    def __init__(self, env_name, input_tst, output_tst, disable_failures=False):

        # Environment we're processing
        self.env_name = env_name

        # Input file
        self.input_tst = input_tst

        # Output file
        self.output_tst = output_tst

        # Are we disabling failing tests?
        self.disable_failures = disable_failures

        # Input lines
        self.input_lines = open(self.input_tst).readlines()

        # API object on our environment
        self.api = Api(self.env_name)

        # The lines we expect to strip
        self.to_strip = {}

        # Tests we want to disable
        self.hard_terminations = {}

    def calculate_failures(self):
        """
        Uses DataAPI to find all of the test-case failures for a given
        environment
        """

        # Iterate on all test-cases
        for test in self.api.TestCase.all():

            # Get the current unit/function/test-case name
            curr_unit = test.unit_display_name
            curr_func = test.function_display_name_ada
            curr_name = test.name

            # Did this test-case have a "hard termination"?
            hard_termination = bool(test.failure_reasons) or bool(
                test.history.get_signals()
            )

            # Build-up the default dictionary contents
            if curr_unit not in self.hard_terminations:
                self.hard_terminations[curr_unit] = {}
            if curr_func not in self.hard_terminations[curr_unit]:
                self.hard_terminations[curr_unit][curr_func] = {}

            # Store if this test had a "hard termination"
            self.hard_terminations[curr_unit][curr_func][curr_name] = hard_termination

            #
            # Get the expected values for the whole test
            #
            # TODO: ATG doesn't need the user-code ones
            #
            all_expected = (
                test.expected + test.expected_user_code + test.input_user_code
            )

            if not test.passed and all(map(attrgetter("passed"), all_expected)):
                #
                # If the test did not pass, and all of the tests failed
                #
                # TODO: understand why this is neccessary vs. the below
                #
                failed = test.expected
            else:
                # This gets all of the failed values
                failed = [x for x in test.expected if not x.passed]

            # If we have failed elements
            if failed:
                # For each failed element
                for f in failed:

                    # Build-up the default dictionary contents
                    if curr_unit not in self.to_strip:
                        self.to_strip[curr_unit] = {}
                    if curr_func not in self.to_strip[curr_unit]:
                        self.to_strip[curr_unit][curr_func] = {}
                    if curr_name not in self.to_strip[curr_unit][curr_func]:
                        self.to_strip[curr_unit][curr_func][curr_name] = set()

                    # Get the name of the current expected value
                    curr_item = f.name

                    # Replace `.[0]` with `[0]` -- probably fixed in DataAPI?
                    if ".[0]" in curr_item:
                        curr_item = curr_item.replace(".[0]", "[0]")

                    if ".class members" in curr_item:
                        curr_item = curr_item.replace(".class members", "")

                    if " instance>>" in curr_item:
                        curr_item = re.sub("<<([^>]*) instance>>", "(cl).\g<1>", curr_item)

                    # Store that we want to strip this failure
                    self.to_strip[curr_unit][curr_func][curr_name].add(curr_item)


    def write_stripped(self):
        """
        Writes-out a 'stripped' tst removing any failures
        """

        # Open-up the output file
        with open(output_tst, "w") as stripped:

            #
            # Are we inside of an import failures block?
            #
            # Persists across multiple lines (so outside of the loop)
            #
            in_import_failures = False

            # For each input line
            for line in self.input_lines:

                # Boolean flag to determine if we want to strip this line
                strip = False

                if line.startswith("TEST.END_IMPORT_FAILURES:"):
                    # Record we're no longer in import failures
                    in_import_failures = False

                    # But still strip this tag!
                    strip = True

                elif line.startswith("TEST.IMPORT_FAILURES:"):
                    #
                    # Record we're in an import failures block (line is
                    # implicitly stripped)
                    #
                    in_import_failures = True

                elif line.startswith("TEST.UNIT:"):
                    # Find the unit
                    curr_unit = line.split(":")[1].strip()

                elif line.startswith("TEST.SUBPROGRAM:"):
                    # Find the subprogram
                    #
                    # TODO: this is probably broken for C++ due to `::`
                    #
                    curr_func = line.split(":", 1)[1].split("(", 1)[0].strip()

                elif line.startswith("TEST.NAME:"):
                    # Find the test-case name
                    curr_name = line.split(":")[1].strip()

                elif (
                    line.startswith("TEST.ATTRIBUTES:")
                    and "DISPLAY_STATE=DISPLAY" in line
                ):
                    # We always want to remove display attributes
                    strip = True

                elif "<<out-of-range>>" in line:
                    #
                    # We always want to remove values that haven't come out
                    # correctly
                    #
                    strip = True

                elif line.startswith("TEST.EXPECTED:"):
                    # If we have an expected value ...

                    # Find the name of the current item
                    curr_item = line.split(":", 1)[1].strip()
                    curr_item = ":".join(curr_item.split(":")[:-1])

                    # Obtain all of the lines to remove for the current test-case
                    try:
                        to_remove = self.to_strip[curr_unit][curr_func][curr_name]
                    except KeyError:
                        to_remove = set()

                    # If our current item is in 'to_strip' ...
                    if curr_item in to_remove:
                        # ... mark it for removal
                        strip = True

                elif line.strip() == "TEST.END" and not in_import_failures:

                    # If we're disabling failures and the test failed
                    if (
                        self.disable_failures
                        and self.hard_terminations[curr_unit][curr_func][curr_name]
                    ):
                        stripped.write("TEST.COMPOUND_ONLY\n")

                # If we're not stripping this line ...
                if not strip and not in_import_failures:
                    # ... write it out!
                    stripped.write(line)

    def main(self):
        """
        Entry-point for the class
        """
        self.calculate_failures()
        self.write_stripped()


if __name__ == "__main__":

    # Params
    input_tst = sys.argv[1]
    output_tst = sys.argv[2]

    # Do we want to disable failing tests?
    disable_failures = bool(int(sys.argv[3]))

    # We are currently guessing the env name (TODO: fix this)
    env_name = os.path.splitext(glob.glob("*.env")[0])[0]

    # Run it
    StripFailures(
        env_name, input_tst, output_tst, disable_failures=disable_failures
    ).main()

# EOF
