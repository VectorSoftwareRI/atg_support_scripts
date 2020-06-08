#!/usr/bin/env python3

import os
import json
import operator
import collections
import tqdm
import re


ALT_EXC_PREFIX = "## --- "
EXC_PREFIX = "## "
EXC_ARROW = "==>"


def find_files_with_ext(dirpath, extension):
    """
    Generator finding all the .tst files
    """
    all_files = set()
    for root, dirs, files in os.walk(dirpath):
        for f in files:
            if f.endswith(extension):
                all_files.add(os.path.join(root, f))
    return all_files


last_line_re = re.compile(r"^## [A-z_]*:")


class LineSanitiser:

    ACTIONS = {
        "Region size exceeds limit": "remove_region_name",
        "Cannot generate value line for": "remove_after_second_arrow",
        "Cannot get offset for field which is not relevant": "remove_after_second_arrow",
        "Expecting a fieldpath ending with function pointer": "remove_after_second_arrow",
        "Function pointer has no candidate function mapping": "remove_after_second_arrow",
        "Non-NULL pointer const used": "remove_after_second_arrow",
        "Trying to overwrite the value": "remove_after_second_arrow",
        "Unable to find a VCAST user global": "remove_after_second_arrow",
        "Unable to get allocation const": "remove_after_second_arrow",
        "Missing memory region": "remove_after_second_arrow",
        "Trying to overwrite the value": "sanitise_invalid_test_value_line",
        "Invalid TEST.VALUE line": "sanitise_invalid_test_value_line",
        "Needs-Alloc handling crashed": "remove_after_second_arrow",
    }

    def __init__(self, line):
        self.line = line

    def proc(self):

        for action_trigger, action_name in LineSanitiser.ACTIONS.items():
            if action_trigger in self.line:
                try:
                    action_method = getattr(self, action_name)
                except AttributeError as e:
                    raise RuntimeError(
                        "Action not handled/installed: {:s}".format(str(e))
                    )

                action_method()

        return self.line

    def remove_region_name(self):
        try:
            left, right = self.line.split("region=", 1)
            right = right.split(" ", 1)[1]
            self.line = left + right
        except Exception:
            # if failed, fallback to remove_after_second_arrow
            self.remove_after_second_arrow()

    def remove_after_second_arrow(self):
        if EXC_ARROW not in self.line:
            return
        split_line = self.line.split(EXC_ARROW)
        if len(split_line) == 3:
            new_line = EXC_ARROW.join(split_line[:2])
            self.line = new_line

    def sanitise_invalid_test_value_line(self):
        self.remove_after_second_arrow()
        try:
            left, right = self.line.split(EXC_ARROW, 1)
            right = right.split("value: ", 1)[1]
            right = right[:-1]  # remove ")"
        except Exception:
            return
        self.line = left + right


class ExceptionData:
    def __init__(self):
        self.lines = []
        self._last_line = None

    def add_line(self, line):
        self.lines.append(line.strip())

    @property
    def last_line(self):
        if not self._last_line:
            last_line = self.lines[-1]
            if not re.match(last_line_re, last_line):
                # remove the current last line
                self.lines = self.lines[:-2]

                # Get the _new_ last line
                last_line = self.lines[-1]
            self._last_line = last_line

        return self._last_line

    def sanitise(self):
        last_line = self.last_line
        sanitisation_needed = False

        line_sanitiser = LineSanitiser(last_line)
        sanitised_line = line_sanitiser.proc()
        if sanitised_line != last_line:
            self.replace_last_line(sanitised_line)

    def replace_last_line(self, new_line):
        self.lines.pop()
        self.lines.append(new_line)
        self._last_line = None

    def __str__(self):
        return "\n".join(self.lines)

    def key_data(self):
        return str(self)


class TstLine:
    @staticmethod
    def is_exception_start(line):
        return EXC_PREFIX in line and "Traceback" in line

    @staticmethod
    def is_exception_line(line):
        return EXC_PREFIX in line

    @staticmethod
    def normalise(line):
        line = line.strip()
        if EXC_PREFIX in line and line.startswith(ALT_EXC_PREFIX):
            line = EXC_PREFIX + line[len(ALT_EXC_PREFIX) :]
        return line


class TstStats:
    def __init__(self, root_dir=None):
        if root_dir is None:
            self.root_dir = "."
        else:
            self.root_dir = root_dir

        self.exception_counts = {}

    def run(self):
        self.process_all_tst_files()

    def process_all_tst_files(self):

        tst_files = find_files_with_ext(".", ".tst")

        with tqdm.tqdm(total=len(tst_files)) as pbar:
            for tst_path in tst_files:
                self.process_tst_file(tst_path)
                pbar.update(1)

    def save_exception(self, exception_data):
        exception_data.sanitise()
        exception_key = exception_data.key_data()
        self.exception_counts.setdefault(exception_key, 0)
        self.exception_counts[exception_key] += 1

    def save_current_exception(self):
        if self.current_exception is not None:
            self.save_exception(self.current_exception)
            self.current_exception = None

    def process_tst_file(self, tst_path):

        ex_open = False
        self.current_exception = None

        for line in open(tst_path):

            line = TstLine.normalise(line)

            #
            # If there is no exception marker, then
            # there is nothing to process
            #
            if not TstLine.is_exception_line(line):
                if ex_open:
                    self.save_current_exception()
                    ex_open = False
                continue

            if TstLine.is_exception_start(line):
                self.save_current_exception()
                self.current_exception = ExceptionData()
                ex_open = True

            if ex_open:
                self.current_exception.add_line(line)

        if ex_open:
            self.save_current_exception()

    def _sort_counts(self):
        # Sort based on the counts
        self.exception_counts = collections.OrderedDict(
            sorted(
                self.exception_counts.items(), key=operator.itemgetter(1), reverse=True
            )
        )

    def print_exceptions(self):

        for exception, count in self.exception_counts.items():
            print()
            print(count)
            print(exception)

    def save_json(self):
        with open("exceptions.json", "w") as f:
            json.dump(self.exception_counts, f)

    def save_txt(self):
        with open("exceptions.txt", "w") as f:
            for exception, count in self.exception_counts.items():
                f.write("=" * 20 + "\n")
                f.write(str(count) + "\n")
                f.write(exception + "\n")
                f.write("=" * 20 + "\n")


def main():
    """
    MAIN
    """
    tst_stats = TstStats()
    tst_stats.run()

    tst_stats._sort_counts()

    # tst_stats.print_exceptions()
    # tst_stats.save_json()
    tst_stats.save_txt()


if __name__ == "__main__":
    main()

# EOF
