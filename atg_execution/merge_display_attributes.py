from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
)

import sys
from collections import OrderedDict

import atg_execution.misc as atg_misc


@atg_misc.for_all_methods(atg_misc.log_entry_exit)
class MergeDisplayAttributes(object):
    def __init__(self, src_tst, dest_tst, output_tst):
        # What's the tst we want to take attributes from?
        self.src_tst = src_tst

        # Where do we want to put the attributes?
        self.dest_tst = dest_tst

        # Where do we want to write them to?
        self.output_tst = output_tst

        # Read the src lines
        self.src_lines = open(self.src_tst).readlines()

        # Read the dest lines
        self.dest_lines = open(self.dest_tst).readlines()

        # The extracted attributes
        self.src_attributes = OrderedDict()

    def __repr__(self):
        return str({"src_tst": self.src_tst, "dest_tst": self.dest_tst})

    def extract_attributes(self):
        """
        Extracts the attributes from the src tst file
        """

        # We have no subprogram to start with
        current_sp = None

        # Walk our src tst
        for line in self.src_lines:

            # When we see a subprogram ...
            if line.startswith("TEST.SUBPROGRAM:"):
                #
                # ... extract the name
                #
                # TODO: won't work for C++
                #
                current_sp = line.split(":")[1].strip()

                # If our current subprogram has not yet been seen
                if current_sp not in self.src_attributes:

                    # Set the attributes for this subprogram to an empty set
                    self.src_attributes.update({current_sp: set()})

            elif line.startswith("TEST.ATTRIBUTES:"):

                # If we see attributes, we expect to have a subprogram
                assert current_sp is not None

                #
                # If we see an attribute line, store it for the current
                # subprogram
                #
                self.src_attributes[current_sp].add(line.strip())

    def merge_attributes_to_dest(self):
        """
        Merges our display attributes into the dest tst and writes the output
        """
        with open(self.output_tst, "w") as output:

            # We have no subprogram to start with
            current_sp = None

            # For each line in the destination tst
            for line in self.dest_lines:

                # Find the subprogram
                if line.startswith("TEST.SUBPROGRAM:"):
                    # TODO: won't work for C++
                    current_sp = line.split(":")[1].strip()

                elif line.strip() == "TEST.END":
                    # End of the tst

                    # Current subprogram should not be none
                    assert current_sp is not None

                    try:
                        # Grab the attributes for our subprogram
                        output_attrs = "\n".join(self.src_attributes[current_sp]) + "\n"

                        # Write them out
                        output.write(output_attrs)
                    except KeyError:
                        pass

                # Write the original line
                output.write(line)

    @classmethod
    def merge(cls, baseline_tst, atg_tst, merged_tst):
        m = cls(baseline_tst, atg_tst, merged_tst)
        m.extract_attributes()
        m.merge_attributes_to_dest()


# EOF
