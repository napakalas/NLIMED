# NLIMED
Natural Language Interface for Model Entity Discovery (NLIMED) is an interface to search model entities (i.e. flux of sodium across the basolateral plasma membrane, the concentration of potassium in the portion of tissue fluid) in the biosimulation models in repositories. The interface utilises the RDF inside biosimulation models and metadata from BioPortal. Currently, the interface can retrieve model entities from the Physiome Model Repository (PMR, https://models.physiomeproject.org) and the BioModels (https://www.ebi.ac.uk/biomodels/).

In general, NLIMED works by converting natural language query into SPARQL, so it may help users by avoiding the rigid syntax of SPARQL, query path consisting multiple predicates, and detail knowledge about ontologies.

Note: model entities extracted from BioModels are those having ontologies indexed by BioPortal.

Reference: https://doi.org/10.1101/756304

## General instruction
1. Download or clone all files in a new folder
2. NLIMED implements Stanford Parser, NLTK Parser, and NCBO parser. You may select one of them for your system.
  * NLTK Parser:
    - Install NLTK, please follow this link: https://www.nltk.org/install.html
  * NCBO parser:
    - You have to get an apikey through [https://bioportal.bioontology.org/help#Getting_an_API_key](https://bioportal.bioontology.org/help#Getting_an_API_key) and setup the apikey in Settings.py file, line 16.``
  ```python
  self.oboAPIKey = 'put your apikey here'
  ```
  * Stanford Parser:
    - Please download jar files of stanford-corenlp and stanford-english-corenlp-models.
    - These files can be downloaded from https://stanfordnlp.github.io/CoreNLP/download.html, as a full zip package. Then extract the zip file to your new folder.
    -  Based on stanford-corenlp version downloaded, you will find a different folder and files' name. For example, in this works, we use stanford-corenlp-full-2018-10-05.zip, so it will create <span style="color:green">stanford-corenlp-full-2018-10-05</span> folder where the stanford-corenlp file is <span style="color:green">stanford-corenlp-3.9.2.jar</span> and the corenlp-models file is <span style="color:green">stanford-english-corenlp-2018-10-05-models.jar</span>. Then, modify QueryAnnotator.py file at line 174, 175, and 176, set these to your downloaded file names. Here are the lines that you should modify:
  ```python
  STANFORD = os.path.join(os.path.abspath("."), "stanford-corenlp-full-2018-10-05")
        coreNLPFile = os.path.join(STANFORD, "stanford-corenlp-3.9.2.jar")
        modelFile = os.path.join(STANFORD, "stanford-english-corenlp-2018-10-05-models.jar")
  ```
    - In some case, running Stanford Parser directly on Windows system may not work. It probably shows a message:

      <span style="color:red">Windows could not start the CoreNLP service on Local Computer. The service did not return an error. This could be an internal Windows error or an internal service error. If the problem persists, contact your system administrator.</span>

      Please refer to https://github.com/stanfordnlp/CoreNLP/issues/435 to overcome this issue.



## Running NLIMED from console (query to get model entities)
NLIMED can be run directly on command prompt or terminal. There are 2 mandatory arguments and 7 optional arguments. To get help about the required arguments, run:
```terminal
$ python NLIMED.py -h
```
then you will get:
```terminal
usage: NLIMED.py [-h] -r {pmr,bm,all} -p {stanford,nltk,ncbo} -q QUERY
                 [-pl PL] [-s {models,sparql,annotation,verbose}] [-a ALPHA]
                 [-b BETA] [-g GAMMA] [-d DELTA]

optional arguments:
  -h, --help            show this help message and exit
  -r {pmr,bm,all}, --repo {pmr,bm,all}
                        repository name
  -p {stanford,nltk,ncbo}, --parser {stanford,nltk,ncbo}
                        parser tool
  -q QUERY, --query QUERY
                        query -- any text containing words
  -pl PL                precision level, >=1
  -s {models,sparql,annotation,verbose}, --show {models,sparql,annotation,verbose}
                        results presentation type
  -a ALPHA, --alpha ALPHA
                        Minimum alpha is 0
  -b BETA, --beta BETA  Minimum beta is 0
  -g GAMMA, --gamma GAMMA
                        Minimum gamma is 0
  -d DELTA, --delta DELTA
                        Minimum delta is 0
```
Here is the description of those arguments:
* -r {pmr,bm,all} or --repo {pmr,bm,all} (mandatory) is the name of repository. pmr is the Physiome Repository Model, bm is BioSimulations, all is for both repositories
* -p {stanford,nltk,ncbo} or --parser {stanford,nltk,ncbo} (mandatory) is the type of parser for query annotation.
* -q QUERY or --query QUERY (mandatory) is the query text. For a multi words query, the words should be double quoted.
* -pl PL (optional) is precision level indicating the number of ontologies used to construct SPARQL. Larger number will utilised more ontologies which may generate more SPARQL and produce more results. Minimum value is 1. Default value is 1.
* -s {models,sparql,annotation,verbose} or --show {models,sparql,annotation,verbose} (optional) is for selecting presented results. models shows models, sparql shows all possible SPARQLs, annotation shows annotation results, and verbore shows annotation results, SPARQLs, and models
* -a ALPHA or --alpha ALPHA (optional) is to set up the weight of preffered label feature. Minimum alpha is 0. Default value is 4.
* -b BETA or --beta BETA (optional) is to set up the weight of synonym feature. Minimum beta is 0. Default value is 0.7.
-g GAMMA or --gamma GAMMA (optional) is to set up the weight of definition feature. Minimum gamma is 0. Default value is 0.5.
-d DELTA, --delta DELTA (optional) is to set up the weight of description feature. Minimum gamma is 0. Default value is 0.8.

### Running example
* running with minimum setup for repository = Physiome Model Repository, parser = NLTK, query = "flux of sodium", and other default arguments values:
  ```
  $ python NLIMED.py -r pmr -p nltk -q "flux of sodium"
  ```
* running with full setup for repository=BioModels, parser=Stanford, query="flux of sodium", precision level = 2, alpha = 2, beta = 1, gamma = 1, and delta = 1
  ```
  $ python NLIMED.py -r bm -p stanford -q "flux of sodium" -pl 2 -a 2 -b 1 -g 1 -d 1
  ```
  Note: running with Stanford parser may cause delay local server setup for the first run. However, for the next run, the delay is disappeared.

* running for repository = Physiome Model Repository, parser = NCBO, query = "flux of sodium", precision level = 3,and other default arguments

  ```
  $ python NLIMED.py -r pmr -p ncbo -q "flux of sodium" -pl 3
  ```
  Note: running with NCBO Parser parser is slower than other parsers because it is using a web service depended on the Internet connection.


## Utilising NLIMED in your Python code

The main class for retrieving model entities from repositories is NLIMED in NLIMED.py. Utilising this class, we can annotate query into ontologies, get all possible SPARQL, and get model entities. We suggest you to create one NLIMED object for all your queries since it will reuse the loaded indexes so it can save your device resources.

### Get Model Entities
* minimum syntax example
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='stanford')
  query = 'flux of sodium'
  result = nlimed.getModels(query=query,format='json')

  """
  where:
  - repo : repository {'pmr','bm'}
  - parser : parser tool {'stanford','nltk','ncbo'}
  - query : query text
  - format : the returning format data {'json','print'}
  """
  ```
* full syntax example
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='stanford', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8)
  query = 'flux of sodium'
  result = nlimed.getModels(query=query,format='json')

  """
  where:
  - repo (mandatory) : repository {'pmr','bm'}
  - parser : parser tool {'stanford','nltk','ncbo'}
  - pl (optional) : precision level, the minimum value is 1
  - alpha (optional) : preffered label weight, the minimum value is 0
  - beta (optional) : synonym weight, the minimum value is 0
  - gamma (optional) : definition weight, the minimum value is 0
  - delta (optional) : description weight, the minimum value is 0
  - query : query text
  - format : the returning format data {'json','print'}
  """
  ```

### Get Query Annotation
* minimum syntax
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='stanford')
  query = 'flux of sodium'
  result = nlimed.getAnnotated(query=query,format='json')
  ```
* full syntax
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='stanford', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8)
  query = 'flux of sodium'
  result = nlimed.getAnnotated(query=query,format='json')
  ```

### Get SPARQL
* minimum syntax
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='stanford')
  query = 'flux of sodium'
  result = nlimed.getSparql(query=query,format='json')
  ```
* full syntax
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='stanford', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8)
  query = 'flux of sodium'
  result = nlimed.getSparql(query=query,format='json')
  ```

## Recreate Indexes (RDF Graph Index and Text Feature Index)

All indexes are already provided in this project. However, if you want to recreate all indexes you can use the following script on console. Please be patient, since it may take times to be finished.

### Indexing the pmr

```
$ python Indexer.py -r pmr
```

### Indexing biomodels

```
$ python Indexer.py -r bm
```
