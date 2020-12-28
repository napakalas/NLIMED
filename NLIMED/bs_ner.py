import pandas as pd
import sys
import urllib.request
import os

from itertools import chain

import nltk
import sklearn
import scipy.stats
from sklearn.metrics import make_scorer
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import RandomizedSearchCV

import sklearn_crfsuite
from sklearn_crfsuite import scorers
from sklearn_crfsuite import metrics

import copy

def createTrainingNer(repo, ontoFolder):
    listServers = {'pmr':['MA','CHEBI','PR','GO','OPB','FMA','CL','UBERON'],
                   'bm':['SO','PW','PSIMOD','PR','PATO','OPB','NCBITAXON','MAMO',
                    'FMA','EFO','EDAM','ECO','CL','CHEBI','BTO','SBO',
                    'UNIPROT','KEGG','EC-CODE','ENSEMBL','GO']}
    servers = listServers[repo]
    # now we only consider csv and obo files
    ontologies = {}
    for file in os.listdir(ontoFolder):
        ontoName = file[:file.rfind('.')]
        if  file.endswith('.csv') and ontoName in servers:
            file = os.path.join(ontoFolder,file)
            df = pd.read_csv(file,sep=',',header=0)
            pref = df['Preferred Label'].tolist()
            synonyms = df['Synonyms'].tolist()
            __extractNerClasses(ontologies, ontoName, pref, synonyms)
        elif file.endswith('.obo') and ontoName in servers:
            file = os.path.join(ontoFolder,file)
            f = open(file, 'r')
            lines = f.readlines()
            f.close()
            # get attributes
            pref = []
            for i in range(len(lines)):
                if lines[i] == '[Term]':
                    pref += [lines[i+2][lines[i+2].find(' ')+1:]]
                    i += 4
            __extractNerClasses(ontologies, ontoName, pref)

def __extractNerClasses(ontologies, ontoName, *features):
    ontologies[ontoName] = []
    for feature in features:
        for txts in feature:
            try:
                if isinstance(txts,str):
                    txts = txts.split('|')
                    for txt in txts:
                        terms = txt.lower().strip().split()
                        line = []
                        for i in range(len(terms)):
                            tag = 'I-'+ontoName if i==0 else 'B-'+ontoName
                            term = __cleanTerm(terms[i])
                            pair = (term,tag)
                            line += [pair]
                ontologies[ontoName] += [line]
            except:
                pass
    print(ontoName, ' ', len(ontologies[ontoName]), ' ', ontologies[ontoName][0])

def createSpellAndNerModels(repo, folder):
    spellTrain, spellTrainBigram, nerListTrain = {}, {}, []
    for file in os.listdir(folder):
        if  file.endswith('.csv'):
            ontoName = file[:file.rfind('.')]
            file = os.path.join(folder,file)
            # load ontology from csv
            df = pd.read_csv(file,sep=',',header=0)
            # store preffered label, synonym, and definition to local var
            pref = df['Preferred Label'].tolist()
            syn = df['Synonyms'].tolist()
            defi = df['Definitions'].tolist()

            # create and add model for spellchecker
            __createSpellTrains(spellTrain, spellTrainBigram, pref, syn, defi)

            # create and add model for NER
            __createNerTrain(nerListTrain, ontoName, pref)

    # create and save to Spelling models
    createAndSaveSpellingModel(spellTrain, spellTrainBigram, repo)

    # create NER models
    createAndSaveNerModel(word2features, repo+'_ner_model',nerListTrain)
    createAndSaveNerModel(word2features_prefsuf, repo+'_ner_model_prefsuf',nerListTrain)
    createAndSaveNerModel(word2features_rmvocal, repo+'_ner_model_rmvocal',nerListTrain)
    createAndSaveNerModel(word2features_pref, repo+'_ner_model_pref',nerListTrain)
    createAndSaveNerModel(word2features_suf, repo+'_ner_model_suf',nerListTrain)
    createAndSaveNerModel(word2features_combine_wo_postag, repo+'_ner_model_combine_wo_postag',nerListTrain)

def __createSpellTrains(spellTrain, spellTrainBigram, *features):
    for feature in features:
        for txts in feature:
            if isinstance(txts,str):
                txts = txts.split('|')
                for txt in txts:
                    terms = txt.lower().strip().split()
                    # update trainingSpellOneGram
                    for term in terms:
                        try:
                            term = __cleanTerm(term)
                            spellTrain[term] = spellTrain[term] + 1 if term in spellTrain else 1
                        except:
                            pass
                    # update trainingSpellBiGram
                    for i in range(len(terms)-1):
                        try:
                            term = __cleanTerm(terms[i])+' '+__cleanTerm(terms[i+1])
                            spellTrainBigram[term] = spellTrainBigram[term] + 1 if term in spellTrainBigram else 1
                        except:
                            pass

def __cleanTerm(term):
    term = term.strip()
    term = term[1:-1] if term[0]=='(' and term[-1]==')' else term
    term = term.replace('(','') if '(' in term and ')' not in term else term
    term = term.replace(')','') if '(' not in term and ')' in term else term
    while True:
        tmpTerm = term
        if term[-1] in ['.',',',';','!','?',':',"'",'"']:
            term = term[:-1]
        if term[0] in ['.',',',';','!','?',':',"'",'"']:
            term = term[1:]
        if tmpTerm == term:
            break
    return term

def __createNerTrain(nerListTrain, ontoName, *features):
    for feature in features:
        for txts in feature:
            try:
                if isinstance(txts,str):
                    txts = txts.split('|')
                    for txt in txts:
                        terms = txt.lower().strip().split()
                        line = []
                        for i in range(len(terms)):
                            tag = 'I-'+ontoName if i==0 else 'B-'+ontoName
                            term = __cleanTerm(terms[i])
                            pair = (term,tag)
                            line += [pair]
                nerListTrain += [line]
            except:
                pass

def saveModel(obj, localDir, fileName):
    import pickle
    path = os.path.dirname(os.path.realpath(__file__))
    modelFile =  os.path.join(path,localDir,fileName)
    with open(modelFile, 'wb') as f:
        pickle.dump(obj, f)

def createAndSaveNerModel(featureExtractFunc, modelFile, nerListTrain):
    # NER MODEL LABEL
    y_train = [__sent2labels(s) for s in nerListTrain]

    X_train = [__sent2features(s,featureExtractFunc) for s in nerListTrain]
    crf = sklearn_crfsuite.CRF(
        algorithm='lbfgs',
        c1=0.1,
        c2=0.1,
        max_iterations=100,
        all_possible_transitions=True
    )
    crf.fit(X_train, y_train)

    # save binary model
    saveModel(crf, 'models', modelFile)

# NER FUNCTION
def word2features(sent, i):
    word = sent[i][0]
    features = {
        'bias': 1.0,
        'word.isdigit()': word.isdigit(),
    }
    if i > 0:
        word1 = sent[i-1][0]
        features.update({
            '-1:word.isdigit()': word1.isdigit(),
        })
    if i < len(sent)-1:
        word1 = sent[i+1][0]
        features.update({
            '+1:word.isdigit()': word1.isdigit(),
        })
    return features #basic feature

def word2features_prefsuf(sent, i): #with preffix and suffix
    features = word2features(sent, i)
    word = sent[i][0]
    features.update({
        'word[-3:]': word[-3:],
        'word[-2:]': word[-2:],
        'word[+2:]': word[2:],
        'word[+3:]': word[3:],
    })
    if i > 0:
        word1 = sent[i-1][0]
        features.update({
            '-1:word[-3:]': word1[-3:],
            '-1:word[-2:]': word1[-2:],
            '-1:word[+2:]': word1[2:],
            '-1:word[+3:]': word1[3:],
        })
    if i < len(sent)-1:
        word1 = sent[i+1][0]
        features.update({
            '+1:word[-3:]': word1[-3:],
            '+1:word[-2:]': word1[-2:],
            '+1:word[+2:]': word1[2:],
            '+1:word[+3:]': word1[3:],
        })
    return features

def word2features_rmvocal(sent, i): #with removed vocal
    features = word2features(sent, i)
    word = sent[i][0]
    features.update({
        'word.rmvocal()': remove_vowel(word.lower()),
    })
    if i > 0:
        word1 = sent[i-1][0]
        features.update({
            '-1:word.rmvocal()': remove_vowel(word1.lower()),
        })
    if i < len(sent)-1:
        word1 = sent[i+1][0]
        features.update({
            '+1:word.rmvocal()': remove_vowel(word1.lower()),
        })
    return features

def word2features_pref(sent, i): #with preffix
    features = word2features(sent, i)
    word = sent[i][0]
    features.update({
        'word[+2:]': word[2:],
        'word[+3:]': word[3:],
    })
    if i > 0:
        word1 = sent[i-1][0]
        features.update({
            '-1:word[+2:]': word1[2:],
            '-1:word[+3:]': word1[3:],
        })
    if i < len(sent)-1:
        word1 = sent[i+1][0]
        features.update({
            '+1:word[+2:]': word1[2:],
            '+1:word[+3:]': word1[3:],
        })
    return features

def word2features_suf(sent, i): #with suffix
    features = word2features(sent, i)
    word = sent[i][0]
    features.update({
        'word[-3:]': word[-3:],
        'word[-2:]': word[-2:],
    })
    if i > 0:
        word1 = sent[i-1][0]
        features.update({
            '-1:word[-3:]': word1[-3:],
            '-1:word[-2:]': word1[-2:],
        })
    if i < len(sent)-1:
        word1 = sent[i+1][0]
        features.update({
            '+1:word[-3:]': word1[-3:],
            '+1:word[-2:]': word1[-2:],
        })
    return features

def word2features_combine_wo_postag(sent, i): #
    features = word2features(sent, i)
    word = sent[i][0]
    features.update({
        'word[-3:]': word[-3:],
        'word[-2:]': word[-2:],
        'word[+2:]': word[2:],
        'word[+3:]': word[3:],
        'word.rmvocal()': remove_vowel(word.lower()),
    })
    if i > 0:
        word1 = sent[i-1][0]
        features.update({
            '-1:word[-3:]': word1[-3:],
            '-1:word[-2:]': word1[-2:],
            '-1:word[+2:]': word1[2:],
            '-1:word[+3:]': word1[3:],
            '-1:word.rmvocal()': remove_vowel(word1.lower()),
        })
    if i < len(sent)-1:
        word1 = sent[i+1][0]
        features.update({
            '+1:word[-3:]': word1[-3:],
            '+1:word[-2:]': word1[-2:],
            '+1:word[+2:]': word1[2:],
            '+1:word[+3:]': word1[3:],
            '+1:word.rmvocal()': remove_vowel(word1.lower()),
        })
    return features

def remove_vowel(term):
    vowels = ('a', 'e', 'i', 'o', 'u')
    return ''.join([l for l in term if l not in vowels]);

def __sent2labels(sent):
    return [label for token, label in sent]

def __sent2features(sent, extractionFunction):
    return [extractionFunction(sent, i) for i in range(len(sent))]

""" LOAD MODEL FROM FILE """

def loadModel(localDir,fileName):
    import pickle
    path = os.path.dirname(os.path.realpath(__file__))
    modelFile =  os.path.join(path,localDir,fileName)
    with open(modelFile, 'rb') as f:
        model = pickle.load(f)
    return model

def getNerResult(modelFile, extractionFunction, query):
    nerModel = loadModel('models',modelFile)
    listQuery = [[[term] for term in query.split()]]
    X_test = [__sent2features(s,extractionFunction) for s in listQuery]
    labels = list(nerModel.classes_)
    y_pred = nerModel.predict(X_test)
    print(y_pred)

"""SPELL CHECKER FUNCTION"""
from cc.symspellpy import SymSpell, Verbosity  # import the module

def createAndSaveSpellingModel(spellTrain, spellTrainBigram, repo):

    def __saveSpellingModel(dct, file):
        path = os.path.dirname(os.path.realpath(__file__))
        file =  os.path.join(path,'tmp',file)
        f = open(file, 'w+')
        dct = dict((k,v) for (k,v) in dct.items() if v > 1)
        for key, val in dct.items():
            string = key+' '+str(val)
            try:
                f.write(string+'\n')
            except:
                pass
        f.close()
    __saveSpellingModel(spellTrain,repo+'_freq_dict.txt')
    __saveSpellingModel(spellTrainBigram,repo+'_freq_dict_bigram.txt')

    # maximum edit distance per dictionary precalculation
    max_edit_distance_dictionary = 2
    prefix_length = 7
    # create object
    sym_spell = SymSpell(max_edit_distance_dictionary, prefix_length)
    # load dictionary
    path = os.path.dirname(os.path.realpath(__file__))
    dictionary_path =  os.path.join(path,'tmp',repo+'_freq_dict.txt')
    bigram_path = os.path.join(path,'tmp',repo+'_freq_dict_bigram.txt')
    sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
    sym_spell.load_bigram_dictionary(bigram_path, term_index=0, count_index=2)
    sym_spell.save_pickle(os.path.join(path,'models',repo+'_spell_model'),compressed=True)

def spellCheker(modelFile, input_term):
    sym_spell = loadModel('models',modelFile)
    max_edit_distance_lookup = 2
    suggestions = sym_spell.lookup_compound(input_term,
                                            max_edit_distance_lookup)
    for suggestion in suggestions:
        print("1. {}, {}, {}".format(suggestion.term, suggestion.distance,
                                  suggestion.count))

    result = sym_spell.word_segmentation(input_term)
    # display suggestion term, term frequency, and edit distance
    print("2. {}, {}, {}".format(result.corrected_string, result.distance_sum,
                              result.log_prob_sum))

    suggestion_verbosity = Verbosity.CLOSEST  # TOP, CLOSEST, ALL
    suggestions = sym_spell.lookup(input_term, suggestion_verbosity,
                                   max_edit_distance_lookup)
    # display suggestion term, term frequency, and edit distance
    for suggestion in suggestions:
        print("3. {}, {}, {}".format(suggestion.term, suggestion.distance,
                                  suggestion.count))


createTrainingNer('pmr','/Users/ymun794/Documents/Ontologies')

# createSpellAndNerModels('pmr','/Users/ymun794/Documents/Ontologies')

# spellCheker('pmr_spell_model', 'portionofcytosol')

# query = '(2s,3s,4r)-4-(hydroxymethyl)-1-(2-methoxy-1-oxoethyl)-3-[4-(3-pyridinyl)phenyl]-2-azetidinecarbonitr'
#
# mySpellChecker = SymSpell()
# path = os.path.dirname(os.path.realpath(__file__))
# #
# mySpellChecker.load_pickle(os.path.join(path,'models','pmr_spell_model'),compressed=True)
# result = mySpellChecker.word_segmentation(query)
# print(result.corrected_string)
#
# suggestions = mySpellChecker.lookup_compound(query,1)
# for suggestion in suggestions:
#     print("{}, {}, {}".format(suggestion.term, suggestion.distance,
#                               suggestion.count))
# suggestions = mySpellChecker.lookup_compound(query,2)
# for suggestion in suggestions:
#     print("{}, {}, {}".format(suggestion.term, suggestion.distance,
#                               suggestion.count))
#
# suggestions = mySpellChecker.lookup(query, Verbosity.CLOSEST, 1)
# for suggestion in suggestions:
#     print("{}, {}, {}".format(suggestion.term, suggestion.distance,
#                               suggestion.count))
