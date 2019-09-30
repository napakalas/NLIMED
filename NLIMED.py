import sys
from QueryAnnotator import StanfordAnnotator, NLTKAnnotator, OBOLIBAnnotator
from SPARQLGenerator import SPARQLGenerator
import argparse

dictArgs = {'repo': ['pmr', 'bm', 'all'], 'parser': ['stanford', 'nltk', 'ncbo'],
            'show': ['models', 'sparql', 'annotation', 'verbose'], 'pl': 1,
            'alpha':4, 'beta':0.7, 'gamma':0.5, 'delta':0.8}
dictArgsMandatory = {'repo','parser'}
class NLIMED:
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
                print(
                    "  Error: can not instantiate annotator, try other parser {stanford, nltk, ncbo}")
            self.sparqlGen = SPARQLGenerator(vargs['repo'])
        else:
            sys.exit(2)

    def __isArgsValid(self, **vargs):
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
        annotated = self.getAnnotated(query, format)
        sparqlList = self.getSparql(query, format)
        modelList = self.getModels(query, format)
        if format == 'json':
            return {'annotated': annotated, 'sparql': sparqlList, 'models': modelList}


if sys.argv[0] == "NLIMED.py":
    def getArguments():
        parser = argparse.ArgumentParser()
        parser.add_argument('-r', '--repo', required=True,
                            help='repository name', choices=dictArgs['repo'])
        parser.add_argument('-p', '--parser', required=True,
                            help='parser tool', choices=dictArgs['parser'])
        def query_type(x):
            if x.strip() == 0:
                raise argparse.ArgumentTypeError("Query should contain words")
            return x
        parser.add_argument('-q', '--query', required=True,
                            help='query -- any text containing words', type=query_type)
        def pl_type(x):
            x = int(x)
            if x < 1:
                raise argparse.ArgumentTypeError("Minimum bandwidth is 1")
            return x
        parser.add_argument(
            '-pl', default=dictArgs['pl'], help='precision level, >=1', type=pl_type)
        parser.add_argument(
            '-s', '--show', default=dictArgs['show'][0], help='results presentation type ', choices=dictArgs['show'])



        def multiply_type(x):
            x = float(x)
            if x >= 0:
                return x
            else:
                raise argparse.ArgumentTypeError("Query should contain words")
        parser.add_argument('-a', '--alpha', default=dictArgs['alpha'], help='Minimum alpha is 0', type=multiply_type)
        parser.add_argument('-b', '--beta', default=dictArgs['beta'], help='Minimum beta is 0', type=multiply_type)
        parser.add_argument('-g', '--gamma', default=dictArgs['gamma'], help='Minimum gamma is 0', type=multiply_type)
        parser.add_argument('-d', '--delta', default=dictArgs['delta'], help='Minimum delta is 0', type=multiply_type)
        args = vars(parser.parse_args())
        args['console'] = True
        return(args)

    def getResult(**vargs):
        print('\nREPOSITORY: ' + vargs['repo'].upper())
        nlimed = NLIMED(**vargs)
        if vargs['show'] == 'models':
            nlimed.getModels(vargs['query'], 'print')
        if vargs['show'] == 'sparql':
            nlimed.getSparql(vargs['query'], 'print')
        if vargs['show'] == 'annotation':
            nlimed.getAnnotated(vargs['query'], 'print')
        if vargs['show'] == 'verbose':
            nlimed.getVerbose(vargs['query'], 'print')
    vargs = getArguments()
    if vargs['repo'] != 'all':
        getResult(**vargs)
    else:
        vargs['repo'] = 'pmr'
        getResult(**vargs)
        vargs['repo'] = 'bm'
        getResult(**vargs)
