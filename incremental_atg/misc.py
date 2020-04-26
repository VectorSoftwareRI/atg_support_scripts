import wrapt
import subprocess
import shlex
import os
import multiprocessing
import monotonic
from multiprocessing.dummy import Pool as ThreadPool
from contextlib import contextmanager


@wrapt.decorator
def log_entry_exit(wrapped, _, args, kwargs):
    # print("Enter {:s} ...".format(wrapped.__name__), flush=True, end=" ")
    result = wrapped(*args, **kwargs)
    # print("Done!", flush=True)
    return result


def parse_git_for_hashes(repo="."):
    # Hack to calculate the current and previous git hash
    cmd = shlex.split("git log --pretty=oneline --abbrev-commit")
    output, _, _ = run_cmd(cmd, cwd=repo, shell=False)
    lines = output.splitlines()
    assert len(lines) > 1

    # Bytes-like object!
    branch_sha = lines[0].split(" ")[0]
    head_sha = lines[1].split(" ")[0]

    return (head_sha, branch_sha)


def run_cmd(cmd, cwd, environ=None, timeout=None, log_file_prefix=None, shell=True):

    if not environ:
        environ = os.environ.copy()

    # What options to do we want to pass to subprocess?
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": shell,
        "universal_newlines": True,
        "cwd": cwd,
        "env": environ,
    }

    # Start a timer
    start = monotonic.monotonic()

    # Start the process
    with subprocess.Popen(cmd, **kwargs) as process:
        try:
            # Communicate with timeout
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            # If our timeout expires ...

            # Kill the process
            process.kill()

            # Grab the output
            stdout, stderr = process.communicate()

    # End the clock
    end = monotonic.monotonic()

    # Calculate the duration
    elapsed_time = end - start

    if log_file_prefix:
        out_log_file = "{prefix}.out".format(prefix=log_file_prefix)
        err_log_file = "{prefix}.err".format(prefix=log_file_prefix)

        modified_stdout = stdout

        # Write the duration to the log
        modified_stdout += "\nElapsed seconds: {:.2f}\n".format(elapsed_time)

        # What's the return code?
        returncode = process.returncode

        # Write the return code to the log
        modified_stdout += "\nReturn code: {retcode}\n".format(retcode=returncode)

        with open(out_log_file, "w") as output_fd:
            output_fd.write(modified_stdout)

        with open(err_log_file, "w") as err_fd:
            err_fd.write(stderr)

    return stdout, stderr, process.returncode


def wrap_class_method(args):
    """
    You cannot pass a class method into pool.map -- so we use a helper function
    to call our really class method
    """
    func, args = args
    func(*args)


class ParallelExecutor(object):
    """
    Helper class that makes it easy to write other classes that can do things
    in parallel
    """

    def __init__(self):
        # When running in parallel, how many workers?
        self.worker_count = multiprocessing.cpu_count()

        # Mutex to allow for threads to update class state
        self.mutex = multiprocessing.Lock()

    def run_routine_parallel(self, routine, routine_contexts):
        """
        Given a routine and routine context, builds-up what is neccessary to
        call the routine via a parallel pool
        """

        #
        # What's the 'execution context' for subprocess?
        #
        # We acutally call 'wrap_class_method', which 'unboxes' routine and
        # calls that
        #
        execution_contexts = []
        for routine_context in routine_contexts:
            execution_contexts.append([routine] + [list(routine_context)])

        # Worker pooler
        pool = ThreadPool(self.worker_count)

        # Run the call method in parallel over the 'context'
        pool.map(wrap_class_method, execution_contexts, chunksize=1)

        # Wait for all the workers
        pool.close()

        # Join all workers
        pool.join()

    @contextmanager
    def update_shared_state(self):
        self.mutex.acquire()
        try:
            yield
        finally:
            self.mutex.release()


# EOF
