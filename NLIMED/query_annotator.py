"""MODUL: ANNOTATION"""
import nltk
import urllib.request
from nltk.parse.corenlp import CoreNLPParser
import operator
import math
import string
from NLIMED.general import *
from nltk.parse.corenlp import CoreNLPServer
import collections
import difflib

class Annotator(GeneralNLIMED, GeneralNLP):

    def __init__(self, **settings):
        super(Annotator, self).__init__()
        # setting multipliers values (alpha, betha, gamma, delta, theta, pl, repo, cutoff)
        self.innerMlt = [settings['alpha'], settings['beta'], settings['gamma'], settings['delta']]
        self.theta = settings['theta']
        self.topConsider = settings['pl']
        self.repository = settings['repo']
        self.cutoff = settings['cutoff'] if 'cutoff' in settings else 0.1
        self.inv_index = self._loadJson('indexes', self.repository + '_inv_index')
        self.inv_index_onto = self._loadJson('indexes', self.repository + '_inv_index_onto')
        self.pred_inv_index = self._loadJson('indexes', self.repository + '_pred_inv_index')
        self.pred_inv_index_onto = self._loadJson('indexes', self.repository + '_pred_inv_index_onto')
        if settings['repo'] == 'pmr':
            self.idx_id_object = self._loadJson('indexes', self.repository + '_idx_id_object')
            idx_id_sbj = self._loadJson('indexes',self.repository + '_idx_id_subject')
            self.totSubject = len(idx_id_sbj)
            self.totObject = 0
            for val in self.idx_id_object.values():
                if val.startswith('http'):
                    self.totObject += 1
        elif settings['repo'] in ['bm','bm-omex']:
            self.idx_id_object = self._loadJson('indexes', self.repository + '_object.json')
            rdfPath = self._loadBinaryInteger('indexes', self.repository + '_rdfPaths')
            self.totSubject = len(rdfPath) / 3
            self.totObject = len(self.idx_id_object)
        # get the average length of pref label, synonym, and definition
        from statistics import mean
        self.avgLengthOntos = list(map(mean, zip(*(self.inv_index_onto.values()))))

    def _getPossibleOntoPredicate(self, phrase):
        def getTf(app, ln, depLoc, numOfToken, type):
            """app = the number of term disappearance
               ln = the length of prefered label, synonyms, or definitions
               numOfToken = the length of phrase
               type = 0->pref label, 1->synonym, 2->definition"""
            return app / math.log1p(numOfToken+1+abs(ln - numOfToken))/math.log1p(1+depLoc)
        def getIdf(nq, N):
            """N = number of documents
               nq = number of documents having term"""
            return math.log1p(N / (nq+1))
        # exit when the phrase is empty
        if len(phrase) == 0: return {'phrase': '', 'candidate': [], 'maxValue': 0}
        # this is for tree from nltk
        if isinstance(phrase[0], tuple): phrase = [pair[0] for pair in phrase]
        outPhrase = ' '.join(phrase)
        deepDependency = self.getDictDeepDependency(outPhrase, getLemma=True)
        candidate = {}
        numOfToken = len(deepDependency)
        numOfPred = len(self.pred_inv_index_onto)
        for token in deepDependency:
            if token in self.pred_inv_index:
                numOfTokenPred = len(self.pred_inv_index[token])
                idf = getIdf(numOfTokenPred, numOfPred)
                for predId, val in self.pred_inv_index[token].items():
                    candidateVal = candidate[predId] if predId in candidate else 0
                    for i in range(len(self.innerMlt)-1): # special in predicate, minus 1, because it is not use parent label
                        candidateVal += self.innerMlt[i] * getTf(val[i], max([val[i+5],deepDependency[token]]), self.pred_inv_index_onto[predId][i], numOfToken, i) * idf
                    candidate[predId] = candidateVal
        # remove candidate with weight lower than cutoff
        for predId in candidate.copy().keys():
            if candidate[predId] < self.cutoff:
                candidate.pop(predId)
        if len(candidate) > 0:
            candidate = sorted(candidate.items(), key=operator.itemgetter(1), reverse=True)
            maxValue = candidate[0][1] if len(candidate) > 0 else 0
            # choose best considered
            if len(candidate) > self.topConsider:
                candidate = candidate[0:self.topConsider]
            return {'phrase': outPhrase, 'candidate': candidate, 'maxValue': maxValue}
        else:
            return {'phrase': '', 'candidate': [], 'maxValue': 0}

    def _getPossibleObo(self, phrase):
        def getTf(app, ln, depLoc, numOfToken, type):
            """app = the number of term disappearance
               ln = the length of prefered label, synonyms, or definitions
               numOfToken = the length of phrase
               type = 0->pref label, 1->synonym, 2->definition"""
            return app / math.log1p(numOfToken+1+abs(ln - numOfToken))/math.log1p(1+depLoc)
            # return app / (numOfToken + math.log1p(1+abs(ln - numOfToken)))
            # return app / (numOfToken + math.log1p((1+abs(ln - numOfToken))*(1+depLoc)))
            # return app / (numOfToken + math.log1p(1+abs(ln - numOfToken)))/math.log1p(1+depLoc)
            # return app / (numOfToken + abs(ln - numOfToken))
            # k1 = 1.2; b = 0.75;
            # return (app * (k1 + 1))/(app + k1 * (1 - b + b * ln / self.avgLengthOntos[type])) # BM25
            # return (app * (k1 + 1))/(app + k1 * (1 - b + b * (ln + abs(ln - numOfToken)) / self.avgLengthOntos[type])) # BM25 - modified

        def getIdf(nq, N):
            """N = number of documents
               nq = number of documents having term"""
            return math.log1p(N / (nq+1))
            # return math.log(N / (nq+1))
            # return math.log1p((N - nq + 0.5)/(nq + 0.5)+1) #BM25

        # exit when the phrase is empty
        if len(phrase) == 0:
            return {'phrase': '', 'candidate': [], 'maxValue': 0}

        if isinstance(phrase[0], tuple):  # this is for tree from nltk
            phrase = [pair[0] for pair in phrase]
        outPhrase = ' '.join(phrase)
        deepDependency = self.getDictDeepDependency(outPhrase)
        candidate = {}
        numOfToken = len(deepDependency)
        for token in deepDependency:
            if token in self.inv_index:
                for oboId, val in self.inv_index[token].items():
                    candidate[oboId] = candidate[oboId] if oboId in candidate else 0
                    idf = getIdf(len(self.inv_index[token]), self.totObject * self.inv_index_onto[oboId][3])
                    for i in range(len(self.innerMlt)):
                        additionalVal = self.innerMlt[i] * getTf(val[i], max([val[i+len(self.innerMlt)],deepDependency[token]]), self.inv_index_onto[oboId][i], numOfToken, i)
                        additionalVal *= idf if i == 2 else 1
                        candidate[oboId] +=  additionalVal
                    idf = getIdf(val[-1], self.totSubject)
                    candidate[oboId] += self.theta * getTf(val[-2], deepDependency[token], numOfToken, self.inv_index_onto[oboId][-1], len(self.inv_index_onto[oboId])-1) * idf
        # remove candidate with weight lower than cutoff
        for oboId in candidate.copy().keys():
            if candidate[oboId] < self.cutoff:
                candidate.pop(oboId)
        if len(candidate) > 0:
            candidate = sorted(candidate.items(), key=operator.itemgetter(1), reverse=True)
            maxValue = candidate[0][1] if len(candidate) > 0 else 0
            # choose best considered
            if len(candidate) - 1 > self.topConsider:
                candidate = candidate[0:self.topConsider]
            # print({'phrase': outPhrase, 'candidate': candidate, 'maxValue': maxValue})
            return {'phrase': outPhrase, 'candidate': candidate, 'maxValue': maxValue}
        else:
            return {'phrase': '', 'candidate': [], 'maxValue': 0}

    def _getObos(self, tree):
        """
        Returning phrases and all ontology instances based on tree input.
        Input : - tree, a parsed query in NLTK parented tree format
                - cutoff, to select meaningful tree. phrase with maxValue
                  lower than cutoff is discarded
        Output: a dictionary of phrases with all ontology intances and values.
        """
        hasAnnotated = {}
        """Calculate weight of all possible subtree"""
        for subtree in tree.subtrees(filter=None):
            if subtree.label() == 'NP':
                pos = subtree.treeposition()
                entity = self._getPossibleObo(subtree.leaves())
                if entity['maxValue'] > self.cutoff:
                    hasAnnotated[pos] = entity
        # print(hasAnnotated, '\n')
        """select phrases with highest value"""
        # sorted hasAnnotated based on maxValue and longest key descendent
        def get_keylength(v):
            key, values = v
            return values['maxValue'], len(key)
        sortedPositions = collections.OrderedDict(sorted(hasAnnotated.items(), key=get_keylength, reverse=True))
        for position in sortedPositions:
            if position in hasAnnotated:
                # delete parent
                parentPos = position[:-1]
                while len(parentPos) > 0:
                    if parentPos in hasAnnotated:
                        hasAnnotated.pop(parentPos)
                    parentPos = parentPos[:-1]
                # delete children
                for childPos in hasAnnotated.copy():
                    if len(childPos) > len(position) and childPos[:len(position)] == position:
                        hasAnnotated.pop(childPos)
        """remove phrase that do not have annotation"""
        for pos in hasAnnotated.copy():
            if len(hasAnnotated[pos]['candidate']) == 0:
                hasAnnotated.pop(pos)
        # print(hasAnnotated, '\n')
        """get list of phrases"""
        phrases = [val['phrase'] for val in hasAnnotated.values()]
        """get combination of all annotation"""
        bestCombination = self._getBestCombination(hasAnnotated)
        """reverse each combination"""
        for comb in bestCombination: comb[0] = comb[0][::-1]
        return {'phrases': phrases, 'result': bestCombination}

    def _getBestCombination(self, hasAnnotated):
        termNum = len(hasAnnotated)
        multiplier = 2
        if termNum > 1:
            key = list(hasAnnotated.keys())[0]
            newAnnotated = hasAnnotated.copy()
            newAnnotated.pop(key)
            prevCombinations = self._getBestCombination(newAnnotated)
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

    def setWeighting(self, alpha, beta, gamma, delta, theta, pl, cutoff):
        self.innerMlt = [alpha, beta, gamma, delta]
        self.theta = theta
        self.topConsider = pl
        self.cutoff = cutoff

    def getWeighting(self):
        return {'alpha':self.innerMlt[0], 'beta':self.innerMlt[1], 'gamma':self.innerMlt[2], \
                'delta':self.innerMlt[3], 'theta':self.theta, 'pl': self.topConsider, 'cutoff':self.cutoff}

    @abstractmethod
    def annotate(self, query):
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
                if 'quite' not in settings:
                    print('Stanford server has been started')
                elif not settings['quite']:
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
              | [][.,;"'?():_`-]    # these are separate tokens, includes brackets
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
        toks = self.tokenise(query)
        postoks = nltk.tag.pos_tag(toks)
        return ParentedTree.convert(chunker.parse(postoks))

    def annotate(self, query):
        tree = self.getTree(query)
        return self._getObos(tree)

class OBOLIBAnnotator(GeneralNLIMED):
    def __init__(self):
        super(OBOLIBAnnotator, self).__init__()
        apikey = 'apikey=' + self.apikey
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

class StanzaAnnotator(Annotator):
    nlps = {'bionlp13cg':stanza.Pipeline('en', package='craft', processors={'ner': 'BioNLP13CG'},verbose=False), \
            'jnlpba':stanza.Pipeline('en', package='craft', processors={'ner': 'JNLPBA'},verbose=False), \
            'anatem':stanza.Pipeline('en', package='craft', processors={'ner': 'AnatEM'},verbose=False), \
            'radiology':stanza.Pipeline('en', package='craft', processors={'ner': 'i2b2'},verbose=False)}

    def __init__(self, **settings):
        super(StanzaAnnotator, self).__init__(**settings)

    def getTree(self, query):
        pass

    def _getDictAllPhrases(self, query):
        """ Get all possible phrases """
        self.__docs = [nlp(query) for nlp in self.nlps.values()]
        dictPhrases = {}
        for doc in self.__docs:
            for sentence in doc.sentences:
                for entity in sentence.entities:
                    if entity.type == 'TEST': continue # exclude TEST type entity
                    if entity.start_char not in dictPhrases:
                        dictPhrases[entity.start_char] = entity.to_dict()
                    elif dictPhrases[entity.start_char]['end_char'] == entity.end_char:
                        if entity.type not in dictPhrases[entity.start_char]['type']:
                            dictPhrases[entity.start_char]['type'] += '|' + entity.type
                    elif dictPhrases[entity.start_char]['end_char'] < entity.end_char:
                        dictPhrases[entity.start_char] = entity.to_dict()
        dictPhrases = collections.OrderedDict(sorted(dictPhrases.items()))
        return dictPhrases

    def _getPhrases(self, query):
        """
        This function returns phrases utilising three stanza processors in
        biomedical and clinical package. The phrases are the longest phrases
        based on provided query
        """
        # get all possible phrases
        dictPhrases = self._getDictAllPhrases(query)
        # remove shorter phrases contained by longest phrase
        keys = list(dictPhrases.copy().keys()); currPos = 0
        for i in range(1, len(keys)):
            if dictPhrases[keys[i]]['end_char'] <= dictPhrases[keys[currPos]]['end_char']:
                dictPhrases.pop(keys[i])
            else:
                currPos = i
        return dictPhrases

    def annotate(self, query):
        """
        This annotation using stanza NER. The type of entities are mostly
        anatomy, chemical, protein. Not yet identified physics of biology,
        such as OPB and predicates such as <isVersionOf>
        """
        # get longest entities based on stanza biomedical and clinical package
        dictPhrases = self._getPhrases(query)

        # get possible Ontology from each entity
        entities = {}
        phrases = []
        for key, phrase in dictPhrases.items():
            possibleObo = self._getPossibleObo(self.tokenise(phrase['text']))
            if len(possibleObo['candidate']) > 0:
                entities[key] = possibleObo
                phrases += [phrase['text']]

        # get combination of all annotation
        bestCombination = self._getBestCombination(entities)

        # reverse each combination
        for comb in bestCombination:
            comb[0] = comb[0][::-1]

        return {'phrases': phrases, 'result': bestCombination}

class MixedAnnotator(StanzaAnnotator):
    def __init__(self, **settings):
        super(MixedAnnotator, self).__init__(**settings)

    def getTree(self, query):
        pass

    def __getBorders(self, sentence):
        """Get all phrase borders in a sentence"""
        borders = []
        for word in sentence.words:
            if word.upos == 'PUNCT': continue
            borders += [word.id]
            if abs(word.id-word.head) == 1: continue
            depRange = (word.id, word.head)
            for i in range(min(depRange)+1,max(depRange)):
                if i in borders: borders.remove(i)
        return borders

    def __getMainHeadFromEntity(self, entity):
        """Get the main term in an entity and its parent"""
        wordIds = [word.id for word in entity.words]
        headIds = [word.head for word in entity.words]
        for wordId in wordIds.copy():
            if wordId in headIds: headIds.remove(wordId); wordIds.remove(wordId)
        return wordIds[0], headIds[0]

    def __getBorderOfEntity(self, mainId, stcBorders):
        """Get the border of an entity"""
        for i in range(len(stcBorders)-1):
            if stcBorders[i] <= mainId and stcBorders[i+1]>= mainId:
                return stcBorders[i], stcBorders[i+1]
        return None

    def __getContexts(self, entBorders, entity, sentence):
        """Get contexts of an entity"""
        leftEntityId, rightEntityId = entity.words[0].id, entity.words[-1].id
        leftStart, leftEnd = sentence.tokens[entBorders[0]-1].start_char, entity.start_char - 1
        rightStart, rightEnd = entity.end_char + 1, sentence.tokens[entBorders[1]-1].end_char
        leftCtx = ' '.join([sentence.words[i].text for i in range(entBorders[0]-1, entity.words[0].id-1)])
        rightCtx= ' '.join([sentence.words[i].text for i in range(entity.words[-1].id, entBorders[1])])
        context = [{'obo':leftCtx+ ' ' + entity.type.replace('_', ' ') if len(leftCtx.strip()) > 0 else '', 'pred':leftCtx, 'start_char':leftStart, 'end_char':leftEnd}, \
                   {'obo':entity.type.replace('_', ' ') + ' ' + rightCtx if len(rightCtx.strip()) > 0 else '', 'pred':rightCtx, 'start_char':rightStart, 'end_char':rightEnd}]
        return context

    def __getContextOnto(self, context):
        "Get the ontology of context, can be as ontology instances or predicates or none"
        contextOnto = {'obo':{}, 'predicate':[]}
        for ctx in context:
            instances = self._getPossibleObo(self.tokenise(ctx['obo']))
            predicates = self._getPossibleOntoPredicate(self.tokenise(ctx['pred']))
            if instances['maxValue'] > predicates['maxValue']:
                contextOnto['obo'][ctx['start_char']] = instances
            else:
                contextOnto['predicate'] += [predicates]
        return contextOnto

    def _getDictAllPhrases(self, query):
        """
            Get all possible phrases and context surrounding the phrase.
            The context can be related to a new ontology instances or predicates.
            To identify context:
            1. Find the borders of a sentence. The borders of an entity are words
               to separate the entity to previous and next entities.
            2. Find the main term of an entity
            3. Find the border of an entity
            4. Find context surrounding an entity
            5. normalise overlapped text in context so it use the type of entity rather than the text of entity
        """
        self.__docs = [nlp(query) for nlp in self.nlps.values()]
        dictPhrases = {}
        for doc in self.__docs:
            for sentence in doc.sentences:
                # 1. identify sentence borders
                stcBorders = self.__getBorders(sentence)
                for entity in sentence.entities:
                    if entity.type == 'TEST': continue # exclude TEST type entity
                    if entity.start_char not in dictPhrases:
                        dictPhrases[entity.start_char] = entity.to_dict()
                    elif dictPhrases[entity.start_char]['end_char'] == entity.end_char:
                        if entity.type not in dictPhrases[entity.start_char]['type']:
                            dictPhrases[entity.start_char]['type'] += '|' + entity.type
                    elif dictPhrases[entity.start_char]['end_char'] < entity.end_char:
                        dictPhrases[entity.start_char] = entity.to_dict()
                    # 2. get the main term of an entity
                    mainAndHead = self.__getMainHeadFromEntity(entity)
                    dictPhrases[entity.start_char]['main'] = mainAndHead[0]
                    dictPhrases[entity.start_char]['head'] = mainAndHead[1]
                    # 3. get the borders of the entity
                    entBorders = self.__getBorderOfEntity(mainAndHead[0], stcBorders)
                    if entBorders != None:
                        dictPhrases[entity.start_char]['leftBorder'] = entBorders[0]
                        dictPhrases[entity.start_char]['rightBorder'] = entBorders[1]
                    # 4. get context surrounding the entity
                    if entBorders != None:
                        context = self.__getContexts(entBorders, entity, sentence)
                    else:
                        context = []
                    dictPhrases[entity.start_char]['context'] = context
        dictPhrases = collections.OrderedDict(sorted(dictPhrases.items()))

        # 5.normalise overlapped text in context so it use the type of entity rather than the text of entity
        keys = list(dictPhrases.keys())
        for i in range(len(keys)):
            key = keys[i]
            prevI, nextI = i-1, i+1
            if len(dictPhrases[key]['context']) < 2: continue
            while prevI >= 0:
                ctx = dictPhrases[key]['context'][0]
                prevPhrase = dictPhrases[keys[prevI]]
                if prevPhrase['start_char'] >= ctx['start_char'] and prevPhrase['end_char'] <= ctx['end_char']:
                    ctx['obo'] = ctx['obo'].replace(prevPhrase['text'], prevPhrase['type'])

                if prevPhrase['start_char'] < ctx['start_char'] and prevPhrase['end_char'] > ctx['start_char'] and prevPhrase['end_char'] <= ctx['end_char']:
                    match = difflib.SequenceMatcher(None, prevPhrase['text'], ctx['obo']).get_matching_blocks()
                    if len(match) > 1:
                        ctx['obo'] = ctx['obo'][match[-2].b+match[-2].size+1:]

                if prevPhrase['end_char'] < ctx['start_char']:
                    break
                prevI -= 1
            while nextI < len(keys):
                ctx = dictPhrases[key]['context'][1]
                nextPhrase = dictPhrases[keys[nextI]]
                if nextPhrase['start_char'] >= ctx['start_char'] and nextPhrase['end_char'] <= ctx['end_char']:
                    ctx['obo'] = ctx['obo'].replace(nextPhrase['text'], nextPhrase['type'])

                if nextPhrase['start_char'] > ctx['start_char'] and nextPhrase['start_char'] < ctx['end_char'] and nextPhrase['end_char'] >= ctx['end_char']:
                    match = difflib.SequenceMatcher(None, nextPhrase['text'], ctx['obo']).get_matching_blocks()
                    if len(match) > 1:
                        ctx['obo'] = ctx['obo'][:match[-2].b-1]

                if nextPhrase['end_char'] < ctx['start_char']:
                    break
                nextI += 1

        return dictPhrases

    def annotate(self, query):
        """
        This function annotates query utilising stanza and CoreNLP
        1. Find the longest phrases/entities based on stanza along with their contexts
        2. Find ontologies of the longest phrases and their contexts
        3. Find context's predicates or ontology instances
        4. Specify contex ontology instances as additional ontologies

        """
        # 1. Find the longest phrases/entities based on stanza along with their contexts
        dictPhrases = self._getPhrases(query)
        # 2. Find ontologies of the longest phrases and their contexts
        entities = {}
        phrases = []
        predicates = []
        for key, phrase in dictPhrases.items():
            # get possible obo
            possibleObo = self._getPossibleObo(self.tokenise(phrase['text']))
            # consider possible obo with candidate only
            if len(possibleObo['candidate']) > 0:
                entities[key] = possibleObo
                phrases += [phrase['text']]
                # 3. Find context's predicates or ontology instances
                contextOnto = self.__getContextOnto(phrase['context'])
                predicates += [[pred for preds in contextOnto['predicate'] for pred in preds['candidate']]]
                entities[key]['predicate'] = [pred for preds in contextOnto['predicate'] for pred in preds['candidate']]
                # 4. Specify contex ontology instances as additional ontologies
                for keyOnto, onto in contextOnto['obo'].items():
                    entities[keyOnto] = onto
                    predicates += [[]]
                    phrases += [onto['phrase']]

        # get combination of all annotation
        bestCombination = self._getBestCombination(entities)

        # reverse each combination
        for comb in bestCombination:
            comb[0] = comb[0][::-1]

        return {'phrases': phrases, 'result': bestCombination, 'predicates': predicates}
