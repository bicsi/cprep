
# Cprep - preparing contests made easy

Cprep is a project inspired by Codeforces Polygon, that aims 
to provide an open-source extensible alternative to programming contest creation.


## Installation

#### Via pip (recommended)
- Run `pip3 install cprep`

#### Via source code
- Clone the repository
- Run `pip3 install .`


## How to use

<img src="https://user-images.githubusercontent.com/8794929/112736706-5ffbcc80-8f5d-11eb-8c3e-7986852da21f.gif" width="640" />


#### Create a problem
To create a problem, go to some folder and type `cprep create [PROBLEM_NAME]`. 

This will create a folder with the name you provided, as well as some files inside that folder to get you started.

#### Generate tests
To generate tests, you have to write one or more generators, and modify the `tests.sh` script to generate each test. You can also optionally include validators. 

To generate the actual tests, you can use the command `cprep generate`.

#### Evaluate tests
To evaluate the solutions without (re-)generating test cases by using `cprep evaluate`. This will show a table with results of all the submissions. 

You can optionally specify which submissions to evaluate.

#### Run-all
You can also opt to run all of the above steps in order by typing `cprep runall`. 


_Note: You can always check the available options by running `cprep --help`, and even `cprep [COMMAND] --help`._


## Configuration

When running the tool, there will always be a configuration dictating how the process will happen. It can be printed by using `cprep config`. 

_Note: The configuration printed by the above command may depend on the directory you are in._

#### Global configuration

In order to modify
any of the global configuration values, you can add a file
called `.cprep.yaml` in your home directory, where you can 
override any of the defaults.

For example, if you want to use a different C++ compiler, you can save:
```yaml
compilation:
  languages:
    C++:
      compile: "g++ -O0 {src_path} -o {exec_path}"
```
to destination path `~/.cprep.yaml`.

#### Local configuration 

For local-level (per problem) configuration, edit the `config.yaml` file inside the problem directory (created by running `cprep create [NAME]`). This will override the global configuration, when running the tool from inside the problem folder (it will not affect other problems, though). 

This is generally useful for modifying problem-level details like time limit, input/output files, as well as test name structure.


**IMPORTANT: This project is still in early stages of development, therefore the config structure is always subject to change.**


