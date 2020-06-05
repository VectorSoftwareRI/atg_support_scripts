#!/usr/bin/env python3

import os
import json
import operator
import collections
import tqdm


ALT_EXC_PREFIX = "## --- "
EXC_PREFIX = "## "
EXC_ARROW = "==>"

# DUMP_ARROW_EXCEPTIONS = [ "Trying to overwrite the value when overwrite isn't enabled", "Needs-Alloc handling crashed", "Region size exceeds limit", "Non-NULL pointer const used" ]
DUMP_ARROW_EXCEPTIONS = []


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


class ExceptionData:
    def __init__(self):
        self.lines = []

    def add_line(self, line):
        self.lines.append(line.strip())

    def get_last_line(self):
        return self.lines[-1]

    def sanitise_second_arrow(self):
        """
        Dumps anything after the second ==>
        """
        last_line = self.get_last_line()
        if EXC_ARROW not in last_line:
            return
        split_line = last_line.split(EXC_ARROW)
        if len(split_line) == 3:
            new_line = EXC_ARROW.join(split_line[:2])
            self.replace_last_line(new_line)

    def sanitise_dump_after(self):
        """
        Dumps everything after ==> when the line contains
        something from the DUMP_ARROW_EXCEPTIONS list
        """
        last_line = self.get_last_line()
        sanitisation_needed = False

        for text in DUMP_ARROW_EXCEPTIONS:
            if text in last_line:
                sanitisation_needed = True
                break

        if sanitisation_needed:
            split_line = last_line.split(EXC_ARROW)
            new_line = split_line[0]
            self.replace_last_line(new_line)

    def sanitise(self):
        self.sanitise_second_arrow()
        self.sanitise_dump_after()

    def replace_last_line(self, new_line):
        self.lines.pop()
        self.lines.append(new_line)

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
