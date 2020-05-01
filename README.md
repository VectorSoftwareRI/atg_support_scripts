# ATG support scripts

## Overview

This project collects together a set of Python scripts that are (predominately) designed for deploying VectorCAST/ATG inside of a _server workflow_ (e.g., as part of a continuous integration system such as Jenkins).

**Importantly** if you are an 'end-user' of VectorCAST/ATG these examples are likely not to be relevant to you. VectorCAST's ATG technology can be used directly from either the VectorCAST/GUI or via `clicast`:

```bash
$VECTORCAST_DIR/clicast -lc -e <env> [-u <unit> [-s <sub>]] TOols AUTO_Atg_test_generation <outputfile>
```

If you require help or assistance with using VectorCAST or VectorCAST/ATG, we recommend you [contact Vector's support](mailto:support@vector.com).

### Prerequisites

These demos have been prepared using [CentOS 8](https://www.centos.org/download/), and using [`gcc 8.3.1`](https://gcc.gnu.org/gcc-8/) and [Python 3.6.8](https://www.python.org/downloads/release/python-368/).

Prior to starting, we recommend you execute the dependency checker to ensure that your prerequisites match:

```bash
# Run the dependency checker
./check_deps.sh
```

### Setup

To allow a user to utilise these scripts without requiring direct installation, it is recommended to take advantage of Python's [virtual environments](https://docs.python.org/3/tutorial/venv.html) (`venv`). The dependencies for this project are listed in [`requirements.txt`](requirements.txt).

Installing the required packages can be achieved as follows:

#### Automatic

```bash
# Setup the venv
./setup_venv.sh
```

#### Manual

```bash
# create a new virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Update https://pypi.org/project/pip/
pip3 install -U pip

# Install from our requirements file
pip3 install -r requirements.txt
```

#### Starting 'venv'

Once you have setup your `venv`, it is important that it is 'activated':

```bash
source venv/bin/activate
```

## Creating your own analysis

**For a detailed example on configuring VectorCAST/ATG for a server workflow, we refer to the [VectorCAST/ATG server workflow demos](https://github.com/VectorSoftwareRI/atg_demo).**

### Background

The entry-point for the server workflow is the Python script [`atg_main.py`](atg_main.py). This script has a required argument of `-p` or `--config_py`, to point to the path to a Python configuration script.

It is possible to configure `atg_main.py` to either run *all* environments, or a subset ("incremental mode") based on files that may have changed.

### Examples

To see examples of these configuration scripts, please see:

* [`atg_small_demo_vcast`...`small.py`](https://github.com/VectorSoftwareRI/atg_small_demo_vcast/blob/master/atg_configuration/small.py)

* [`atg_s2n_demo_vcast`...`s2n.py`](https://github.com/VectorSoftwareRI/atg_s2n_demo_vcast/blob/master/atg_configuration/s2n.py)

### Implementing your own configuration script

Your Python configuration script should provide a function:

```python
def get_configuration(options):
```

which returns, at a minimum, a dictionary as follows:

```python
{
    "manage_vcm_path": manage_vcm_path,  # string
    "repository_path": repository_path,  # string
}
```

where:

* `manage_vcm_path` is the path to your VectorCAST/Manage project file (`.vcm`)

* `repository_path` is the path to the root of your source tree

The first argument (`options`) points to the Python [`ConfigArgParse`](https://pypi.org/project/ConfigArgParse) object constructed from the arguments provided to `atg_main.py`.

**Note** as this Python script is executable, you can perform any additional steps you might require to configure your current environment to build your VectorCAST/Manage project (e.g., setting required environment variables).

#### Optional values

The dictionary that you return has some optional values:

```python
{
    "final_tst_path": final_tst_path,               # string
    "find_unchanged_files": find_unchanged_files,   # function returns a set
    "store_updated_tests": store_updated_tests,     # function taking a set
}
```

where:

* `final_tst_path` is an optional path where you wish your created VectorCAST/ATG tests-cases to be stored; by default, these are stored under the VectorCAST/Manage project specified in `"manage_vcm_path"`.

* `find_unchanged_files` is an optional routine, which, when called, returns a set of **unchanged** files (see 'Configuring an incremental analysis')

* `store_updated_tests` is an optional routine that takes a single parameter of a `set` of tests that have been modified; this is, e.g., to support committing these changes files

### Configuring an incremental analysis

#### Example incremental analyses

To see examples of these configuration scripts, please see:

* [`atg_small_demo_vcast`...`small_incremental.py`](https://github.com/VectorSoftwareRI/atg_small_demo_vcast/blob/master/atg_configuration/small_incremental.py)

* [`atg_s2n_demo_vcast`...`s2n_incremental.py`](https://github.com/VectorSoftwareRI/atg_s2n_demo_vcast/blob/master/atg_configuration/s2n_incremental.py)

#### Detecting changes

When utilising VectorCAST/ATG in a server workflow, and to allow for ATG to be run "incrementally" (i.e., only running on a subset of changed environments), your configuration object can contain the element `"find_unchanged_files"`, which returns a set of *unchanged* files.

The simplest implementation could be:

```python
def get_configuration(options):

    repository_path = ...
    manage_vcm_path = ...

    find_unchanged_files = lambda: set()

    return {
        "repository_path": repository_path,
        "manage_vcm_path": manage_vcm_path,
        "find_unchanged_files": find_unchanged_files,
    }

```

That is, this is an analysis that states that there are _no_ **unchanged** files in the source tree. Returning an empty `set` means that all environments would be processed with VectorCAST/ATG.

Conversely, an implementation such as:

```python
def get_configuration(options):

    repository_path = ...
    manage_vcm_path = ...

    all_files = set(
        [os.path.join(dp, f) for dp, dn, fn in os.walk(repository_path) for f in fn]
    )

    find_unchanged_files = lambda: all_files

    return {
        "repository_path": repository_path,
        "manage_vcm_path": manage_vcm_path,
        "find_unchanged_files": find_unchanged_files,
    }

```

would state that _all_ files are **unchanged** and therefore no environments would be processed with VectorCAST/ATG.

