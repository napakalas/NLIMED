"""MODUL: ANNOTATION"""
import operator
import math
import json
from nltk.corpus import stopwords
from abc import ABCMeta, abstractmethod, ABC
import Settings

class Annotator(ABC):
    totSubject = int
    inv_index = {}
    idx_id_object = {}
    topConsider = int

    def __init__(self, topConsider, **settings):
        self.m_prefDef = 4
        self.m_synonym = 0.7
        self.m_definition = 0.5
        self.m_mention = 0.8
        with open('inv_index', 'r') as fp:
            Annotator.inv_index = json.load(fp)
        with open('idx_id_object', 'r') as fp:
            Annotator.idx_id_object = json.load(fp)
        Annotator.totSubject = len(Annotator.idx_id_object)
        Annotator.topConsider = topConsider
        if len(settings) > 0:
            self.m_prefDef = settings['m_prefDef']
            self.m_synonym = settings['m_synonym']
            self.m_definition = settings['m_definition']
            self.m_mention = settings['m_mention']

    def __getPossibleObo(self,phrase):
        if isinstance(phrase[0],tuple): # this is for tree from nltk
            tmpPhrase = []
            for pair in phrase:
                tmpPhrase += [pair[0]]
            phrase = tmpPhrase
        phrase = [w for w in phrase if not w in stopwords.words('english')]
        w_prefDef = {}
        w_synonym = {}
        w_definition = {}
        w_mention = {}
        numOfToken = 0
        candidate = {}
        for token in phrase:
            if token in Annotator.inv_index:
                numOfToken += 1
                for key, val in Annotator.inv_index[token].items():
                    if key not in w_prefDef:
                        w_prefDef[key] = [(val[0],val[1])]
                        w_synonym[key] = [(val[2],val[3])]
                        w_definition[key] = [(val[4],val[5],len(Annotator.inv_index[token]))]
                        w_mention[key] = [(val[6],val[7],val[8])]
                    else:
                        w_prefDef[key] += [(val[0],val[1])]
                        w_synonym[key] += [(val[2],val[3])]
                        w_definition[key] += [(val[4],val[5],len(Annotator.inv_index[token]))]
                        w_mention[key] += [(val[6],val[7],val[8])]
        for oboId in  w_prefDef:
            candidate[oboId] = 0
            for app, ln in w_prefDef[oboId]:
                candidate[oboId] += self.m_prefDef * app / (ln + numOfToken)
            for app, ln in w_synonym[oboId]:
                candidate[oboId] += self.m_synonym * app / (ln + numOfToken)
            for app, ln, lnInv in w_definition[oboId]:
                candidate[oboId] += self.m_definition * app / (ln + numOfToken) / lnInv
            for freq, docLen, totSbj in w_mention[oboId]:
                candidate[oboId] += self.m_mention * freq / (docLen + numOfToken) * math.log(Annotator.totSubject/(Annotator.totSubject-totSbj))
        phrase = " ".join(map(str,phrase))
        candidate = sorted(candidate.items(), key=operator.itemgetter(1), reverse=True)
        maxValue = candidate[0][1] if len(candidate) > 0 else 0
        #choose best considered
        if len(candidate)-1 > Annotator.topConsider:
            candidate=candidate[0:Annotator.topConsider]
        return {'phrase':phrase,'candidate':candidate,'maxValue':maxValue}

    def _getObos(self, tree):
        hasAnnotated = {}
        control = {}
        childParent = {}
        """Calculate weight of all possible subtree"""
        for subtree in tree.subtrees(filter=None):
            if subtree.label() == 'NP':
                pos = subtree.treeposition()
                entity = self.__getPossibleObo(subtree.leaves())
                parentEntity = subtree.parent()
                while parentEntity.label() != 'ROOT' and parentEntity.label() != 'NP' and parentEntity.label() != 'S':
                    parentEntity = parentEntity.parent();
                posParent = parentEntity.treeposition()
                if entity['phrase'] not in control:
                    hasAnnotated[pos] = entity
                    control[entity['phrase']] = pos
                    childParent[pos] = posParent
                elif not all(control[entity['phrase']][i] == pos[i] for i in range(len(control[entity['phrase']]))):
                    hasAnnotated[pos] = entity
                    control[entity['phrase']] = pos
                    childParent[pos] = posParent
        """remove all parents having smaller weight than child"""
        for subtree in tree.subtrees(filter=None):
            pos = subtree.treeposition()
            if subtree.label() == 'NP' and pos in childParent:
                parentPos = childParent[pos]
                if parentPos in hasAnnotated:
                    if hasAnnotated[pos]['maxValue'] > hasAnnotated[parentPos]['maxValue']:
                        hasAnnotated.pop(parentPos)
                        childParent.pop(parentPos)
        """remove all child having smaller weight than parent"""
        for pos, parentPos in childParent.items():
            if pos in hasAnnotated and parentPos in hasAnnotated:
                hasAnnotated.pop(pos)
        """get list of phrases"""
        phrases = []
        for pos in hasAnnotated:
            phrases += [hasAnnotated[pos]['phrase']]
        """remove phrase that do not have annotation"""
        for pos in childParent:
            if pos in hasAnnotated:
                if len(hasAnnotated[pos]['candidate']) == 0:
                    hasAnnotated.pop(pos)
        """get combination of all annotation"""
        bestCombination = self.__getBestCombination(hasAnnotated)
        """reverse each combination"""
        for comb in bestCombination:
            comb[0] = comb[0][::-1]
        return {'phrases':phrases,'result':bestCombination}

    def __getBestCombination(self,hasAnnotated):
        termNum = len(hasAnnotated)
        count = 0
        multiplier = 2
        if termNum>1:
            key = list(hasAnnotated.keys())[0]
            newAnnotated = hasAnnotated.copy()
            newAnnotated.pop(key)
            prevCombinations = self.__getBestCombination(newAnnotated)
            newList = []
            for prevCombination in prevCombinations:
                candidates = hasAnnotated[key]['candidate']
                for oboClassId, val in candidates:
                    prevCombList = prevCombination[0]
                    prevCombVal = prevCombination[1]
                    if oboClassId in prevCombList:
                        currVal = prevCombVal + multiplier*val
                        currCombList = prevCombList
                    else:
                        currVal = prevCombVal + val
                        currCombList = prevCombList+[oboClassId]
                    newList+=[[currCombList,currVal]]
            return newList
        elif termNum==1:
            key = list(hasAnnotated.keys())[0]
            candidates = hasAnnotated[key]['candidate']
            newList = []
            for oboClassId, val in candidates:
                data = [[[oboClassId],val]]
                newList += data
            return sorted(newList,key=operator.itemgetter(1),reverse=True)
        else:
            return []

    def printAnnotated(self, result):
        print(result['phrases'])
        for pairs in result['result']:
            for pair in pairs[0]:
                print('\t'+str(pair))
            print('\t'+str(pairs[1]))

    @abstractmethod
    def annotate(self, tree):
        pass
    @abstractmethod
    def getTree(self, tree):
        pass

from nltk.parse.corenlp import CoreNLPServer
import os
from  nltk.parse.corenlp  import CoreNLPParser
from nltk.tree import ParentedTree
import string
import urllib.request
class StanfordAnnotator(Annotator):
    serverIsStarted = False
    STANFORD = os.path.join(".", "stanford-corenlp-full-2018-10-05")
    server = CoreNLPServer(
       os.path.join(STANFORD, "stanford-corenlp-3.9.2.jar"),
       os.path.join(STANFORD, "stanford-english-corenlp-2018-10-05-models.jar"),
    )

    def __init__(self, topConsider, **settings):
        super(StanfordAnnotator, self).__init__(topConsider, **settings)
        if StanfordAnnotator.serverIsStarted == False:
            # check whether the http server is up or not
            try:
                connectionStatus = urllib.request.urlopen("http://localhost:9000").getcode()
                if connectionStatus == 200:
                    print('Server has been started')
                    StanfordAnnotator.serverIsStarted = True
            except:
                try:
                    # Start the server in the background
                    StanfordAnnotator.server.start()
                    StanfordAnnotator.serverIsStarted = True
                except:
                    print('Server can not be started')

    def stopServer(self):
        StanfordAnnotator.server.stop()
        StanfordAnnotator.serverIsStarted = False

    def getTree(self, query):
        query = query.translate(str.maketrans(string.punctuation, ' '*len(string.punctuation))).lower()
        parser = CoreNLPParser()
        return ParentedTree.convert(next(parser.raw_parse(query)))

    def annotate(self, query):
        tree = self.getTree(query)
        return self._getObos(tree)

from nltk.corpus import stopwords
import nltk
import string
from nltk.tree import ParentedTree
from nltk.tokenize import RegexpTokenizer

class NLTKAnnotator(Annotator):
    def __init__(self, topConsider, **settings):
        super(NLTKAnnotator, self).__init__(topConsider, **settings)

    def getTree(self, query):
        query = query.translate(str.maketrans(string.punctuation, ' '*len(string.punctuation))).lower()
        # Used when tokenizing words
        sentence_re = r"""
                (?x)                # set flag to allow verbose regexps
                (?:[A-Z]\.)+        # abbreviations, e.g. U.S.A.
              | \w+(?:-\w+)*        # words with optional internal hyphens
              | \$?\d+(?:\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
              | \.\.\.              # ellipsis
              | [][.,;"'?():_`-]    # these are separate tokens;
        """
        #Taken from Su Nam Kim Paper...
        grammar = r"""
            NBAR:
                {<NN.*|JJ>*<NN.*|NNS.*>}  # Nouns and Adjectives, terminated with Nouns
            NP:
                {<DT><VBG><NBAR>} #Add by me
                {<NBAR><CD><NBAR>} #Add by me
                {<NBAR><CD>} #Add by me
                {<NBAR>}
                {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
        """
        chunker = nltk.RegexpParser(grammar)
        tokenizer = RegexpTokenizer(r'\w+')
        toks = tokenizer.tokenize(query.lower())
        postoks = nltk.tag.pos_tag(toks)
        return ParentedTree.convert(chunker.parse(postoks))

    def annotate(self, query):
        tree = self.getTree(query)
        return self._getObos(tree)

import requests
class OBOLIBAnnotator(Annotator):
    def __init__(self, topConsider):
        super(OBOLIBAnnotator, self).__init__(topConsider)
        apikey = '?apikey='+Settings.apikey
        ontologies = '&ontologies=MA,CHEBI,PR,GO,OPB,FMA,CL,UBERON'
        synonym = '&exclude_synonyms=false'
        whole_word_only = '&whole_word_only=true'
        exclude_numbers = '&exclude_numbers=false'
        longest_only = '&longest_only=true'
        self.__server = 'http://data.bioontology.org/annotator'+apikey+ontologies+synonym+whole_word_only+exclude_numbers+longest_only+'&text='

    def getTree(self,query):
        pass

    def annotate(self,query):
        r = requests.get(self.__server+query)
        results = r.json()
        if len(results)>0:
            selects = []
            # print(r.status_code)
            for i in range(len(results)):
                res = results[i]
                oboId = res['annotatedClass']['@id']
                annotations = res['annotations']
                for j in range(len(annotations)):
                    annot = annotations[j]
                    if j == 0:
                        v_from = int(annot['from'])
                        v_to = int(annot['to'])
                        v_text = annot['text']
                    else:
                        v_from = int(annot['from']) if int(annot['from']) < v_from else v_from
                        v_to = int(annot['to']) if int(annot['to']) > v_to else v_to
                        v_text = annot['text'] +' '+ v_text if int(annot['from']) < v_from else v_text
                        v_text += ' ' + annot['text'] if int(annot['to']) > v_to else v_text
                    v_len = v_to - v_from
                if i == 0:
                    selects += [{'oboId':oboId,'from':v_from,'to':v_to,'len':v_len,'text':v_text}]
                else:
                    prevSelect = selects[len(selects)-1]
                    if prevSelect['from'] >= v_from and prevSelect['to'] <= v_to and prevSelect['len'] < v_len:
                        prevSelect['from'] = v_from
                        prevSelect['to'] = v_to
                        prevSelect['len'] = v_len
                        prevSelect['text'] = v_text
                        prevSelect['oboId'] = oboId
                    elif prevSelect['from'] == v_from and prevSelect['to'] == v_to and prevSelect['oboId'] != oboId:
                        if 'fma' in oboId:
                            prevSelect['oboId'] = oboId
                        elif 'fma' not in prevSelect['oboId']:
                            prevSelect['oboId'] = oboId
                    elif prevSelect['to'] < v_from:
                        selects += [{'oboId':oboId,'from':v_from,'to':v_to,'len':v_len,'text':v_text}]
        phrases = []
        result = []
        for sel in selects:
            phrases += [sel['text']]
            result += [sel['oboId']]
        return {'phrases':phrases,'result':[[result,1]]}
