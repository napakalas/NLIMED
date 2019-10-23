import sys
from NLIMED.QueryAnnotator import StanfordAnnotator, NLTKAnnotator, OBOLIBAnnotator
from NLIMED.SPARQLGenerator import SPARQLGenerator

dictArgs = {'repo': ['pmr', 'bm', 'all'], 'parser': ['stanford', 'nltk', 'ncbo'],
            'show': ['models', 'sparql', 'annotation', 'verbose'], 'pl': 1,
            'alpha':4, 'beta':0.7, 'gamma':0.5, 'delta':0.8}
dictArgsMandatory = {'repo','parser'}

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

            nlimed = NLIMED(repo='pmr', parser='stanford', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8)

            nlimed = NLIMED(repo='bm', parser='nltk')

            nlimed = NLIMED(repo='bm', parser='nltk', pl=2)

            nlimed = NLIMED(repo='bm', parser='nltk', pl=3, alpha=2, beta=0.2, gamma=0.2, delta=0.3)

        Attributes:
            repo {'pmr','bm'} (mandatory): the repository name, pmr for the Physiome Model Repository or bm for the BioModels.

            parser {'stanford','nltk','ncbo'} (mandatory): the type of parser used to annotated natural language query into ontologies.

            pl (int) (optional): precision level, to set up the maximum number of considered ontologies related to phrases

            alpha (float) (>=0) (optional) : the multiplier of preffered_label feature

            beta (float) (>=0) (optional) : the multiplier of synonym feature

            gamma (float) (>=0) (optional) : the multiplier of definition feature

            delta (float) (>=0) (optional) : the multiplier of description feature

        Functions:
            getModels(query, format):

            getSparql(query,  format)

            getAnnotated(query,  format):

            getVerbose(query, format)
    """
    def __init__(self, **vargs):
        isArgsValid = self.__isArgsValid(**vargs)
        if isArgsValid:
            try:
                if vargs['parser'] == 'stanford':
                    self.annotator = StanfordAnnotator(**vargs)
                elif vargs['parser'] == 'nltk':
                    self.annotator = NLTKAnnotator(**vargs)
                elif vargs['parser'] == 'ncbo':
                    self.annotator = OBOLIBAnnotator(**vargs)
            except:
                print("  Error: cannot instantiate annotator, try other parser {stanford, nltk, ncbo}")
                sys.exit(2)
            self.sparqlGen = SPARQLGenerator(vargs['repo'])
        else:
            sys.exit(2)

    def __isArgsValid(self, **vargs):
        """Check wheteher the arguments provided to create NLIMED instance are appropriate and correct
        """
        def __showErrorMessage():
            print(" error in calling getModelEntities(**vargs) function")
            print(" arguments are not complete or values are not correct")
            print("   - repo {%s}" % ','.join(map(str, dictArgs["repo"])))
            print("   - parser {%s}" % ','.join(map(str, dictArgs["parser"])))
            print("   - [pl  PL>1]")
            print("   - [alpha a>=0]")
            print("   - [beta b>=0]")
            print("   - [gamma g>=0]")
            print("   - [delta d>=0]")
            print(" example:")
            print("   minimum call: ")
            print("     NLIMED(repo='pmr', parser='stanford')")
            print("   complete call: ")
            print(
                "     NLIMED(repo='pmr', parser='stanford', pl=1, alpha=4, beta=0.7, gamma=0.5, delta=0.8)")
        if all(key in vargs.keys() for key in dictArgsMandatory):
            for key in dictArgsMandatory:
                if vargs[key] not in dictArgs[key]:
                    __showErrorMessage()
                    return False
            return True
        else:
            __showErrorMessage()
            return False

    def getModels(self, query, format):
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
        annotated = self.annotator.annotate(query)
        resultDict = {'vars': [], 'results': []}
        for annTerm in annotated['result']:
            sparqls = self.sparqlGen.constructSPARQL(*annTerm[0])
            for sparql in sparqls:
                sparqlResult = self.sparqlGen.runSparQL(sparql)
                resultDict['vars'] = sparqlResult['head']['vars']
                for binding in sparqlResult['results']['bindings']:
                    result = {var: binding[var]['value'] for var in binding}
                    resultDict['results'] += [result]
        if format == 'json':
            return resultDict
        elif format == 'print':
            print(resultDict['vars'])
            for result in resultDict['results']:
                for key, field in result.items():
                    print('  ' + key + ': ' + field)
                print('\n')

    def getSparql(self, query,  format):
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
        annotated = self.annotator.annotate(query)
        sparqlList = []
        for annTerm in annotated['result']:
            sparqlList += list(self.sparqlGen.constructSPARQL(*annTerm[0]))
        if format == 'json':
            return sparqlList
        elif format == 'print':
            for sparql in sparqlList:
                print(sparql)
                print('\n')

    def getAnnotated(self, query,  format):
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
        annotated = self.annotator.annotate(query)
        if format == 'json':
            return annotated
        elif format == 'print':
            print(' phrases: ' + ', '.join(annotated['phrases']))
            for result in annotated['result']:
                print(' ontologies: ')
                print('  ' + '\n  '.join(result[0]))
                print('  weight: ' + str(result[1]))
                print('\n')

    def getVerbose(self, query, format):
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
