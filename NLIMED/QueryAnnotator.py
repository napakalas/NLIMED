"""MODUL: ANNOTATION"""
import nltk
from nltk.tokenize import RegexpTokenizer
import urllib.request
from nltk.parse.corenlp import CoreNLPParser
import operator
import math
import string
from NLIMED.Settings import *
from nltk.parse.corenlp import CoreNLPServer

class Annotator(GeneralNLIMED):

    def __init__(self, **settings):
        super(Annotator, self).__init__()
        # setting multipliers values (alpha, betha, gamma, delta)
        self.m_prefDef = settings['alpha'] if 'alpha' in settings else 4
        self.m_synonym = settings['beta'] if 'beta' in settings else 0.7
        self.m_definition = settings['gamma'] if 'gamma' in settings else 0.5
        self.m_mention = settings['delta'] if 'delta' in settings else 0.8
        self.topConsider = settings['pl'] if 'pl' in settings else 1
        if settings['repo'] == 'pmr':
            self.inv_index = self._loadJson('indexes/inv_index')
            self.idx_id_object = self._loadJson('indexes/idx_id_object')
        elif settings['repo'] == 'bm':
            self.inv_index = self._loadJson('indexes/BM_inv_index')
            self.idx_id_object = self._loadJson('indexes/BM_selected_object.json')
        self.totSubject = len(self.idx_id_object)

    def __getPossibleObo(self, phrase):
        if isinstance(phrase[0], tuple):  # this is for tree from nltk
            tmpPhrase = []
            for pair in phrase:
                tmpPhrase += [pair[0]]
            phrase = tmpPhrase
        phrase = [w for w in phrase if not w in stopwords.words('english')]
        w_prefDef, w_synonym, w_definition, w_mention, candidate, numOfToken = {}, {}, {}, {}, {}, 0
        for token in phrase:
            if token in self.inv_index:
                numOfToken += 1
                for key, val in self.inv_index[token].items():
                    w_prefDef[key] = w_prefDef[key] + \
                        [(val[0], val[1])] if key in w_prefDef else [
                        (val[0], val[1])]
                    w_synonym[key] = w_synonym[key] + \
                        [(val[2], val[3])] if key in w_synonym else [
                        (val[2], val[3])]
                    w_definition[key] = w_definition[key] + [(val[4], val[5], len(
                        self.inv_index[token]))] if key in w_definition else [(val[4], val[5], len(self.inv_index[token]))]
                    w_mention[key] = w_definition[key] + [
                        (val[6], val[7], val[8])] if key in w_mention else [(val[6], val[7], val[8])]
        for oboId in w_prefDef:
            candidate[oboId] = sum(
                self.m_prefDef * app / (ln + numOfToken) for app, ln in w_prefDef[oboId])
            candidate[oboId] += sum(self.m_synonym * app / (ln + numOfToken)
                                    for app, ln in w_synonym[oboId])
            candidate[oboId] += sum(self.m_definition * app / (ln + numOfToken) /
                                    lnInv for app, ln, lnInv in w_definition[oboId])
            candidate[oboId] += sum(self.m_mention * freq / (docLen + numOfToken) * math.log(
                self.totSubject / (self.totSubject - totSbj)) for freq, docLen, totSbj in w_mention[oboId])
        phrase = " ".join(map(str, phrase))
        candidate = sorted(candidate.items(),
                           key=operator.itemgetter(1), reverse=True)
        maxValue = candidate[0][1] if len(candidate) > 0 else 0
        # choose best considered
        if len(candidate) - 1 > self.topConsider:
            candidate = candidate[0:self.topConsider]
        return {'phrase': phrase, 'candidate': candidate, 'maxValue': maxValue}

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
                    parentEntity = parentEntity.parent()
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
        return {'phrases': phrases, 'result': bestCombination}

    def __getBestCombination(self, hasAnnotated):
        termNum = len(hasAnnotated)
        count = 0
        multiplier = 2
        if termNum > 1:
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
                        currVal = prevCombVal + multiplier * val
                        currCombList = prevCombList
                    else:
                        currVal = prevCombVal + val
                        currCombList = prevCombList + [oboClassId]
                    newList += [[currCombList, currVal]]
            return newList
        elif termNum == 1:
            key = list(hasAnnotated.keys())[0]
            candidates = hasAnnotated[key]['candidate']
            newList = []
            for oboClassId, val in candidates:
                data = [[[oboClassId], val]]
                newList += data
            return sorted(newList, key=operator.itemgetter(1), reverse=True)
        else:
            return []

    def printAnnotated(self, result):
        print(result['phrases'])
        for pairs in result['result']:
            for pair in pairs[0]:
                print('\t' + str(pair))
            print('\t' + str(pairs[1]))

    @abstractmethod
    def annotate(self, tree):
        pass

    @abstractmethod
    def getTree(self, tree):
        pass


class StanfordAnnotator(Annotator):

    def __init__(self, **settings):
        super(StanfordAnnotator, self).__init__(**settings)
        try:
            connectionStatus = urllib.request.urlopen("http://localhost:9000").getcode()
            if connectionStatus == 200:
                print('Stanford server has been started')
        except:
            try:
                print('Please wait, try to start Stanford server')
                core, model = self.__getCoreAndModel()
                self.server = CoreNLPServer(core, model,)
                self.server.start()
                print('Starting server is succeed')
            except:
                print('Stanford server cannot be started, use another parser {nltk,ncbo}')

    def __getCoreAndModel(self):
        import os
        for file in os.listdir(self.corenlp_home):
            if file.startswith("stanford-corenlp") and file.endswith("models.jar"):
                model = os.path.join(self.corenlp_home, file)
            if file.startswith("stanford-corenlp") and not any(suff in file for suff in ["models.jar","javadoc.jar","sources.jar"]):
                core = os.path.join(self.corenlp_home, file)
        try:
            return core,model
        except:
            print("Files core or model are not found")

    def getTree(self, query):
        query = query.translate(str.maketrans(
            string.punctuation, ' ' * len(string.punctuation))).lower()
        parser = CoreNLPParser()
        return ParentedTree.convert(next(parser.raw_parse(query)))

    def annotate(self, query):
        tree = self.getTree(query)
        return self._getObos(tree)


class NLTKAnnotator(Annotator):
    def __init__(self, **settings):
        super(NLTKAnnotator, self).__init__(**settings)

    def getTree(self, query):
        query = query.translate(str.maketrans(
            string.punctuation, ' ' * len(string.punctuation))).lower()
        # Used when tokenizing words
        sentence_re = r"""
                (?x)                # set flag to allow verbose regexps
                (?:[A-Z]\.)+        # abbreviations, e.g. U.S.A.
              | \w+(?:-\w+)*        # words with optional internal hyphens
              | \$?\d+(?:\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
              | \.\.\.              # ellipsis
              | [][.,;"'?():_`-]    # these are separate tokens; includes ], [
        """
        # Taken from Su Nam Kim Paper...
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


class OBOLIBAnnotator(Annotator):
    def __init__(self, **settings):
        super(OBOLIBAnnotator, self).__init__(**settings)
        apikey = 'apikey=fc5d5241-1e8e-4b44-b401-310ca39573f6'
        ontologies = '&ontologies=MA,CHEBI,PR,GO,OPB,FMA,CL,UBERON'
        synonym = '&exclude_synonyms=false'
        whole_word_only = '&whole_word_only=true'
        exclude_numbers = '&exclude_numbers=false'
        longest_only = '&longest_only=true'
        self.__server = 'http://data.bioontology.org/annotator?' + apikey + ontologies + \
            synonym + whole_word_only + exclude_numbers + longest_only + '&text='

    def getTree(self, query):
        pass

    def annotate(self, query):
        r = requests.get(self.__server + query)
        results = r.json()
        selects = []
        if len(results) > 0:
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
                        v_from = int(annot['from']) if int(
                            annot['from']) < v_from else v_from
                        v_to = int(annot['to']) if int(
                            annot['to']) > v_to else v_to
                        v_text = annot['text'] + ' ' + \
                            v_text if int(annot['from']) < v_from else v_text
                        v_text += ' ' + \
                            annot['text'] if int(
                                annot['to']) > v_to else v_text
                    v_len = v_to - v_from
                if i == 0:
                    selects += [{'oboId': oboId, 'from': v_from,
                                 'to': v_to, 'len': v_len, 'text': v_text}]
                else:
                    prevSelect = selects[len(selects) - 1]
                    if prevSelect['from'] >= v_from and prevSelect['to'] <= v_to and prevSelect['len'] < v_len:
                        prevSelect['from'] = v_from
                        prevSelect['to'] = v_to
                        prevSelect['len'] = v_len
                        prevSelect['text'] = v_text
                        prevSelect['oboId'] = oboId
                    elif prevSelect['from'] == v_from and prevSelect['to'] == v_to and prevSelect['oboId'] != oboId:
                        #                         selects += [{'oboId':oboId,'from':v_from,'to':v_to,'len':v_len,'text':v_text}]
                        if 'fma' in oboId:
                            prevSelect['oboId'] = oboId
                        elif 'fma' not in prevSelect['oboId']:
                            prevSelect['oboId'] = oboId
                    elif prevSelect['to'] < v_from:
                        selects += [{'oboId': oboId, 'from': v_from,
                                     'to': v_to, 'len': v_len, 'text': v_text}]
        phrases = []
        result = []
        for sel in selects:
            phrases += [sel['text']]
            result += [sel['oboId']]
        return {'phrases': phrases, 'result': [[result, 1]]}
