import git
import whatthepatch
import incremental_atg.misc as atg_misc
import os


class ImpactedObjectFinder(object):
    def __init__(self, repository_location, allow_moves):
        self.repository_location = repository_location
        self.allow_moves = allow_moves

    def _calculate_preserved_files(self, current_id, new_id):
        """
        This is what you implement
        """
        raise NotImplementedError()

    @atg_misc.log_entry_exit
    def calculate_preserved_files(self, current_id, new_id):
        """
        Method that is called to obtain the set of files that haven't changed
        between two ids
        """
        ret_val = self._calculate_preserved_files(current_id, new_id)
        assert isinstance(ret_val, set)
        return ret_val


class GitImpactedObjectFinder(ImpactedObjectFinder):
    """
    Class to return the list of file changes for a given repo
    """

    def __init__(self, repository_location, allow_moves):

        # Call the super constructor
        super().__init__(repository_location, allow_moves)

        # Create our git class
        self.repo = git.Repo(repository_location)

    def _find_all_files(self):
        g = git.Git(self.repository_location)
        all_files = {fname.strip() for fname in g.ls_files().split("\n")}
        return all_files

    def _find_changed_files(self, current_id, new_id):
        """
        Calculates the set of _changed_ files!
        """

        # Grab the raw git diff
        diff_text = self.repo.git.diff(current_id, new_id)

        # parse the diff
        parsed_diff = whatthepatch.parse_patch(diff_text)

        # Our changed files
        changed_files = set()

        # Iterate over the diff -- one 'diff' per file
        for diff in parsed_diff:

            # Detect if the file is new or moved
            if diff.header.old_path != diff.header.new_path:

                if not self.allow_moves:
                    raise RuntimeError(
                        "Your commit range contains file moves. Cowardly aborting."
                    )

                git_old_path = diff.header.old_path

                # If the old path is not /dev/null, then ...
                if git_old_path != "/dev/null":
                    # ... file moves start with 'a' (for old) and 'b' for new
                    old_leading_dir = git_old_path.split(os.path.sep, 1)[0]
                    assert old_leading_dir == "a"

                    git_new_path = diff.header.new_path
                    new_leading_dir, new_path = git_new_path.split(os.path.sep, 1)
                    assert new_leading_dir == "b"
                else:
                    # Otherwise, must be a wholly new file
                    new_path = diff.header.new_path

                #
                # TODO: we need to flag to the user that the Manage project
                # needs updating and things _will not work_ because the units
                # have moved
                #

                # Make it clear that this is further refined by interrogating Manage

            else:
                new_path = diff.header.new_path

            # Currently, environments depend on the new files and the old files
            changed_files.add(new_path)

        return changed_files

    def _calculate_preserved_files(self, current_id, new_id):
        """
        Calculates the set of _preserved_ files!
        """

        # Find all the files
        all_files = self._find_all_files()

        # Find the changed files
        changed_files = self._find_changed_files(current_id, new_id)

        # Check that everything in changed is also in all files
        assert changed_files.intersection(all_files) == changed_files

        # Calculate the difference
        unchanged_files = all_files - changed_files

        # Return our set of unchanged files
        return unchanged_files


# EOF
