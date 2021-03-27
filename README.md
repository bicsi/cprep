
# Testutil - preparing contests made easy

Testutil is a project inspired by Codeforces Polygon,
that aims to provide an open-source extensible alternative to programming contest creation.


## Installation

- Clone or download the repository
- Run `pip3 install -r requirements.txt`
- Add `testutil` folder to PATH


## How to use

<img src="https://user-images.githubusercontent.com/8794929/112736706-5ffbcc80-8f5d-11eb-8c3e-7986852da21f.gif" width="640" />


To create a problem, go to some folder and type `testutil create [PROBLEM_NAME]`. To build tests for a problem, make sure you are inside the folder and type `testutil make`. You can also evaluate the solutions without (re-)generating test cases by using `testutil eval`. 

You can always check the available options by running `testutil --help`

_Note: Both of the above commands will require you to have testutil added to your PATH._

