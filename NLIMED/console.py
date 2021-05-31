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
    elif '--download' in sys.argv:
        downloadData()
    elif '--build-index' in sys.argv:
        buildIndex()
    elif '--hyperparam' in sys.argv:
        hyperparam()
    else:
        getArguments()

def runApp():
    from nlimed.nlimed import nlimed
    def getResult(**vargs):
        print('\nREPOSITORY: ' + vargs['repo'].upper())
        nlimed = nlimed(**vargs)
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
        if sys.argv.index("--apikey")+1 < len(sys.argv) and sys.argv.index("--corenlp-home")+1 < len(sys.argv):
            apikey = sys.argv[sys.argv.index("--apikey")+1]
            corenlp_home = sys.argv[sys.argv.index("--corenlp-home")+1]
            from nlimed.nlimed import config
            config(parsers={'ncbo':apikey, 'coreNLP':corenlp_home})
            print("  configuration succeed")
        else:
            print("  error config")
            print("  example: $ nlimed --config --apikey {your-ncbo-api-key} --corenlp-home {CoreNLP-folder}")
    else:
        print("  error config")
        print("  example: $ nlimed --config --apikey {your-ncbo-api-key} --corenlp-home {CoreNLP-folder}")

def downloadData():
    download()

def buildIndex():
    repo = sys.argv[2]
    ontologies = sys.argv[3]

    if repo in ['pmr', 'bm', 'bm-omex']:
        from nlimed.rdf_graph_index import  IndexSPARQL
        from nlimed.text_feature_index import IndexAnnotation
        idxSparql = IndexSPARQL(repo)
        idxSparql.buildIndex(*sys.argv)
        # create Index ANNOTATION and inverted index
        idxAnnotation = IndexAnnotation(repo, ontologies)
        idxAnnotation.collectClassAttributes()
        idxAnnotation.developInvertedIndex()
    else:
        print("  error indexing")
        print('  pmr: $ nlimed --build-index pmr "{location-of-ontology-files}"')
        print('  bm : $ nlimed --build-index bm "{location-of-ontology-files}" "{location-of-RDF-files}"')

def hyperparam():
    """ generate hyperparameter and save it in Files
        input: - repository
               - dataTrainZile
               - precAt -> maximum of precAt
               - preff/header file to be saved
               - destination folder
               - parser
        how to run: nlimed --hyperparam pmr "DataTest" 9 pure "dest" CoreNLP
    """
    repo = sys.argv[2]
    datatTrainFile = sys.argv[3]
    precAt = int(sys.argv[4])
    preffix = sys.argv[5]
    destination = sys.argv[6]
    parser = sys.argv[7]
    from nlimed.nlimed import nlimed
    nli = nlimed(repo=repo, parser=parser)
    stats = nli.hyperparam(datatTrainFile, precAt)
    import json, time
    filename = destination+preffix+"_"+str(precAt) + "_" + parser+ "_" + str(time.time()) + ".json"
    with open(filename, 'w') as fp:
        json.dump(stats, fp)

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
    parser.add_argument(
        '-t', '--theta', default=__dictDefArgsVal__['theta'], help='Minimum theta is 0', type=__dictArgsOptional__['theta'])
    parser.add_argument(
        '-c', '--cutoff', default=__dictDefArgsVal__['cutoff'], help='Minimum cutoff is 0', type=__dictArgsOptional__['cutoff'])
    parser.add_argument(
        '-tf', '--tfMode', default=__dictDefArgsVal__['tfMode'], help='tf mode calculation, [1,2,3]', type=__dictArgsOptional__['tfMode'])
    args = vars(parser.parse_args())
    args['quite'] = False
    return(args)
