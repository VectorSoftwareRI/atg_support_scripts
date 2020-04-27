import wrapt
import subprocess
import shlex
import os
import multiprocessing
import monotonic
from multiprocessing.dummy import Pool as ThreadPool
from contextlib import contextmanager
import inspect

import logging


log = logging.getLogger("Incremental ATG")

TRUNC_DOTS = "..."
DO_NOT_DECORATE_METHODS = ["__repr__", "__str__", "__init__"]


def str_trunc(text, headsize=16, tailsize=8):
    text = str(text)
    if len(text) > headsize + tailsize + len(TRUNC_DOTS):
        ret = text[:headsize] + TRUNC_DOTS
        if tailsize > 0:
            ret += text[-tailsize:]
    else:
        ret = text
    assert len(ret) <= (headsize + len(TRUNC_DOTS) + tailsize)
    return ret


def get_class_state(instance):
    class_name = instance.__class__.__name__
    if instance:
        instance_state = "(class={:s} state={:s}) ".format(class_name, str(instance))
    else:
        instance_state = ""
    return instance_state


@wrapt.decorator
def log_entry_exit(wrapped, instance, args, kwargs):

    callee_name = wrapped.__name__
    str_args = str([str_trunc(a) for a in args])
    instance_state = get_class_state(instance)

    log.debug(
        "Call: {inst:s}{callee:s} args={args:s}".format(
            inst=instance_state, callee=callee_name, args=str_args
        )
    )

    result = wrapped(*args, **kwargs)

    str_result = str_trunc(result)
    instance_state = get_class_state(instance)

    log.debug(
        "Return: {inst:s}{callee:s} ret={result:s}".format(
            inst=instance_state, callee=callee_name, result=str_result
        )
    )

    return result


def for_all_methods(decorator):
    """
    Class decorator
    """

    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)) and attr not in DO_NOT_DECORATE_METHODS:
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls

    return decorate


@log_entry_exit
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


@log_entry_exit
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


@for_all_methods(log_entry_exit)
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
