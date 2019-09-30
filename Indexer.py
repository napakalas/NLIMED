import sys
from RDFGraphIndex import  IndexSPARQL
from TextFeatureIndex import IndexAnnotation
import argparse


if sys.argv[0] == "Indexer.py":
    def getArguments():
        parser = argparse.ArgumentParser()
        parser.add_argument('-r', '--repo', required=True,
                            help='repository name', choices=['pmr','bm'])
        args = vars(parser.parse_args())
        return(args)

    vargs = getArguments()
    # create Index SPARQL
    idxSparql = IndexSPARQL(vargs['repo'])
    idxSparql.buildIndex('-build')
    # create Index ANNOTATION and inverted index
    idxAnnotation = IndexAnnotation(vargs['repo'])
    idxAnnotation.collectClassAttributes()
    idxAnnotation.developInvertedIndex()
