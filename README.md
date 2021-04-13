
# Cprep - preparing contests made easy

Cprep is a project inspired by Codeforces Polygon, that aims 
to provide an open-source extensible alternative to programming contest creation.


## Installation

##### Via pip (recommended)
- Run `pip3 install cprep`

##### Via source code
- Clone the repository
- Run `pip3 install .`


## How to use

<img src="https://user-images.githubusercontent.com/8794929/112736706-5ffbcc80-8f5d-11eb-8c3e-7986852da21f.gif" width="640" />


##### Create a problem
To create a problem, go to some folder and type `cprep create [PROBLEM_NAME]`. 

##### Generate tests
To generate tests, you have to write one or more generators, and modify the `tests.sh` script to generate each test. You can also optionally include validators. To generate the actual tests, you can use the command `cprep generate`.

##### Evaluate tests
To evaluate the solutions without (re-)generating test cases by using `cprep evaluate`. This will show a table with results of all the submissions. You can optionally specify which submissions to evaluate.

##### Run-all
You can also opt to run all of the above steps in order by typing `cprep runall`. 


_Note: You can always check the available options by running `cprep --help`, and even `cprep [COMMAND] --help`. All of the above commands will require you to have testutil added to your PATH._

