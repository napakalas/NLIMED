# NLIMED

![Latest Version](https://img.shields.io/pypi/v/nlimed.svg?colorB=bc4545)
![Python Versions](https://img.shields.io/pypi/pyversions/nlimed.svg?colorB=bc4545)

Natural Language Interface for Model Entity Discovery (NLIMED) is an interface to search model entities (i.e. flux of sodium across the basolateral plasma membrane, the concentration of potassium in the portion of tissue fluid) in the biosimulation models in repositories. The interface utilises the RDF inside biosimulation models and metadata from BioPortal. Currently, the interface can retrieve model entities from the Physiome Model Repository (PMR, https://models.physiomeproject.org) and the BioModels (https://www.ebi.ac.uk/biomodels/).

In general, NLIMED works by converting natural language query into SPARQL, so it may help users by avoiding the rigid syntax of SPARQL, query path consisting multiple predicates, and detail knowledge about ontologies.

Note: model entities extracted from BioModels are those having ontology classes indexed by BioPortal.

License :: OSI Approved :: GNU General Public License (GPL)

## Demo
1. [Online web](http://130.216.217.102/nlimed)
2. [Colab](https://colab.research.google.com/drive/1xq3ewKIT9pHD0AveWuYy2cpJvG4oLjDR#scrollTo=VYv3uMcMt6HJ) - online tutorial

## References
The main reference of this work is: https://doi.org/10.1101/756304

Cite the following works when you implement NLIMED with parser or nlp of:
1. CoreNLP: https://stanfordnlp.github.io/CoreNLP/citing.html
2. Benepar: https://arxiv.org/abs/1805.01052
3. NCBO: https://www.ncbi.nlm.nih.gov/pubmed/21347171
4. Stanza and xStanza: http://arxiv.org/abs/2007.14640

## Installation
We sugest you to install NLIMED from PyPI. If you already installed [pip](https://pip.pypa.io/en/stable/installing/), run the following command:
  ```
  pip install NLIMED
  ```
As an alternative, you can clone and download this github repository and use the following command:
  ```
  git clone https://github.com/napakalas/NLIMED.git
  cd NLIMED
  pip install -e .
  ```

Follow this [Colab](https://colab.research.google.com/drive/1xq3ewKIT9pHD0AveWuYy2cpJvG4oLjDR#scrollTo=VYv3uMcMt6HJ) tutorial for easy step by step installation and utilisation.

## Configuration

NLIMED implements CoreNLP Parser, Benepar Parser, and NCBO parser. You may select one of them for your system.
  * Benepar, Stanza, xStanza:
    - automatically deploy as a dependency.
  * To run CoreNLP and NCBO, you need to run configuration. It can be using default value
    ```python
    from NLIMED import config
    config()
    ```
    or using your own [NCBO api key](https://bioportal.bioontology.org/help#Getting_an_API_key) and self defined CoreNLP installation location
    ```python
    from NLIMED import config
    config(apikey='your-api-key', corenlp_home='installation-location')
    ```

  * It is also possible to run configuration from command prompt or terminal:

      ```
      NLIMED --config --apikey {your-ncbo-api-key} --corenlp-home {installation-location}
      ```

## Issues

For any issues please follows and reports [issues](https://github.com/napakalas/NLIMED/issues).

## Experiment
We conducted an experiment to measure NLIMED performance in term of:
1. Annotating natural language query to ontology classes
2. NLIMED behaviour to native query in PMR

The experiment is available at:
1. [Jupyter](https://github.com/napakalas/NLIMED/tree/experiment)
2. Colab:
  * [NLQ Annotator Performance](https://colab.research.google.com/drive/1xq3ewKIT9pHD0AveWuYy2cpJvG4oLjDR#scrollTo=KwQAqORxsnk_)
  * [NLIMED Behaviour on Native Query in PMR (Historical Data)](https://colab.research.google.com/drive/1xq3ewKIT9pHD0AveWuYy2cpJvG4oLjDR#scrollTo=qsEFA2pGtVZH)

## How NLIMED works?
Here is the process inside NLIMED converting natural language query (NLQ) and SPARQL and then retrieving model entities from biomodel repositories:
1. NLQ Annotation -- Annotating NLQ to ontology classes

    - NLQ is parsed using selected parser (CoreNLP, Benepar, NCBO, Stanza, or xStanza), resulting candidate noun phrases (CNPs).
    - Measuring association level of each CNP to ontology classes. The measurement utilises five textual features, i.e. preferred label, synonym, definition,, parent label (from ontology class) and local definition (from biosimulation model)
    - Select CNPs with highest association, having longest term, and not overlapping with other CNP. The selected CNPs should cover all terms in NLQ.
    - Filter out CNP having low association to ontology class (<cutoff)
    - Select the top pl of ontology classes from selected CNPs
    - Combine all possible ontology classes with no overlapping CNPs

2. SPARQL Generation
    - Construct SPARQLs for each ontotology class combinations

3. Retrieve model entities by sending each SPARQLs to model repository SPARQL endpoints.

## Utilising NLIMED in your Python code

The main class for retrieving model entities from repositories is NLIMED in NLIMED.py. Utilising this class, we can annotate query into ontology classes, get all possible SPARQL, and get model entities. We suggest you to create one NLIMED object for all your queries since it will reuse the loaded indexes so it can save your device resources.

### Get Model Entities
The following codes are used to retrieve model entities from the PMR or Biomodels.
* Returning model entities from the PMR using CoreNLP parser with standard setting for query: "mitochondrial calcium ion transmembrane transport"
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='CoreNLP')
  query = 'mitochondrial calcium ion transmembrane transport'
  result = nlimed.getModels(query=query,format='json')

  """
  where:
  - repo : repository {'pmr', 'bm', 'bm-omex'}
  - parser : parser tool {'CoreNLP', 'Benepar', 'xStanza', 'Stanza', 'ncbo'}
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

* It also possible to increase the precision level, so NLIMED can show more results. Here we are returning model entities from the PMR using CoreNLP parser and precision level 2, alpha=4, beta=0.7, gamma=0.5, delta=0.8, theta=0.01.
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='CoreNLP', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8, theta=0.1, cutoff=1, tfMode=3)
  query = 'mitochondrial calcium ion transmembrane transport'
  result = nlimed.getModels(query=query,format='json')

  """
  where:
  - repo (mandatory) : repository {'pmr', 'bm', 'bm-omex'}
  - parser : parser tool {'CoreNLP', 'Benepar', 'Stanza', 'xStanza', 'ncbo'}
  - pl (optional) : precision level, the minimum value is 1
  - alpha (optional) : preffered label weight, the minimum value is 0
  - beta (optional) : synonym weight, the minimum value is 0
  - gamma (optional) : definition weight, the minimum value is 0
  - delta (optional) : parent labels weight, the minimum value is 0
  - theta (optional) : description weight, the minimum value is 0
  - cutoff (optional) : minimum degree of asociation, the minimum value is 0
  - tfMode (optional) : the term frequency calculation mode, [1,2,3]
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
* Get model entities from BioModels with standard setting using Benepar Parser:
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='bm', parser='Benepar')
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
* Get model entities from BioModels with precision level 2, alpha=4, beta=0.7, gamma=0.5, delta=0.8, theta=0.01 and Beneparvv parser
```python
from NLIMED import NLIMED
nlimed = NLIMED(repo='bm', parser='Benepar', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8, theta=0.01)
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
* Code example to annotated query "concentration of potassium in the portion of tissue fluid" in the PMR using CoreNLP parser
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='CoreNLP', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8, theta=0.01)
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
  The query is separated into three phrases, then each phrase is classify into ontology classes. There is a score 5.061734018829371 indicating the weight of ontology classes combination.

* Code example to annotated query "concentration of potassium in the portion of tissue fluid" in the PMR using CoreNLP parser, pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8, theta=0.01
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='CoreNLP', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8, theta=0.01)
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
  Just the same as the previous result, the query is separated into three phrases, then each phrase is classify into ontology classes. Since we use higher precisin level, the function presents more ontology classes combination with a different score. Higher score means higher probability of relevant annotation.

### Get SPARQL
It is also possible to get SPARQL only without model entities. It utilise getSparql function which generated all possible SPARQL based on annotation results.

* Get SPARQL code for query "concentration of potassium in the portion of tissue fluid" in the PMR using CoreNLP parser
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='CoreNLP')
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
* Get SPARQL code for query "concentration of potassium in the portion of tissue fluid" in the PMR using CoreNLP parser with precision level 2, alpha=4, beta=0.7, gamma=0.5, delta=0.8, theta=0.01 and CoreNLP parser
  ```python
  from NLIMED import NLIMED
  nlimed = NLIMED(repo='pmr', parser='CoreNLP', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8, theta=0.01)
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

  ## Running NLIMED from console (query to get model entities)
  NLIMED can be run directly on command prompt or terminal. There are 2 mandatory arguments and 7 optional arguments. To get help about the required arguments, run:
  ```terminal
  NLIMED -h
  ```
  then you will get:
  ```terminal
  usage: NLIMED [-h] -r {pmr,bm,all} -p {CoreNLP,Benepar,ncbo} -q QUERY
                   [-pl PL] [-s {models,sparql,annotation,verbose}] [-a ALPHA]
                   [-b BETA] [-g GAMMA] [-d DELTA] [-t THETA]

  optional arguments:
    -h, --help            show this help message and exit
    -r {pmr,bm,all}, --repo {pmr,bm,all}
                          repository name
    -p {corenlp,benepar,stanza,xstanza,ncbo}, --parser {corenlp,benepar,stanza,xstanza,ncbo}
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
    -t THETA, --theta THETA
                          Minimum theta is 0
    -c CUTOFF, --cutoff CUTOFF
                          Minimum cutoff is 0
    -tf TFMODE, --tfMode TFMODE
                          tf mode calculation, [1,2,3]
  ```
  Here is the description of those arguments:
  * -r {pmr,bm,all} or --repo {pmr,bm,all} (mandatory) is the name of repository. pmr is the Physiome Repository Model, bm is BioSimulations, all is for both repositories
  * -p {corenlp,benepar,stanza,xstanza,ncbo} or --parser {CoreNLP,Benepar,ncbo} (mandatory) is the type of parser for query annotation.
  * -q QUERY or --query QUERY (mandatory) is the query text. For a multi words query, the words should be double quoted.
  * -pl PL (optional) is precision level indicating the number of ontology classes used to construct SPARQL. Larger number will utilised more ontology cllasses which may generate more SPARQL and produce more results. Minimum value is 1. Default value is 1.
  * -s {models,sparql,annotation,verbose} or --show {models,sparql,annotation,verbose} (optional) is for selecting presented results. models shows models, sparql shows all possible SPARQLs, annotation shows annotation results, and verbore shows annotation results, SPARQLs, and models
  * -a ALPHA or --alpha ALPHA (optional) is to set up the weight of preffered label feature. Minimum alpha is 0. Default value is 3.0.
  * -b BETA or --beta BETA (optional) is to set up the weight of synonym feature. Minimum beta is 0. Default value is 3.0.
  * -g GAMMA or --gamma GAMMA (optional) is to set up the weight of definition feature. Minimum gamma is 0. Default value is 0.1.
  * -d DELTA, --delta DELTA (optional) is to set up the weight of parent labels feature. Minimum gamma is 0. Default value is 0.1.
  * -t THETA, --theta THETA (optional) is to set up the weight of description feature. Minimum theta is 0. Default value is 0.38.
  * -c CUTOFF, --cutoff (optional) is the minimum degree of association between a phrases and a ontology class used. Minimum cutoff is 0. Default value is 1.
  * -tf tfMode, --tfMode (optional) is the term frequency calculation mode, 1 = all features with dependency term, 2 = all features without dependency term, 3 = highest feature with dependency term. Devault value is 3.

  ### Running example
  * running with minimum setup for repository = Physiome Model Repository, parser = Benepar, query = "flux of sodium", and other default arguments values:
    ```
    NLIMED -r pmr -p Benepar -q "flux of sodium"
    ```
  * running with full setup for repository=BioModels, parser=CoreNLP, query="flux of sodium", precision level = 2, alpha = 2, beta = 1, gamma = 1, and delta = 1, theta = 0.4, cutoff = 1.0, tfMode = 3
    ```
    NLIMED -r bm -p CoreNLP -q "flux of sodium" -pl 2 -a 2 -b 1 -g 1 -d 1 -t 0.4 -c 1 -tf 3
    ```
    Note: running with CoreNLP parser may cause delay local server startup for the first run. However, for the next run, the delay is disappeared.

  * running for repository = Physiome Model Repository, parser = NCBO, query = "flux of sodium", precision level = 3,and other default arguments

    ```
    NLIMED -r pmr -p ncbo -q "flux of sodium" -pl 3
    ```
    Note: running with NCBO Parser parser is slower than other parsers because it is using a web service depended on the Internet connection.

## Recreate Indexes (RDF Graph Index and Text Feature Index)

All indexes are already provided in this project. However, if you want to recreate all indexes you can use the following script on command prompt or terminal. Please be patient, it may take times to be finished.

### Indexing the pmr
Download all required ontology dictionaries for indexing from (https://bioportal.bioontology.org/).
Preferably is csv files but obo files are working.
List of ontology dictionaries:
'SO','PW','PSIMOD','PR','PATO','OPB','NCBITAXON','MAMO',
'FMA','EFO','EDAM','ECO','CL','CHEBI','BTO','SBO',
'UNIPROT','KEGG','EC-CODE','ENSEMBL','GO'

```
NLIMED --build-index pmr "{location-of-ontology-files}"
```

### Indexing biomodels
1. Download all RDF files (ftp://ftp.ebi.ac.uk/pub/databases/RDF/biomodels/r31/biomodels-rdf.tar.bz2) as a compressed file from BioModels. Extract the compressed file at your convenience directory.

2. Run the following code:
    ```
    NLIMED --build-index bm "{location-of-ontology-files}" "{location-of-RDF-files}"
    ```
