import sys
from QueryAnnotator import StanfordAnnotator,NLTKAnnotator,OBOLIBAnnotator
from SPARQLGenerator import SPARQLGenerator

def showErrorMessage():
    print("incorrect format, should be:")
    print("python NLIMED.py parserType query")
    print("valid parserType: -stanford, -nltk, -obo")
    print("example:")
    print("python NLIMED.py -stanford 'flux of sodium'")

if len(sys.argv) < 3:
    showErrorMessage()
elif sys.argv[1] not in ('-stanford','-nltk','-obo'):
    showErrorMessage()
else:
    print('QUERY: %s'%sys.argv[2])
    if sys.argv[1] == '-stanford':
        annotator = StanfordAnnotator(1)
    elif sys.argv[1] == '-nltk':
        annotator = NLTKAnnotator(1)
    elif sys.argv[1] == '-obo':
        annotator = OBOLIBAnnotator(1)
    sg = SPARQLGenerator()
    annResult = annotator.annotate(sys.argv[2])
    print('ANNOTATE: %s'%', '.join(annResult['phrases']))
    print('CLASSES: %s'%', '.join(annResult['result'][0][0]))
    if len(annResult) > 0:
        annTerm = annResult['result'][0]
        sparqlSet = sg.constructSPARQL(*annTerm[0])
        for sparql in sparqlSet:
            print('###################################')
            print(sparql)
            print('###################################')
            results = sg.runSparQL(sparql)
            sg.print_results(results,'flat')
            print('\n')
