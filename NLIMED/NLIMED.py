from NLIMED.query_annotator import StanfordAnnotator, NLTKAnnotator, OBOLIBAnnotator, StanzaAnnotator, MixedAnnotator
from NLIMED.sparql_generator import SPARQLGenerator

def config(apikey, corenlp_home):
    import json
    import os.path
    currentPath = os.path.dirname(os.path.realpath(__file__))
    file = os.path.join(currentPath,"config.txt")
    data = {"apikey":apikey,"corenlp-home":corenlp_home}
    with open(file, 'w') as fp:
        json.dump(data, fp)

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
        return {"apikey":"","corenlp-home":""}

class NLIMED:
    """
    NLIMED: Natural Language Interface Model Entities Discovery
            Class NLIMED is the main class for Natural Language Query (NLQ) annotation, SPARQL composition, and model entities retrieval.
            The creation of NLIMED instance needs 2 mandatory and 5 optional attributes.

        Examples:
            nlimed = NLIMED(repo='pmr', parser='stanford')
            nlimed = NLIMED(repo='pmr', parser='stanford', pl=3)
            nlimed = NLIMED(repo='pmr', parser='stanford', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8, theta=0.01)
            nlimed = NLIMED(repo='bm', parser='nltk')
            nlimed = NLIMED(repo='bm', parser='nltk', pl=2)
            nlimed = NLIMED(repo='bm', parser='nltk', pl=3, alpha=2, beta=0.2, gamma=0.2, delta=0.3, theta=0.01, quite=True)
            nlimed = NLIMED(repo='bm-omex', parser='mixed', pl=3, alpha=2, beta=0.2, gamma=0.2, delta=0.3, theta=0.01, cutoff=1.0, quite=True)

        Attributes:
            repo {'pmr', 'bm', 'bm-omex'} (mandatory): the repository name, pmr for the Physiome Model Repository or bm for the BioModels.
            parser {'stanford', 'nltk', 'stanza', 'mixed', 'ncbo'} (mandatory): the type of parser used to annotated natural language query into ontologies.
            pl (int) (optional): precision level, to set up the maximum number of considered ontologies related to phrases
            alpha (float) (>=0) (optional) : the multiplier of preffered_label feature
            beta (float) (>=0) (optional) : the multiplier of synonyms feature
            gamma (float) (>=0) (optional) : the multiplier of definitions feature
            delta (float) (>=0) (optional) : the multiplier of palrent labels feature
            theta (float) (>=0) (optional) : the multiplier of description feature
            cutoff (float) (>=0) (optional) : the cutoff
            quiet (boolean) (optional) : set to not print unnecessary message

        Functions:
            getModels(query, format):

            getSparql(query,  format)

            getAnnotated(query,  format):

            getVerbose(query, format)
    """
    def __init__(self, **vargs):
        vargs = self.__getValidArgs(**vargs)
        try:
            if vargs['parser'] == 'stanford':
                self.__annotator = StanfordAnnotator(**vargs)
            elif vargs['parser'] == 'nltk':
                self.__annotator = NLTKAnnotator(**vargs)
            elif vargs['parser'] == 'ncbo':
                self.__annotator = OBOLIBAnnotator()
            elif vargs['parser'] == 'stanza':
                self.__annotator = StanzaAnnotator(**vargs)
            elif vargs['parser'] == 'mixed':
                self.__annotator = MixedAnnotator(**vargs)
        except:
            raise Error("  Error: cannot instantiate annotator, try other parser {stanford, nltk, ncbo}")
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
              - parser ['stanford', 'nltk', 'stanza', 'mixed', 'ncbo']
              - [pl  PL>1]
              - [alpha a>=0]
              - [beta b>=0]
              - [gamma g>=0]
              - [delta d>=0]
              - [theta t>=0]
              - [cutoff c>=0]
              - [quite boolean]
            example:
              minimum call:
                NLIMED(repo='pmr', parser='stanford')
              complete call:
                NLIMED(repo='pmr', parser='stanford', pl=1, alpha=4, beta=0.7, gamma=0.5, delta=0.8, theta=0.01, cutoff=1, quite=True)
            """
        if all(key in vargs.keys() for key in __dictArgsMandatory__):
            # check mandatory arguments
            for key in __dictArgsMandatory__:
                if vargs[key] not in __dictArgsMandatory__[key]:
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
                nlimed = NLIMED(repo='pmr', parser='stanford')
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
                nlimed = NLIMED(repo='pmr', parser='stanford')
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
                nlimed = NLIMED(repo='pmr', parser='stanford')
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
                nlimed = NLIMED(repo='pmr', parser='stanford')
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

    def setWeighting(self, alpha, beta, gamma, delta, theta, cutoff, pl):
        self.__annotator.setWeighting(alpha, beta, gamma, delta, theta, cutoff, pl)

    def getWeighting(self):
        return self.__annotator.getWeighting()

    def hyperparam(self, datatTrainFile, precAt=10, isVerbose=True):
        return self.__annotator.hyperparam(datatTrainFile, precAt, isVerbose)
