# Running NLIMED from terminal
import sys
import os
import json
import argparse

def runTerminal():
    if any(arg in ['-r','--repo','-p','--parser','-q','--query'] for arg in sys.argv):
        runApp()
    elif '--config' in sys.argv:
        setupSystem()
    elif '--build-index' in sys.argv:
        buildIndex()
    else:
        getArguments()

def runApp():
    from NLIMED.NLIMED import NLIMED
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

def setupSystem():
    #config NLIMED
    if all(key in sys.argv for key in ["--apikey","--corenlp-home"]):
        if sys.argv.index("--apikey") < len(sys.argv)-1 and sys.argv.index("--corenlp-home") < len(sys.argv)-1:
            file = os.path.join(os.path.dirname(os.path.realpath(__file__)),"config.txt")
            #setup apikey NCBO and coreNLP home
            config = {"apikey":sys.argv[sys.argv.index("--apikey")+1],"corenlp-home":sys.argv[sys.argv.index("--corenlp-home")+1]}
            with open(file, 'w') as fp:
                json.dump(config, fp)
                print("  configuration succeed")
    else:
        print("  error config")
        print("  example: $ NLIMED --config --apikey {your-ncbo-api-key} --corenlp-home {CoreNLP-folder}")

def buildIndex():
    repo = sys.argv[-1]
    if repo in ['pmr','bm']:
        from NLIMED.RDFGraphIndex import  IndexSPARQL
        from NLIMED.TextFeatureIndex import IndexAnnotation
        idxSparql = IndexSPARQL(repo)
        idxSparql.buildIndex('-build')
        # create Index ANNOTATION and inverted index
        idxAnnotation = IndexAnnotation(repo)
        idxAnnotation.collectClassAttributes()
        idxAnnotation.developInvertedIndex()
    else:
        print("  error indexing")
        print("  pmr: $ NLIMED --corenlp-home pmr")
        print("  bm : $ NLIMED --corenlp-home bm")

def getArguments():
    dictArgs = {'repo': ['pmr', 'bm', 'all'], 'parser': ['stanford', 'nltk', 'ncbo'],
                'show': ['models', 'sparql', 'annotation', 'verbose'], 'pl': 1,
                'alpha': 4, 'beta': 0.7, 'gamma': 0.5, 'delta': 0.8}
    dictArgsMandatory = {'repo', 'parser'}
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
        raise argparse.ArgumentTypeError("Minimum multiplier is 0")
    parser.add_argument(
        '-a', '--alpha', default=dictArgs['alpha'], help='Minimum alpha is 0', type=multiply_type)
    parser.add_argument(
        '-b', '--beta', default=dictArgs['beta'], help='Minimum beta is 0', type=multiply_type)
    parser.add_argument(
        '-g', '--gamma', default=dictArgs['gamma'], help='Minimum gamma is 0', type=multiply_type)
    parser.add_argument(
        '-d', '--delta', default=dictArgs['delta'], help='Minimum delta is 0', type=multiply_type)
    args = vars(parser.parse_args())
    args['console'] = True
    return(args)
