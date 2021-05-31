"""GENERAL CLASS: performing method used by all classes"""

from abc import ABCMeta, abstractmethod, ABC
import json
import os
import requests
from nltk.corpus import stopwords
from nltk.tree import ParentedTree
from SPARQLWrapper import SPARQLWrapper, JSON, BASIC, POST
import copy
import rdflib
from shutil import copyfile
import pickle
import gzip
import stanza
from nltk.tokenize import RegexpTokenizer

class GeneralNLIMED(ABC):
    def __init__(self):
        self.currentPath = os.path.dirname(os.path.realpath(__file__))
        self.apikey = 'no-api-key'
        self.corenlp_home = '/'
        self.corenlp_ep = 'http://localhost:9001'
        try:
            config = self._loadJson("config.txt")
            if 'ncbo' in config:
                self.apikey = config['ncbo']
            if 'coreNLP' in config:
                self.corenlp_home = config['coreNLP']
                self.corenlp_ep = config['coreNLP_EP']
        except:
            pass
        self.oboUrl = "http://data.bioontology.org/ontologies/"

    def _loadJson(self, *paths):
        file = os.path.join(self.currentPath,*paths)
        isExist = os.path.exists(file)
        if isExist:
            with open(file, 'r') as fp:
                data = json.load(fp)
            return data
        else:
            return {}

    def _dumpJson(self, data, *paths):
        file = os.path.join(self.currentPath,*paths)
        with open(file, 'w') as fp:
            json.dump(data, fp)

    def _saveToFlatFile(self, data, *paths):
        file = os.path.join(self.currentPath,*paths)
        f = open(file, 'w+')
        for datum in data:
            f.write(str(datum).replace('\n', ' ').replace('\r', ' ') + '\n')
        f.close()

    def _loadFromFlatFile(self, *paths):
        file = os.path.join(self.currentPath,*paths)
        try:
            f = open(file, 'r')
            lines = f.readlines()
            f.close()
            return lines
        except:
            return []

    def _saveBinaryInteger(self, data, *paths):
        import struct
        file = os.path.join(self.currentPath,*paths)
        with open(file, "wb") as f:
            for x in data:
                f.write(struct.pack('i', x))  # 4bytes

    def _loadBinaryInteger(self, *paths):
        import struct
        file = os.path.join(self.currentPath,*paths)
        with open(file, 'rb') as f:
            bdata = []
            while True:
                bytes = f.read(4)
                if bytes == b'':
                    break
                else:
                    bdata.append(struct.unpack('i', bytes)[0])  # 4bytes
        return bdata

    def _copyToIndexes(self, files):
        for file in files:
            src = os.path.join(self.currentPath, 'tmp', file)
            dst = os.path.join(self.currentPath, 'indexes', file.replace('_selected',''))
            if os.path.exists(src):
                copyfile(src, dst)

    def dumpPickle(self, data, *paths):
        filename = os.path.join(self.currentPath, *paths)
        file = gzip.GzipFile(filename, 'wb')
        pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)
        file.close()

    def loadPickle(self, *paths):
        filename = os.path.join(self.currentPath, *paths)
        file = gzip.GzipFile(filename, 'rb')
        data = pickle.load(file)
        file.close()
        return data

    def getAllFilesInDir(self, *paths):
        drc = os.path.join(self.currentPath, *paths)
        lst = []
        for path, subdirs, files in os.walk(drc):
            for name in files:
                lst += [os.path.join(path, name)]
        return lst

    def _getURICode(self, uri):
        # function to get ontology class ID rather than full url
        import re
        partUri = uri[uri.rfind('/')+1:].lower()
        regex = re.compile('[^a-z0-9]')
        partUri = regex.sub('', partUri)
        return partUri

class GeneralNLP():
    __tokenizer = RegexpTokenizer(r'\w+')
    nlp = stanza.Pipeline('en' , package='craft', processors={'ner': 'BioNLP13CG'},verbose=False)
    def __init__(self):
        pass

    def getDictDeepDependency(self, phrase, getLemma=False):
        """ This function is to extract the intention position of words in sentences
            For example, 'version of hexokinase activity' will return
            {'version': 1.0, 'of': 3.0, 'hexokinase': 3.0, 'activity': 2.0}
            where version is the root, activity is version's child, and of and
            hexokinase are the children of activity
            Input:  - phrase: any text, can be a string or a list
                    - getLemma: if false will return original text, otherwise lemma
            Output: - a dictionary, k = word text/lemma : v = deep position
        """
        # convert input phrase into string when it is a list
        if isinstance(phrase, list):
            phrases = phrase;
            for i, phrase in enumerate(phrases):
                phrases[i] = phrase.strip()[:-1] if phrase.strip().endswith('.') else phrase.strip()
            phrase = '\n\n'.join(phrases) # using \n\n to make sure sentence separation
        else:
            phrase = phrase.strip()[:-1] if phrase.strip().endswith('.') else phrase.strip()
        # proceed when the phrase length is not 0
        if len(phrase.strip()) > 0:
            doc = self.nlp(phrase)
            docSentences = []
            # execute each sentence.
            for sentence in doc.sentences:
                # convert sentence into dictionary so it easy to handle
                docPhrase = {word['id']: word for word in sentence.to_dict()}
                listDel = []
                # imagine the sentence has tree structure, now get the leaves
                leaves = docPhrase.copy()
                for word in docPhrase.values(): listDel+=[word['head']]
                for delId in listDel:
                    if delId in leaves: del leaves[delId]
                # tracing from leaf to root and save it as deep position from root
                for leaf in leaves.values():
                    deepToRoot = [leaf['id']]
                    curr = leaf
                    while curr['head'] != 0:
                        curr = docPhrase[curr['head']]
                        # add parent at the front of child
                        deepToRoot.insert(0, curr['id'])
                    for i in range(len(deepToRoot)):
                        docPhrase[deepToRoot[i]]['deep'] = i + 1
                docSentences += [docPhrase]
            wordDeep = {}
            # summarise the result so it return word and deep position
            for sentence in docSentences:
                for word in sentence.values():
                    # selecting whether returning original text or lemma
                    text = word['lemma'] if getLemma==True else word['text']
                    if text.lower() in wordDeep:
                        wordDeep[text.lower()] += [word['deep']]
                    else:
                        wordDeep[text.lower()] = [word['deep']]
            for word in wordDeep.copy():
                if word in stopwords.words('english'): wordDeep.pop(word); continue
                wordDeep[word] = round(sum(wordDeep[word])/len(wordDeep[word]),1)
            return wordDeep
        else:
            return {}

    def stopAndToken(self, text):
        tokens = self.tokenise(text)
        filtered_sentence = [t for t in tokens if t not in stopwords.words('english')]
        return filtered_sentence

    def tokenise(self, text):
        if len(text.strip()) == 0: return []
        doc = self.nlp(text)
        tokens = [token.text.lower() for sentence in doc.sentences for token in sentence.tokens]
        return tokens
