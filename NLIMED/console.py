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
    repo = sys.argv[2]
    if repo in ['pmr','bm']:
        from NLIMED.RDFGraphIndex import  IndexSPARQL
        from NLIMED.TextFeatureIndex import IndexAnnotation
        idxSparql = IndexSPARQL(repo)
        idxSparql.buildIndex(*sys.argv)
        # create Index ANNOTATION and inverted index
        idxAnnotation = IndexAnnotation(repo)
        idxAnnotation.collectClassAttributes()
        idxAnnotation.developInvertedIndex()
    else:
        print("  error indexing")
        print("  pmr: $ NLIMED --build-index pmr")
        print('  bm : $ NLIMED --build-index bm {location-of-RDF-files}')

def getArguments():
    from NLIMED import __dictArgsOptional__, __dictArgsMandatory__, __dictDefArgsVal__
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--repo', required=True,
                        help='repository name', choices=__dictArgsMandatory__['repo'])
    parser.add_argument('-p', '--parser', required=True,
                        help='parser tool', choices=__dictArgsMandatory__['parser'])
    def query_type(x):
        if x.strip() == 0:
            raise argparse.ArgumentTypeError("Query should contain words")
        return x
    parser.add_argument('-q', '--query', required=True,
                        help='query -- any text containing words', type=query_type)
    parser.add_argument(
        '-pl', default=__dictDefArgsVal__['pl'], help='precision level, >=1', type=__dictArgsOptional__['pl'])
    parser.add_argument(
        '-s', '--show', default=__dictDefArgsVal__['show'][0], help='results presentation type ', choices=__dictArgsOptional__['show'])
    parser.add_argument(
        '-a', '--alpha', default=__dictDefArgsVal__['alpha'], help='Minimum alpha is 0', type=__dictArgsOptional__['alpha'])
    parser.add_argument(
        '-b', '--beta', default=__dictDefArgsVal__['beta'], help='Minimum beta is 0', type=__dictArgsOptional__['beta'])
    parser.add_argument(
        '-g', '--gamma', default=__dictDefArgsVal__['gamma'], help='Minimum gamma is 0', type=__dictArgsOptional__['gamma'])
    parser.add_argument(
        '-d', '--delta', default=__dictDefArgsVal__['delta'], help='Minimum delta is 0', type=__dictArgsOptional__['delta'])
    args = vars(parser.parse_args())
    args['quite'] = False
    return(args)
