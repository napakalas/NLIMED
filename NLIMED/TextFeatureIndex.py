"""MODULE: GET ALL URI DATA FROM BioPortal AND BUILD Cellml INVERTED INDEX FOR AUTOMATIC ANNOTATION"""
from nltk.tokenize import RegexpTokenizer
import struct
from NLIMED.Settings import *


class IndexAnnotation(GeneralNLIMED):
    """COLLECTING DATA FROM OBOLIBRARY"""

    def __init__(self, repository):
        super(IndexAnnotation, self).__init__()
        self.repository = repository
        if self.repository == 'pmr':
            self.__initPMR()
        elif self.repository == 'bm':
            self.__buildIndexBM()

    def __initPMR(self):
        apikey = '?apikey='+self.apikey
        oboUrl = self.oboUrl
        self.servers = {
            'MA': oboUrl + 'MA/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FMA_{id}' + apikey,
            'CHEBI': oboUrl + 'CHEBI/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FCHEBI_{id}' + apikey,
            'PR': oboUrl + 'PR/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FPR_{id}' + apikey,
            'GO': oboUrl + 'GO/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_{id}' + apikey,
            'OPB': oboUrl + 'classes/http%3A%2F%2Fbhi.washington.edu%2FOPB%23OPB_{id}' + apikey,
            'FMA': oboUrl + 'FMA/classes/http%3A%2F%2Fpurl.org%2Fsig%2Font%2Ffma%2Ffma{id}' + apikey,
            'CL': oboUrl + 'CL/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FCL_{id}' + apikey,
            'UBERON': oboUrl + 'UBERON/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FUBERON_{id}' + apikey
        }

    def __initBM(self):
        apikey = '?apikey='+self.apikey
        oboUrl = self.oboUrl
        self.ontoServers = {
            'SO': oboUrl + 'SO/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FSO_{$id}+' + apikey,
            'SBO': oboUrl + 'SBO/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FSBO_{$id}' + apikey,
            'PW': oboUrl + 'PW/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FPW_{$id}' + apikey,
            'MOD': oboUrl + 'PSIMOD/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FMOD_{$id}' + apikey,
            'PR': oboUrl + 'PR/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_{$id}' + apikey,
            'PATO': oboUrl + 'PATO/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FPATO_{$id}' + apikey,
            'OPB': oboUrl + 'OPB/classes/http%3A%2F%2Fbhi.washington.edu%2FOPB%23OPB_{id}' + apikey,
            'NCBITAXON': oboUrl + 'NCBITAXON/classes/http%3A%2F%2Fpurl.bioontology.org%2Fontology%2FNCBITAXON%2F{$id}' + apikey,
            'MAMO': oboUrl + 'MAMO/classes/http%3A%2F%2Fidentifiers.org%2Fmamo%2FMAMO_{$id}' + apikey,
            'GO': oboUrl + 'GO/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_{id}' + apikey,
            'FMA': oboUrl + 'FMA/classes/http%3A%2F%2Fpurl.org%2Fsig%2Font%2Ffma%2Ffma{id}' + apikey,
            'EFO': oboUrl + 'EFO/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FIAO__{$id}' + apikey,
            'EDAM': oboUrl + 'EDAM/classes/http%3A%2F%2Fedamontology.org%2Fdata_{$id}' + apikey,
            'ECO': oboUrl + 'ECO/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FECO_{$id}' + apikey,
            'CL': oboUrl + 'CL/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FCL_{id}' + apikey,
            'CHEBI': oboUrl + 'CHEBI/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FCHEBI_{id}' + apikey,
            'BTO': oboUrl + 'BTO/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FBTO_{$id}' + apikey,
            'UNIPROT': 'https://www.uniprot.org/uniprot/{$id}.txt',
            'KEGG': 'http://rest.kegg.jp/get/{$id}',
            'EC-CODE': 'ftp://ftp.ebi.ac.uk/pub/databases/intenz/xml/ASCII/EC_5/EC_5.4/EC_5.4.2/EC_{$id}.xml',
            'ENSEMBL': 'https://rest.ensembl.org/lookup/id/{$id}?content-type=application/json'
        }
        self.ontoMap = {'so': 'SO',
                        'biomodels.sbo': 'SBO',
                        'sbo': 'SBO',
                        'pw': 'PW',
                        'obo.pw': 'PW',
                        'psimod': 'MOD',
                        'obo.psi-mod': 'MOD',
                        'pr': 'PR',
                        'pato': 'PATO',
                        'obo.pato': 'PATO',
                        'opb': 'OPB',
                        'taxonomy': 'NCBITAXON',
                        'mamo': 'MAMO',
                        'mamo': 'MAMO',
                        'go': 'GO',
                        'obo.go': 'GO',
                        'www.geneontology.org': 'GO',
                        'go': 'GO',
                        'GO': 'GO',
                        'fma': 'FMA',
                        'obo.fma': 'FMA',
                        'obo.FMA': 'FMA',
                        'efo': 'EFO',
                        'edam': 'EDAM',
                        'eco': 'ECO',
                        'obo.eco': 'ECO',
                        'cl': 'CL',
                        'chebi': 'CHEBI',
                        'obo.chebi': 'CHEBI',
                        'ChEBI': 'CHEBI',
                        'bto': 'BTO',
                        'obo.bto': 'BTO', }

    def stopAndToken(self, text):
        stWords = stopwords.words('english')
        tokenizer = RegexpTokenizer(r'\w+')
        word_tokens = tokenizer.tokenize(text.lower())
        filtered_sentence = [w for w in word_tokens if not w in stWords]
        return filtered_sentence

    def getOboId(self, bioClass):
        txtClass = bioClass.replace('<', '').replace('>', '').strip(' \t\n\r')
        if txtClass[0:4] == 'http':
            oboId = txtClass[txtClass.rfind('/') + 1:]
            if any(x in oboId for x in ['_', ':']):
                oboId = oboId.replace('_', ':')
                return {'status': True, 'reg': oboId[0:oboId.find(':')], 'id': oboId[oboId.find(':') + 1:], 'text': txtClass}
        return {'status': False, 'text': txtClass}

    def getClassId(self, bioClass):
        if bioClass[0:4] == 'http':
            cls = bioClass[bioClass.rfind('/') + 1:]
            clsId = cls if cls.find(':') < 0 else cls[cls.find(':') + 1:]
            clsOnto = bioClass[:bioClass.rfind(
                '/')][bioClass[:bioClass.rfind('/')].rfind('/') + 1:]
            clsOnto = cls[0:cls.find(':')] if cls.find(':') > 0 else clsOnto
            if clsOnto in self.ontoMap:
                clsOnto = self.ontoMap[clsOnto]
                return {'status': True, 'reg': clsOnto, 'id': clsId, 'text': bioClass}
        return {'status': False, 'text': bioClass}

    # obo structure: {'status':True,'reg':FMA,'id':123,'text':'http://purl.obolibrary.org/obo/FMA_123'}
    # mapObo structure: {'FMA:123':{'link':['http://purl.obolibrary.org/obo/FMA_123',...],'prefLabel':'','synonim':[],'definition':[]}, 'FMA:124':{...}, ...}
    def collectClassAttributes(self):
        if self.repository == 'pmr':
            self.__collectClassAttributesPMR()
        elif self.repository == 'bm':
            self.__collectClassAttributesBM()

    def __collectClassAttributesPMR(self):
        f = open('listOfObjects.txt', 'r')
        listLinks = f.readlines()
        f.close()
        mapClass = {}
        for obj in listLinks:
            cls = self.getOboId(obj)
            if cls['status'] is True:
                clsId = cls['reg'] + ':' + cls['id']
                if clsId in mapClass:
                    content = mapClass[clsId]
                    content['link'] = content['link'] + [cls['text']]
                else:
                    url = self.servers[cls['reg']].replace('{id}', cls['id'])
                    r = requests.get(url)
                    res = r.json()
                    if r.status_code == 200:
                        content = {'link': [cls['text']], 'prefLabel': res['prefLabel'],
                                   'synonym': res['synonym'], 'definition': res['definition']}
                        mapClass[clsId] = content
        self._dumpJson(mapClass, os.path.join(self.idxPath,'mapClass.json'))

    def __collectClassAttributesBM(self):
        totObject = len(self.idx_object)
        count = 0
        found = 0
        mapClass = {}
        for obj, objId in self.idx_object.items():
            cls = self.getClassId(obj)
            if cls['status'] is True:
                clsId = cls['reg'] + ':' + cls['id']
                if clsId in mapClass:
                    content = mapClass[clsId]
                    content['link'] += [objId]
                else:
                    try:
                        url = self.ontoServers[cls['reg']].replace(
                            '{id}', cls['id'])
                        r = requests.get(url)
                        res = r.json()
                        if r.status_code == 200:
                            content = {'link': [objId], 'prefLabel': res['prefLabel'],
                                       'synonym': res['synonym'], 'definition': res['definition']}
                            mapClass[clsId] = content
                            found += 1
                    except:
                        print("extraction error at object %d" % count)
                        self._dumpJson(mapClass, 'indexes/BM_mapClass' +
                                       str(count) + '.json')
            count += 1
            if count % 1000 == 0:
                print("extract %d of %d objects, found %d" %
                      (count, totObject, found))
        self._dumpJson(mapClass, 'indexes/BM_mapClass.json')

    """EXTRACTING FEATURES AND BUILD INVERTED INDEX"""

    def developInvertedIndex(self):
        if self.repository == 'pmr':
            self.__developInvertedIndexPMR()
        elif self.repository == 'bm':
            self.__developInvertedIndexBM()

    def __developInvertedIndexPMR(self):
        dataObo = self._loadJson('indexes/mapClass.json')
        idx_sbj_obj = self._loadJson('indexes/idx_sbj_obj')
        idx_id_object = self._loadJson('indexes/idx_id_object')
        # {'term0':{'OPB00': [inPrefLabel, lenPrefLabel, inSynonym, lenSynonym, inDefinition, lenDefinition, freq, totDocLength, totSubject], 'OPB01': [ ... ],...},'term1': {...}, ... }
        inv_index = {}
        for key, value in dataObo.items():
            prefLabel = set(self.stopAndToken(value['prefLabel']))
            synonym = set([word for words in value['synonym']
                           for word in self.stopAndToken(words)])
            definition = set([word for words in value['definition']
                              for word in self.stopAndToken(words)])
            for label in prefLabel:
                for oboId in value['link']:
                    if label in inv_index:
                        content = inv_index[label]
                        if oboId in content:
                            content[oboId] = [1, len(
                                prefLabel), content[oboId][2], content[oboId][3], content[oboId][4], content[oboIdkey][5], 0, 0, 0]
                        else:
                            content[oboId] = [
                                1, len(prefLabel), 0, 0, 0, 0, 0, 0, 0]
                    else:
                        content = {
                            oboId: [1, len(prefLabel), 0, 0, 0, 0, 0, 0, 0]}
                        inv_index[label] = content
            for syn in synonym:
                for oboId in value['link']:
                    if syn in inv_index:
                        content = inv_index[syn]
                        if oboId in content:
                            content[oboId] = [content[oboId][0], content[oboId][1], 1, len(
                                synonym), content[oboId][4], content[oboId][5], 0, 0, 0]
                        else:
                            content[oboId] = [
                                0, 0, 1, len(synonym), 0, 0, 0, 0, 0]
                    else:
                        content = {
                            oboId: [0, 0, 1, len(synonym), 0, 0, 0, 0, 0]}
                        inv_index[syn] = content
            for define in definition:
                for oboId in value['link']:
                    if define in inv_index:
                        content = inv_index[define]
                        if oboId in content:
                            content[oboId] = [content[oboId][0], content[oboId][1],
                                              content[oboId][2], content[oboId][3], 1, len(definition), 0, 0, 0]
                        else:
                            content[oboId] = [0, 0, 0, 0,
                                              1, len(definition), 0, 0, 0]
                    else:
                        content = {
                            oboId: [0, 0, 0, 0, 1, len(definition), 0, 0, 0]}
                        inv_index[define] = content

        # extract textual feature in description for each subject
        dictSbjTermFreq = {}
        for subject, objects in idx_sbj_obj.items():
            setText = set()
            dictTerm = {}
            for idObj in objects:
                obj = idx_id_object[str(idObj)]
                if obj[0:4] != 'http':
                    setText.add(obj.lower())
            for text in setText:
                listTerm = self.stopAndToken(text)
                for term in listTerm:
                    if term not in dictTerm:
                        dictTerm[term] = 1
                    else:
                        dictTerm[term] += 1
            dictSbjTermFreq[subject] = dictTerm
        # construct textual index
        for sbjId, termFreq in dictSbjTermFreq.items():
            listObjId = idx_sbj_obj[sbjId]
            for term, freq in termFreq.items():
                if term not in inv_index:
                    objFreq = {}
                    for objId in listObjId:
                        if idx_id_object[str(objId)][0:4] == 'http':
                            objFreq[idx_id_object[str(objId)]] = [
                                0, 0, 0, 0, 0, 0, freq, len(termFreq), 1]
                else:
                    objFreq = inv_index[term]
                    for objId in listObjId:
                        if idx_id_object[str(objId)][0:4] == 'http':
                            if idx_id_object[str(objId)] not in objFreq:
                                objFreq[idx_id_object[str(objId)]] = [
                                    0, 0, 0, 0, 0, 0, freq, len(termFreq), 1]
                            else:
                                objFreq[idx_id_object[str(objId)]][6] += freq
                                objFreq[idx_id_object[str(
                                    objId)]][7] += len(termFreq)
                                objFreq[idx_id_object[str(objId)]][8] += 1
                inv_index[term] = objFreq
        self._dumpJson(inv_index, 'indexes/inv_index')

    def __developInvertedIndexBM(self):
        # load map class and obolibrary features from file
        dataClasses = self._loadJson('indexes/BM_mapClass.json')
        idx_object_id = self._loadJson('indexes/BM_object.json')
        idx_id_object = {idObj: objText for objText,
                         idObj in idx_object_id.items()}
        print("indexes have been extracted")
        # load sbj-obj from file
        idx_sbj_obj = {}
        idx_sbjobj_tracks = {}
        rdfPath = self._loadBinaryInteger("indexes/BM_rdfPaths")
        print("subjecs, tracks, objects have been loaded")
        for i in range(0, len(rdfPath), 3):
            sbj, track, obj = rdfPath[i], rdfPath[i + 1], rdfPath[i + 2]
            idx_sbj_obj[sbj] = [
                obj] if sbj not in idx_sbj_obj else idx_sbj_obj[sbj] + [obj]
            idx_sbjobj_tracks[(sbj, obj)] = [track] if (
                sbj, obj) not in idx_sbjobj_tracks else idx_sbjobj_tracks[(sbj, obj)] + [track]
        for key in idx_sbj_obj:
            idx_sbj_obj[key] = set(idx_sbj_obj[key])
        print("subjects, tracks, objects have been organised")
        print("# of subjects-object is %d" % len(idx_sbjobj_tracks))

        # extracting bioontology features
        # {'term0':{'OPB00': [inPrefLabel, lenPrefLabel, inSynonym, lenSynonym, inDefinition, lenDefinition, freq, totDocLength, totSubject], 'OPB01': [ ... ],...},'term1': {...}, ... }
        inv_index = {}
        objWithHttp = set()

        # extract obolibrary features for each class
        def extractFeature(value, featName, indexPos):
            featVal = value[featName] if type(value[featName]) is list else [
                value[featName]]
            feature = {
                word for words in featVal for word in self.stopAndToken(words)}
            for term in feature:
                for objId in value['link']:
                    link = idx_id_object[objId]
                    content = inv_index[term] if term in inv_index else {}
                    content[link] = content[link] if link in content else [
                        0, 0, 0, 0, 0, 0, 0, 0, 0]
                    content[link][indexPos] = 1
                    content[link][indexPos + 1] = len(term)
                    inv_index[term] = content
                    objWithHttp.add(objId)

        for key, value in dataClasses.items():
            extractFeature(value, 'prefLabel', 0)
            extractFeature(value, 'synonym', 2)
            extractFeature(value, 'definition', 4)

        print('extracting features of %d ontologies' % len(objWithHttp))
        # extract textual feature in description for each subject
        # create new subject-track-object index and object index
        selected_sbj_track_obj = {}
        count = 0
        for sbjId, objects in idx_sbj_obj.items():
            setText = set()
            setObj = set()
            dictTerm = {}
            for objId in objects:
                if idx_id_object[objId][0:4] != 'http':
                    setText.add(idx_id_object[objId])
                elif objId in objWithHttp:
                    setObj.add(objId)
                    selected_sbj_track_obj[(sbjId, objId)] = set(
                        idx_sbjobj_tracks[(sbjId, objId)])

            if len(setObj) > 0:
                for text in setText:
                    for term in self.stopAndToken(text):
                        dictTerm[term] = 1 if term not in dictTerm else dictTerm[term] + 1

            for objId in setObj:
                link = idx_id_object[objId]
                for term, freq in dictTerm.items():
                    inv_index[term] = {
                    } if term not in inv_index else inv_index[term]
                    inv_index[term][link] = [0, 0, 0, 0, 0, 0, 0, 0,
                                             0] if link not in inv_index[term] else inv_index[term][link]
                    inv_index[term][link][6] += freq
                    inv_index[term][link][7] += len(dictTerm)
                    inv_index[term][link][8] += 1
            count += 1
            if count % 100000 == 0:
                print('excecute %d subjects out of %d' %
                      (count, len(idx_sbj_obj)))

        # save inverted index index
        self._dumpJson(inv_index, 'indexes/BM_inv_index')
        # save selected (subject,path,object) index
        selected = []
        for sbjobj, tracks in selected_sbj_track_obj.items():
            for track in tracks:
                selected += [sbjobj[0], track, sbjobj[1]]
        print("%d %d" % (len(selected_sbj_track_obj), len(selected)))
        self._saveBinaryInteger(selected, 'indexes/BM_selected_rdfPaths')
        # select obj
        selected_id_obj = {
            objId: idx_id_object[objId] for objId in objWithHttp}
        self._dumpJson(selected_id_obj, 'indexes/BM_selected_object.json')
