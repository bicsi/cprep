#include <iostream>

using namespace std;

int main(int argc, char** argv) {
  int v = stoi(argv[1]);
  int a = rand() % v; 
  int b = rand() % v; 
  cout << a << " " << b << endl;
}