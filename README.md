# ATG support scripts

This project collects together a set of Python scripts that are (predominately) designed for deploying VectorCAST/ATG inside of a _server workflow_ (e.g., as part of a continuous integration system such as Jenkins).

**Importantly** if you are an 'end-user' of VectorCAST/ATG these examples are likely not to be relevant to you. VectorCAST's ATG technology can be used directly from either the VectorCAST/GUI or via `clicast`:

```bash
$VECTORCAST_DIR/clicast -lc -e <env> [-u <unit> [-s <sub>]] TOols AUTO_Atg_test_generation <outputfile>
```

If you require help or assistance with using VectorCAST or VectorCAST/ATG, we recommend you [contact Vector's support](mailto:support@vector.com).

## Prerequisites

These demos have been prepared using [CentOS 8](https://www.centos.org/download/), and using [`gcc 8.3.1`](https://gcc.gnu.org/gcc-8/) and [Python 3.6.8](https://www.python.org/downloads/release/python-368/).

Prior to starting, we recommend you execute the dependency checker to ensure that your prerequisites match:

```bash
# Run the dependency checker
./check_deps.sh
```

## Setup

To allow a user to utilise these scripts without requiring direct installation, it is recommended to take advantage of Python's [virtual environments](https://docs.python.org/3/tutorial/venv.html) (`venv`). The dependencies for this project are listed in [`requirements.txt`](requirements.txt).

Installing the required packages can be achieved as follows:

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

