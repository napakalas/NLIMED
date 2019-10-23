# NLIMED
Natural Language Interface for Model Entity Discovery (NLIMED) is an interface to search model entities (i.e. flux of sodium across the basolateral plasma membrane, the concentration of potassium in the portion of tissue fluid) in the biosimulation models in repositories. The interface utilises the RDF inside biosimulation models and metadata from BioPortal. Currently, the interface can retrieve model entities from the Physiome Model Repository (PMR, https://models.physiomeproject.org) and the BioModels (https://www.ebi.ac.uk/biomodels/).

In general, NLIMED works by converting natural language query into SPARQL, so it may help users by avoiding the rigid syntax of SPARQL, query path consisting multiple predicates, and detail knowledge about ontologies.

Note: model entities extracted from BioModels are those having ontologies indexed by BioPortal.

License :: OSI Approved :: GNU General Public License (GPL)

## References
The main reference of this work is: https://doi.org/10.1101/756304

Cite the following works when you implement NLIMED with parser of:
1. CoreNLP: https://stanfordnlp.github.io/CoreNLP/citing.html
2. NLTK: https://arxiv.org/abs/cs/0205028
3. NCBO: https://www.ncbi.nlm.nih.gov/pubmed/21347171

## Installation
We sugest you to install NLIMED from PyPI. If you already installed [pip](https://pip.pypa.io/en/stable/installing/), run the following command:
  ```
  pip install NLIMED
  ```
This installation will also resolve nltk dependency.
In a case you already have old NLIMED installation, you may update it use:
  ```
  pip install NLIMED -U
  ```
As an alternative, you can clone and download this github repository and use the following command:
  ```
  git clone https://github.com/napakalas/NLIMED.git
  cd NLIMED
  pip install -e .
  ```

## Configuration

NLIMED implements Stanford Parser, NLTK Parser, and NCBO parser. You may select one of them for your system.
  * NLTK Parser:
    - NLTK is automatically deploy as a dependency.
  * NCBO parser:
    - You have to get a [bioportal](https://bioportal.bioontology.org/help#Getting_an_API_key) apikey  and run the NLIMED config command.

  * Stanford Parser:
    - Download the [CoreNLP](https://stanfordnlp.github.io/CoreNLP/download.html) zip file and then extract it on your deployment folder.

    - Based on stanford-corenlp version downloaded, you will find a different zip file and extracted folder names. For example, in this works, we get:
      - a zip file : stanford-corenlp-full-2018-10-05.zip
      - a folder   : stanford-corenlp-full-2018-10-05

  * **Configuring Stanford and NCBO parsers**
    If you intent to implement NLTK only, you don't need to configure. NLIMED configuration is needed for Stanford and NCBO parsers.
    - Configuration using command prompt or terminal, use this syntax:

      ```
      NLIMED --config --apikey {your-ncbo-api-key} --corenlp-home {CoreNLP-folder-full-path}
      ```
      As an example if your NCBO apikey is "fc5d5241-1e8e-4b44-b401-310ca39573f6" and your CoreNLP folder is "/path/stanford-corenlp-full-2018-10-05/", the call will be:
      ```
      NLIMED --config --apikey "fc5d5241-1e8e-4b44-b401-310ca39573f6" --corenlp-home "/Users/user1/Documents/Stanford NLP/stanford-corenlp-full-2018-10-05/"
      ```
    - Configuration usin python code, example:

      ```python
      from NLIMED import config
      config(apikey='fc5d5241-1e8e-4b44-b401-310ca39573f6', corenlp_home='/Users/user1/Documents/Stanford NLP/stanford-corenlp-full-2018-10-05/')
      ```
      Show configuration:
      ```python
      from NLIMED import getConfig
      getConfig()
      ```

## Issues

1. When using Stanford parser, you may find the following error message:

    ```
    ...
    requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=9000): Max retries exceeded with url: /?properties=%7B%22outputFormat%22%3A+%22json%22%2C+%22annotators%22%3A+%22tokenize%2Cpos%2Clemma%2Cssplit%2Cparse%22%2C+%22ssplit.eolonly%22%3A+%22true%22%2C+%22tokenize.whitespace%22%3A+%22false%22%7D (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x00000215465682B0>: Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it'))
    ```
    The possible cause is:
    - You are not properly configure CoreNLP folder. Please recheck the correct location and then rerun the configuration command.
    - In some devices, CoreNLP local web services is slowly started, so it is not ready when utise by NLIMED. You can wait for a minute then rerun your command or code.

    Alternative solution solution:
    You may also start the services manually on command line or terminal. Go to your CoreNLP folder and run:
    ```
    java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 -timeout 15000
    ```
    Then check the services availability on your web browser through link: http://localhost:9000/

2. Any other issues please follow [issues](https://github.com/napakalas/NLIMED/issues).

## Experiment
We conducted an experiment to measure NLIMED performance in term of:
1. precision, recall and F-Measure
2. comparison to NCBO Annotator, and
3. features contribution

You can get the [experiment](https://github.com/napakalas/NLIMED/tree/master/experiment) code and DataTest from this repository. Run the code using Jupyter Notebook.

## How NLIMED works?
Here is the process inside NLIMED converting natural language query (NLQ) and SPARQL and then retrieving model entities from biomodel repositories:
1. NLQ Annotation -- Annotating NLQ to ontologies
  - NLQ is parsed using selected parser (Stanford, NLTK, or NCBO), resulting candidate noun phrases (CNPs).
  - Measuring association level of each CNP to ontologies. The measurement utilises four type of textual features, i.e. preferred label, synonym, description, and local definition by this formula:

    ![Image](https://raw.githubusercontent.com/napakalas/NLIMED/master/resource/Eq-NLIMED.gif?raw=true)

    where:
    - <code>p<sub>i</sub>, s<sub>i</sub>, and d<sub>i</sub></code> are the present (1) or the absent (0) of term in preffered label, synonym, and definition consecutively.
    - <code>f<sub>i</sub></code> is the number of term in description.
    - <code>lp<sub>i</sub>, ls<sub>i</sub>, ld<sub>i</sub>, and lf<sub>i</sub></code> are the number of terms in preffered label, synonym, definition, and description consecutively.
    - <code>nt</code> is the number of terms in a phrase
    - <code>N</code> is the number of ontologies having the term
    - <code>S</code> is the number of model entities in the collection.
    - <code>ts<sub>i</sub></code> is the number of model entities having the term
    - <code>&alpha;, &beta;, &gamma;, and &delta;</code> are multipliers to set the features importance level. The multipliers values are decided empirically based on the repositories.

  - Select CNPs with highest association, having longest term, and not overlapping with other CNP. The selected CNPs should cover all terms in NLQ.
  - Select the top pl of ontologies from selected CNPs
  - Combine all possible ontologies with no overlapping CNPs
2. SPARQL Generation
  - Construct SPARQLs for each ontotology combinations
3. Retrieve model entities by sending each SPARQLs to model repository SPARQL endpoints.

## Running NLIMED from console (query to get model entities)
NLIMED can be run directly on command prompt or terminal. There are 2 mandatory arguments and 7 optional arguments. To get help about the required arguments, run:
```terminal
NLIMED -h
```
then you will get:
```terminal
usage: NLIMED [-h] -r {pmr,bm,all} -p {stanford,nltk,ncbo} -q QUERY
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
  NLIMED -r pmr -p nltk -q "flux of sodium"
  ```
* running with full setup for repository=BioModels, parser=Stanford, query="flux of sodium", precision level = 2, alpha = 2, beta = 1, gamma = 1, and delta = 1
  ```
  NLIMED -r bm -p stanford -q "flux of sodium" -pl 2 -a 2 -b 1 -g 1 -d 1
  ```
  Note: running with Stanford parser may cause delay local server startup for the first run. However, for the next run, the delay is disappeared.

* running for repository = Physiome Model Repository, parser = NCBO, query = "flux of sodium", precision level = 3,and other default arguments

  ```
  NLIMED -r pmr -p ncbo -q "flux of sodium" -pl 3
  ```
  Note: running with NCBO Parser parser is slower than other parsers because it is using a web service depended on the Internet connection.


## Utilising NLIMED in your Python code

The main class for retrieving model entities from repositories is NLIMED in NLIMED.py. Utilising this class, we can annotate query into ontologies, get all possible SPARQL, and get model entities. We suggest you to create one NLIMED object for all your queries since it will reuse the loaded indexes so it can save your device resources.

### Get Model Entities
The following codes are used to retrieve model entities from the PMR or Biomodels.
* Returning model entities from the PMR using Stanford parser with standard setting for query: "mitochondrial calcium ion transmembrane transport"
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='stanford')
  query = 'mitochondrial calcium ion transmembrane transport'
  result = nlimed.getModels(query=query,format='json')

  """
  where:
  - repo : repository {'pmr','bm'}
  - parser : parser tool {'stanford','nltk','ncbo'}
  - query : query text
  - format : the returning format data {'json','print'}
  """
  ```
  The code resulting a json format data consisting 27 model entities related to the query
  ```
  {
    'vars': ['graph', 'Model_entity', 'desc'],
    'results': [{
      'graph': 'https://models.physiomeproject.org/workspace/colegrove_albrecht_friel_2000',
      'Model_entity': 'colegrove_albrecht_friel_2000.cellml#id_00011'
    },
      ....
    , {
      'graph': 'https://models.physiomeproject.org/workspace/marhl_haberichter_brumen_heinrich_2000',
      'Model_entity': 'marhl_haberichter_brumen_heinrich_2000.cellml#id_000000025'
    },
      ...
    ]
  }
  ```

* It also possible to increase the precision level, so NLIMED can show more results. Here we are returning model entities from the PMR using Stanford parser and precision level 2, alpha=4, beta=0.7, gamma=0.5, delta=0.8.
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='stanford', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8)
  query = 'mitochondrial calcium ion transmembrane transport'
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
  The code resulting a json format data consisting 141 model entities related to the query
  ```
  {
    'vars': ['graph', 'Model_entity', 'desc'],
    'results': [{
      'graph': 'https://models.physiomeproject.org/workspace/colegrove_albrecht_friel_2000',
      'Model_entity': 'colegrove_albrecht_friel_2000.cellml#id_00011'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/marhl_haberichter_brumen_heinrich_2000',
      'Model_entity': 'marhl_haberichter_brumen_heinrich_2000.cellml#id_000000025'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/winslow_rice_jafri_marban_ororke_1999',
      'Model_entity': 'winslow_rice_jafri_marban_ororke_1999.cellml#sarcolemmal_calcium_pump_i_p_Ca'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/michailova_mcculloch_2001',
      'Model_entity': 'michailova_mcculloch_2001.cellml#id_00118'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/hinch_greenstein_tanskanen_xu_winslow_2004',
      'Model_entity': 'hinch_greenstein_tanskanen_xu_winslow_2004.cellml#id_00038'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/w/andre/SAN-ORd',
      'Model_entity': 'Ohara_Rudy_2011.cellml#id_00011'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/bertram_satin_zhang_smolen_sherman_2004',
      'Model_entity': 'bertram_satin_zhang_smolen_sherman_2004_a.cellml#calcium_handling_Jserca'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/bertram_sherman_2004',
      'Model_entity': 'bertram_sherman_2004.cellml#id_00029'
    }, {
      'graph': 'https://models.physiomeproject.org/workspace/noble_2000',
      'Model_entity': 'noble_2000_a.cellml#id_00024'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/bindschadler_sneyd_2001',
      'Model_entity': 'bindschadler_sneyd_2001.cellml#id_00003'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/fridlyand_tamarina_philipson_2003',
      'Model_entity': 'fridlyand_tamarina_philipson_2003.cellml#id_00025'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/puglisi_bers_2001',
      'Model_entity': 'puglisi_bers_2001.cellml#id_00112'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/terkildsen_niederer_crampin_hunter_smith_2008',
      'Model_entity': 'Hinch_et_al_2004.cellml#id_00010'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/55c',
      'Model_entity': 'Hinch_et_al_2004.cellml#id_00010'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/luo_rudy_1994',
      'Model_entity': 'luo_rudy_1994.cellml#id_00019'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/viswanathan_shaw_rudy_1999',
      'Model_entity': 'viswanathan_shaw_rudy_1999_a.cellml#sarcolemmal_calcium_pump_i_p_Ca'
    }, {
      'graph': 'https://models.physiomeproject.org/workspace/viswanathan_shaw_rudy_1999',
      'Model_entity': 'viswanathan_shaw_rudy_1999_a.cellml#id_00078'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/goforth_bertram_khan_zhang_sherman_satin_2002',
      'Model_entity': 'goforth_bertram_khan_zhang_sherman_satin_2002.cellml#id_00041'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/albrecht_colegrove_friel_2002',
      'Model_entity': 'albrecht_colegrove_friel_2002.cellml#id_00030'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/marhl_haberichter_brumen_heinrich_2000',
      'Model_entity': 'marhl_haberichter_brumen_heinrich_2000.cellml#id_000000019'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/albrecht_colegrove_hongpaisan_pivovarova_andrews_friel_2001',
      'Model_entity': 'albrecht_colegrove_hongpaisan_pivovarova_andrews_friel_2001.cellml#id_00021'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/riemer_sobie_tung_1998',
      'Model_entity': 'riemer_sobie_tung_1998.cellml#id_00063'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/faber_rudy_2000',
      'Model_entity': 'faber_rudy_2000.cellml#id_00074'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/jafri_rice_winslow_1998',
      'Model_entity': 'jafri_rice_winslow_1998_a.cellml#id_00017'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/tentusscher_noble_noble_panfilov_2004',
      'Model_entity': 'tentusscher_noble_noble_panfilov_2004_c.cellml#id_00050'
    },
      ...
    , {
      'graph': 'https://models.physiomeproject.org/workspace/viswanathan_shaw_rudy_1999',
      'Model_entity': 'viswanathan_shaw_rudy_1999_c.cellml#id_00095'
    }]
  }
  ```
* Get model entities from BioModels with standard setting using NLTK Parser:
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='bm', parser='nltk')
  query = 'mitochondrial calcium ion transmembrane transport'
  result = nlimed.getModels(query=query,format='json')
  ```
  The code produce 6 model entities:
  ```
  {
  'vars': ['model', 'type', 'element', 'notes', 'name'],
    'results': [{
      'model': 'http://identifiers.org/biomodels.db/BIOMD0000000354',
      'type': 'http://identifiers.org/biomodels.vocabulary#reaction',
      'element': 'http://identifiers.org/biomodels.db/BIOMD0000000354#_982817',
      'name': 'UniporterFromCytosol'
    },
      ...
    , {
      'model': 'http://identifiers.org/biomodels.db/BIOMD0000000355',
      'type': 'http://identifiers.org/biomodels.vocabulary#reaction',
      'element': 'http://identifiers.org/biomodels.db/BIOMD0000000355#_032020',
      'name': 'CytToMito'
    },
      ...
    ]
  }
  ```
* Get model entities from BioModels with precision level 2, alpha=4, beta=0.7, gamma=0.5, delta=0.8 and NLTK parser
```python
from NLIMED import NLIMED
nlimed = NLIMED(repo='bm', parser='nltk', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8)
query = 'mitochondrial calcium ion transmembrane transport'
result = nlimed.getModels(query=query,format='json')
```
Resulting 12 model entities:
```
'vars': ['model', 'type', 'element', 'notes', 'name'],
  'results': [{
    'model': 'http://identifiers.org/biomodels.db/BIOMD0000000354',
    'type': 'http://identifiers.org/biomodels.vocabulary#reaction',
    'element': 'http://identifiers.org/biomodels.db/BIOMD0000000354#_982817',
    'name': 'UniporterFromCytosol'
  },
    ...
  , {
    'model': 'http://identifiers.org/biomodels.db/BIOMD0000000355',
    'type': 'http://identifiers.org/biomodels.vocabulary#reaction',
    'element': 'http://identifiers.org/biomodels.db/BIOMD0000000355#_032020',
    'name': 'CytToMito'
  },
    ...
  , {
    'model': 'http://identifiers.org/biomodels.db/BIOMD0000000354#_982817',
    'type': 'http://biomodels.net/biology-qualifiers#isVersionOf',
    'element': 'http://purl.obolibrary.org/obo/GO:0006851'
  },
    ...
  , {
    'model': 'http://identifiers.org/biomodels.db/BIOMD0000000355#_032020',
    'type': 'http://biomodels.net/biology-qualifiers#isVersionOf',
    'element': 'http://purl.obolibrary.org/obo/GO:0006851'
  },
    ...
  ]
}
```
### Get Query Annotation
In a case you just need to utilise the annotation function, you can use getAnnotated function. By this, the system will not request Internet connection for SPARQL request. However, if you use NCBO Annotator, Internet connection is still required.
* Code example to annotated query "concentration of potassium in the portion of tissue fluid" in the PMR using Stanford parser
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='stanford', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8)
  query = 'concentration of potassium in the portion of tissue fluid'
  result = nlimed.getAnnotated(query=query,format='json')
  ```
  Result:
  ```
  {
    'phrases': ['concentration', 'potassium', 'portion tissue fluid'],
    'result': [
      [
        ['http://identifiers.org/opb/OPB_00340', 'http://purl.obolibrary.org/obo/CHEBI_29103', 'http://purl.obolibrary.org/obo/FMA_9673'], 5.061734018829371
      ]
    ]
  }
  ```
  The query is separated into three phrases, then each phrase is classify into an ontology. There is a score 5.061734018829371 indicating the weight of ontologies combination.

* Code example to annotated query "concentration of potassium in the portion of tissue fluid" in the PMR using Stanford parser, pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='stanford', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8)
  query = 'flux of sodium'
  result = nlimed.getAnnotated(query=query,format='json')
  ```
  Result:
  ```
  {
    'phrases': ['concentration', 'potassium', 'portion tissue fluid'],
    'result': [
      [
        ['http://identifiers.org/opb/OPB_00340', 'http://purl.obolibrary.org/obo/CHEBI_29103', 'http://purl.obolibrary.org/obo/FMA_9673'], 5.061734018829371
      ],
      [
        ['https://identifiers.org/opb/OPB_00340', 'http://purl.obolibrary.org/obo/CHEBI_29103', 'http://purl.obolibrary.org/obo/FMA_9673'], 5.020508088576971
      ],
      [
        ['http://identifiers.org/opb/OPB_00340', 'http://identifiers.org/chebi/CHEBI:29103', 'http://purl.obolibrary.org/obo/FMA_9673'], 5.06090745289317
      ],
      [
        ['https://identifiers.org/opb/OPB_00340', 'http://identifiers.org/chebi/CHEBI:29103', 'http://purl.obolibrary.org/obo/FMA_9673'], 5.019681522640769
      ],
      [
        ['http://identifiers.org/opb/OPB_00340', 'http://purl.obolibrary.org/obo/CHEBI_29103', 'http://purl.obolibrary.org/obo/FMA_280556'], 4.307255058507058
      ],
      [
        ['https://identifiers.org/opb/OPB_00340', 'http://purl.obolibrary.org/obo/CHEBI_29103', 'http://purl.obolibrary.org/obo/FMA_280556'], 4.266029128254657
      ],
      [
        ['http://identifiers.org/opb/OPB_00340', 'http://identifiers.org/chebi/CHEBI:29103', 'http://purl.obolibrary.org/obo/FMA_280556'], 4.3064284925708565
      ],
      [
        ['https://identifiers.org/opb/OPB_00340', 'http://identifiers.org/chebi/CHEBI:29103', 'http://purl.obolibrary.org/obo/FMA_280556'], 4.265202562318455
      ]
    ]
  }
  ```
  Just the same as the previous result, the query is separated into three phrases, then each phrase is classify into an ontology. Since we use higher precisin level, the function presents more ontologies combination with a different score. Higher score means higher probability of relevant annotation.

### Get SPARQL
It is also possible to get SPARQL only without model entities. It utilise getSparql function which generated all possible SPARQL based on annotation results.

* Get SPARQL code for query "concentration of potassium in the portion of tissue fluid" in the PMR using Stanford parser
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='stanford')
  query = 'flux of sodium'
  result = nlimed.getSparql(query=query,format='json')
  ```
  Resulting a list of SPARQL:
  ```
  [
    'SELECT ?graph ?Model_entity ?desc
      WHERE { GRAPH ?graph {
        ?e  <http://www.bhi.washington.edu/SemSim#hasPhysicalDefinition> <http://purl.obolibrary.org/obo/FMA_9673> .
        ?c  <http://www.bhi.washington.edu/SemSim#hasPhysicalDefinition> <http://purl.obolibrary.org/obo/CHEBI_29103> .
        ?a  <http://www.bhi.washington.edu/SemSim#hasPhysicalDefinition> <http://identifiers.org/opb/OPB_00340> .
        ?Model_entity  <http://www.bhi.washington.edu/SemSim#isComputationalComponentFor> ?a .
        ?a  <http://www.bhi.washington.edu/SemSim#physicalPropertyOf> ?c .
        ?c  <http://www.obofoundry.org/ro/ro.owl#part_of> ?e .
        OPTIONAL{?Model_entity <http://purl.org/dc/terms/description> ?desc .} }}'
  ]
  ```
* Get SPARQL code for query "concentration of potassium in the portion of tissue fluid" in the PMR using Stanford parser with precision level 2, alpha=4, beta=0.7, gamma=0.5, delta=0.8 and NLTK parser
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='stanford', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8)
  query = 'flux of sodium'
  result = nlimed.getSparql(query=query,format='json')
  ```
  The result can be 0 or more than one SPARQL based on the RDF Graph Index.
  ```
  [
  'SELECT ?graph ?Model_entity ?desc
    WHERE { GRAPH ?graph {  ?c  <http://www.bhi.washington.edu/SemSim#hasPhysicalDefinition> <http://purl.obolibrary.org/obo/CHEBI_29103> .
      ?e  <http://www.bhi.washington.edu/SemSim#hasPhysicalDefinition> <http://purl.obolibrary.org/obo/FMA_9673> .
      ?a  <http://www.bhi.washington.edu/SemSim#hasPhysicalDefinition> <http://identifiers.org/opb/OPB_00340> .
      ?Model_entity  <http://www.bhi.washington.edu/SemSim#isComputationalComponentFor> ?a .
      ?a  <http://www.bhi.washington.edu/SemSim#physicalPropertyOf> ?c .
      ?c  <http://www.obofoundry.org/ro/ro.owl#part_of> ?e .
      OPTIONAL{?Model_entity <http://purl.org/dc/terms/description> ?desc .} }}'
  ]
  ```

## Recreate Indexes (RDF Graph Index and Text Feature Index)

All indexes are already provided in this project. However, if you want to recreate all indexes you can use the following script on command prompt or terminal. Please be patient, it may take times to be finished.

### Indexing the pmr

```
NLIMED --build-index pmr
```

### Indexing biomodels

```
NLIMED --build-index bm
```
