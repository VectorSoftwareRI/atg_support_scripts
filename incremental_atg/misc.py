import wrapt
import subprocess
import shlex

@wrapt.decorator
def log_entry_exit(wrapped, instance, args, kwargs):
    print("Enter {:s} ...".format(wrapped.__name__), flush=True, end=" ")
    result = wrapped(*args, **kwargs)
    print("Done!", flush=True)
    return result

def parse_git_for_hashes(repo="."):
    # Hack to calculate the current and previous git hash
    cmd = shlex.split("git log --pretty=oneline --abbrev-commit")
    p = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=repo
    )
    output, err = p.communicate()
    lines = output.splitlines()
    assert len(lines) > 1

    # Bytes-like object!
    branch_sha = str(str(lines[0]).split(" ")[0])[2:]
    head_sha = str(str(lines[1]).split(" ")[0])[2:]

    return (head_sha, branch_sha)


# EOF
