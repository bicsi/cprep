from setuptools import setup

with open("requirements.txt", "r") as f:
    install_requires = list(map(str.rstrip, f.read().splitlines()))

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name='cprep',
    version='0.1.0',    
    description='Preparing contests made easy',
    long_description=long_description,
    url='https://github.com/bicsi/testutil',
    author='Stephen Hudson',
    author_email='bicsi@ymail.com',
    license='GNU General Public License',
    install_requires=install_requires,
    packages=['cprep', 'cprep_cli', 'cprep_cli.commands'],
    classifiers=[
        'Development Status :: 1 - Planning',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 3',
    ],
    python_requires=">=3.6",
    entry_points=dict(
        console_scripts=['cprep=cprep_cli.__main__:main'],
    ),
    package_data={
      'cprep_cli': ['*.yaml', 'skel/*.*']
    }
)