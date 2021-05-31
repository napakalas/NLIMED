import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
    name='NLIMED',
    version='0.0.2',
    author="Yuda Munarko",
    author_email="yuda.munarko@gmail.com",
    description="Natural Language Interface for Model Entity Discovery (NLIMED) is an interface to search model entities in the biosimulation models in repositories. ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/napakalas/NLIMED",
    packages=setuptools.find_packages(),
    # include_package_data = True,
    package_data={
    # If any package contains *.txt files, include them:
    '': ['*.txt'],
    # And include any files found in the 'indexes' package, too:
    '': ['indexes/*'],
    },
    install_requires=[
        'nltk',
        'SPARQLWrapper',
        'pandas',
        'stanza',
        'benepar',
        ],
    entry_points = {
        "console_scripts": [
            "NLIMED = NLIMED.console:runTerminal",
        ]
    },
    classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: GNU General Public License (GPL)",
         "Operating System :: OS Independent",
        ],
    )
