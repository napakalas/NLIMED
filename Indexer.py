from RDFGraphIndex import  IndexSPARQL
from TextFeatureIndex import IndexAnnotation
import argparse

if sys.argv[0] == "NLIMED.py":
    def getArguments():
        parser = argparse.ArgumentParser()
        parser.add_argument('-r', '--repo', required=True,
                            help='repository name', choices=['pmr','bm'])

    vargs = getArguments()
    # create Index SPARQL
    idxSparql = IndexSPARQL(vargs['repo'],'build')
    idxSparql.buildIndex()
    # create Index ANNOTATION and inverted index
    idxAnnotation = IndexAnnotation(vargs['repo'])
    idxAnnotation.collectClassAttributes()
    idxAnnotation.developInvertedIndex()
