def config(parsers={'ncbo':'fc5d5241-1e8e-4b44-b401-310ca39573f6', 'coreNLP':'~/corenlp'}):
    """
        Configuring apikey for ncbo and/or
        installing coreNLP and start the server
        Input: - parsers is a dictionary consisting of pairs of parser name and
                 its keyword or installation location
        Example: - config(parsers={'ncbo':'fc5d5241-1e8e-4b44-b401-310ca39573f6', 'coreNLP':'~/corenlp'})
                 - config() --> configuration with default value
    """
    import json
    import os.path
    currentPath = os.path.dirname(os.path.realpath(__file__))
    configFile = os.path.join(currentPath,'config.txt')

    # setup coreNLP server if the installation location is available
    if 'coreNLP' in parsers:

        # make sure the input is abs path, if not, convert it to abs path
        from os.path import expanduser
        parsers['coreNLP'] = expanduser(parsers['coreNLP'])
        if not os.path.isabs(parsers['coreNLP']):
            parsers['coreNLP'] = expanduser('~/' + parsers['coreNLP'])

        # install when it it not yet installed
        if not os.path.isdir(parsers['coreNLP']):
            print('Relax ... installing CoreNLP take minutes')
            import stanza
            stanza.install_corenlp(dir=parsers['coreNLP'])
            parsers['coreNLP_EP'] = 'http://localhost:9001'
        else:
            print('CoreNLP already installed')

    with open(configFile, 'w') as fp:
        json.dump(parsers, fp)

def getConfig():
    import json
    import os.path
    currentPath = os.path.dirname(os.path.realpath(__file__))
    file = os.path.join(currentPath,"config.txt")
    isExist = os.path.exists(file)
    if isExist:
        with open(file, 'r') as fp:
            data = json.load(fp)
        return data
    else:
        return {}

def download():
    import os
    from pathlib import Path as path
    HOME_DIR = str(path.home())

    # check nltk_data availability, download if not available
    import nltk
    nltk_rsc = os.path.join(HOME_DIR, 'nltk_data')
    for required in [os.path.join('corpora', 'stopwords.zip'), os.path.join('taggers', 'averaged_perceptron_tagger.zip')]:
        if not os.path.exists(os.path.join(nltk_rsc, required)):
            print('downloading nltk: ', required[:-4])
            nltk.download(os.path.basename(required)[:-4], quiet=True)

    # check stanza_data availability, download if not available
    import stanza
    stanza_rsc = os.path.join(HOME_DIR, 'stanza_resources/en/ner')
    for required in ['anatem.pt', 'bionlp13cg.pt', 'i2b2.pt', 'jnlpba.pt']:
        if not os.path.exists(os.path.join(stanza_rsc, required)):
            print('downloading stanza: ', required[:-3])
            stanza.download('en', package='craft', processors={'ner': required[:-3]}, verbose=False)

    # check benepar_data availability, download if not available
    import benepar
    if not os.path.exists(os.path.join(nltk_rsc, 'models', 'benepar_en3')):
        print('downloading benepar: benepar_en3')
        benepar.download('benepar_en3')

class NLIMED:
    """
    NLIMED: Natural Language Interface Model Entities Discovery
            Class NLIMED is the main class for Natural Language Query (NLQ) annotation, SPARQL composition, and model entities retrieval.
            The creation of NLIMED instance needs 2 mandatory and 5 optional attributes.

        Examples:
            nlimed = NLIMED(repo='pmr', parser='CoreNLP')
            nlimed = NLIMED(repo='pmr', parser='CoreNLP', pl=3)
            nlimed = NLIMED(repo='pmr', parser='CoreNLP', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8, theta=0.01)
            nlimed = NLIMED(repo='bm', parser='Benepar')
            nlimed = NLIMED(repo='bm', parser='Benepar', pl=2)
            nlimed = NLIMED(repo='bm', parser='Benepar', pl=3, alpha=2, beta=0.2, gamma=0.2, delta=0.3, theta=0.01, quite=True)
            nlimed = NLIMED(repo='bm-omex', parser='xStanza', pl=3, alpha=2, beta=0.2, gamma=0.2, delta=0.3, theta=0.01, cutoff=1.0, quite=True)
            nlimed = NLIMED(repo='bm-omex', parser='xStanza', pl=3, alpha=2, beta=0.2, gamma=0.2, delta=0.3, theta=0.01, cutoff=1.0, tfMode=1, quite=True)


        Attributes:
            repo {'pmr', 'bm', 'bm-omex'} (mandatory): the repository name, pmr for the Physiome Model Repository or bm for the BioModels.
            parser {'CoreNLP', 'Benepar', 'xStanza', 'xStanza', 'ncbo'} (mandatory): the type of parser used to annotated natural language query into ontologies.
            pl (int) (optional): precision level, to set up the maximum number of considered ontologies related to phrases
            alpha (float) (>=0) (optional) : the multiplier of preffered_label feature
            beta (float) (>=0) (optional) : the multiplier of synonyms feature
            gamma (float) (>=0) (optional) : the multiplier of definitions feature
            delta (float) (>=0) (optional) : the multiplier of palrent labels feature
            theta (float) (>=0) (optional) : the multiplier of description feature
            cutoff (float) (>=0) (optional) : the cutoff
            tfMode (int) (>=1) (optional) : related to the equation to calculate TF, 1: using dependency, 2: without dependency, 3: using dependency but select the highest feature.
            quiet (boolean) (optional) : set to not print unnecessary message

        Functions:
            getModels(query, format):

            getSparql(query,  format)

            getAnnotated(query,  format):

            getVerbose(query, format)
    """
    def __init__(self, **vargs):
        vargs = self.__getValidArgs(**vargs)
        parser = vargs['parser'].lower()
        try:
            if parser == 'corenlp':
                from NLIMED.query_annotator import CoreNLPAnnotator
                self.__annotator = CoreNLPAnnotator(**vargs)
            elif parser == 'benepar':
                from NLIMED.query_annotator import BeneparAnnotator
                self.__annotator = BeneparAnnotator(**vargs)
            elif parser == 'ncbo':
                from NLIMED.query_annotator import OBOLIBAnnotator
                self.__annotator = OBOLIBAnnotator()
            elif parser == 'stanza':
                from NLIMED.query_annotator import StanzaAnnotator
                self.__annotator = StanzaAnnotator(**vargs)
            elif parser == 'xstanza':
                from NLIMED.query_annotator import MixedAnnotator
                self.__annotator = MixedAnnotator(**vargs)
        except:
            raise Error("  Error: cannot instantiate annotator, try other parser {CoreNLP, Benepar, ncbo}")
        from NLIMED.sparql_generator import SPARQLGenerator
        self.__sparqlGen = SPARQLGenerator(vargs['repo'])
        pass

    def __getValidArgs(self, **vargs):
        """
        Check wheteher the arguments provided to create NLIMED instance are appropriate and correct
        """
        from NLIMED import __dictArgsOptional__, __dictArgsMandatory__, __dictDefArgsVal__
        def __showErrorMessage():
            return """
            arguments are not complete or values are not correct
              - repo ['pmr','bm','bm-omex']
              - parser ['CoreNLP', 'Benepar', 'stanza', 'xStanza', 'ncbo']
              - [pl  PL>1]
              - [alpha a>=0]
              - [beta b>=0]
              - [gamma g>=0]
              - [delta d>=0]
              - [theta t>=0]
              - [cutoff c>=0]
              - [tfMode 1 <= t <=3]
              - [quite boolean]
            example:
              minimum call:
                NLIMED(repo='pmr', parser='CoreNLP')
              complete call:
                NLIMED(repo='pmr', parser='CoreNLP', pl=1, alpha=4, beta=0.7, gamma=0.5, delta=0.8, theta=0.01, cutoff=1, tfMode=1, quite=True)
            """
        if all(key in vargs.keys() for key in __dictArgsMandatory__):
            # check mandatory arguments
            for key in __dictArgsMandatory__:
                if vargs[key].lower() not in __dictArgsMandatory__[key]:
                    raise ValueError(__showErrorMessage())
            # check optional arguments
            for key in __dictArgsOptional__:
                # check value
                if key in vargs:
                    if isinstance(__dictArgsOptional__[key], list):
                        if vargs[key] not in __dictArgsOptional__[key]:
                            raise ValueError(__showErrorMessage())
                    elif isinstance(__dictArgsOptional__[key], bool):
                        if not isinstance(vargs[key],bool):
                            raise ValueError(__showErrorMessage())
                    else:
                        vargs[key] = __dictArgsOptional__[key](vargs[key])
                # use default value if not available
                else:
                    vargs[key] = __dictDefArgsVal__[key]
            return vargs

        else:
            raise ValueError(__showErrorMessage())

    def getModels(self, query, format='json'):
        """
        A function to get model entities by providing natural language query:

            Example:
                nlimed = NLIMED(repo='pmr', parser='CoreNLP')
                results = nlimed.getModels('flux of sodium','json')

            Arguments:
                query (string): text containing natural language query_type
                format {'json','print'}: specifying returning format, json for json format, print to show on console

            Results:
                json: {'vars':[...], 'results':[...]}
                    vars is a list of fields name
                    results is the retrieved data containing model entities

                print: print model entities to console
        """
        annotated = self.__annotator.annotate(query)
        predicates = annotated['predicates'] if 'predicates' in annotated else []
        resultDict = {'vars': [], 'results': [], 'sparqls':[]}
        for annTerm in annotated['result']:
            sparqls = self.__sparqlGen.constructSPARQL(annTerm, predicates)
            for sparql in sparqls:
                sparqlResult = self.__sparqlGen.runSparQL(sparql[0])
                if len(sparqlResult)>0:
                    resultDict['sparqls'] += [sparql]
                    resultDict['vars'] = sparqlResult['head']['vars']
                    for binding in sparqlResult['results']['bindings']:
                        result = {var: binding[var]['value'] for var in binding}
                        if result not in resultDict['results']:
                            resultDict['results'] += [result]
        if format == 'json':
            return resultDict
        elif format == 'print':
            print(resultDict['vars'])
            for result in resultDict['results']:
                for key, field in result.items():
                    print('  ' + key + ': ' + field)
                print('\n')

    def getSparql(self, query, format='json'):
        """
        A function to get SPARQL[s] by providing natural language query:

            Example:
                nlimed = NLIMED(repo='pmr', parser='CoreNLP')
                results = nlimed.getSparql('flux of sodium','json')

            Arguments:
                query (string): text containing natural language query_type
                format {'json','print'}: specifying returning format, json for json format, print to show on console

            Results:
                json: a list of SPARQL[s]
                print: print SPARQL[s] to console
        """
        annotated = self.__annotator.annotate(query)
        predicates = annotated['predicates'] if 'predicates' in annotated else []
        sparqlList = []
        for annTerm in annotated['result']:
            sparqlList += list(self.__sparqlGen.constructSPARQL(annTerm, predicates))
        sparqlList.sort(key=lambda x:x[1], reverse=True)

        if format == 'json':
            return sparqlList
        elif format == 'print':
            for sparql in sparqlList:
                print(sparql)
                print('\n')

    def getAnnotated(self, query,  format='json'):
        """
        A function to get annotation results by providing natural language query:

            Example:
                nlimed = NLIMED(repo='pmr', parser='CoreNLP')
                results = nlimed.getAnnotated('flux of sodium','json')

            Arguments:
                query (string): text containing natural language query_type
                format {'json','print'}: specifying returning format, json for json format, print to show on console

            Results:
                json: {'phrases':[...],'result':{'ontologies':[...],'weight':float}}
                print: print annotation results to console
        """
        annotated = self.__annotator.annotate(query)
        if format == 'json':
            return annotated
        elif format == 'print':
            print(' phrases: ' + ', '.join(annotated['phrases']))
            for result in annotated['result']:
                print(' ontologies: ')
                print('  ' + '\n  '.join(result[0]))
                print('  weight: ' + str(result[1]))
                print('\n')

    def getVerbose(self, query, format='json'):
        """
        A function to get verbose results of annotation, SPARQL[s], and model entities by providing natural language query:

            Example:
                nlimed = NLIMED(repo='pmr', parser='CoreNLP')
                results = nlimed.getVerbose('flux of sodium','json')

            Arguments:
                query (string): text containing natural language query_type

                format {'json','print'}: specifying returning format, json for json format, print to show on console

            Results:
                json: {'annotated':{'phrases':[...],'result':{'ontologies':[...],'weight':float}},
                        'sparql':[...],
                        'models':{'vars':[...], 'results':[...]}}

                print: print verbose results to console
        """
        annotated = self.getAnnotated(query, format)
        sparqlList = self.getSparql(query, format)
        modelList = self.getModels(query, format)
        if format == 'json':
            return {'annotated': annotated, 'sparql': sparqlList, 'models': modelList}

    def setWeighting(self, alpha, beta, gamma, delta, theta, cutoff, pl, tfMode=1):
        self.__annotator.setWeighting(alpha, beta, gamma, delta, theta, cutoff, pl, tfMode)

    def getWeighting(self):
        return self.__annotator.getWeighting()

    def hyperparam(self, datatTrainFile, precAt=10, isVerbose=True):
        return self.__annotator.hyperparam(datatTrainFile, precAt, isVerbose)

    def auc(self, datatTrainFile):
        return self.__annotator.auc(datatTrainFile)
