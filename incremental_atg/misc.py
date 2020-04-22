import wrapt

@wrapt.decorator
def log_entry_exit(wrapped, instance, args, kwargs):
    print("Enter {:s} ...".format(wrapped.__name__), flush=True, end=" ")
    result = wrapped(*args, **kwargs)
    print("Done!", flush=True)
    return result

# EOF
