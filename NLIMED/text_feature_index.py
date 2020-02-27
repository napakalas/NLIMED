"""MODULE: GET ALL URI DATA FROM BioPortal AND BUILD Cellml INVERTED INDEX FOR AUTOMATIC ANNOTATION"""
from nltk.tokenize import RegexpTokenizer
import struct
from NLIMED.general import *


class IndexAnnotation(GeneralNLIMED):
    """COLLECTING DATA FROM OBOLIBRARY"""

    def __init__(self, repository, ontoFolder):
        super(IndexAnnotation, self).__init__()
        self.repository = repository
        self.ontoIdPattern = {
            'BTO':'{alp}_{num}',
            'MA':'{alp}_{num}',
            'CHEBI':'{alp}_{num}',
            'UBERON':'{alp}_{num}',
            'SO': '{alp}_{num}',
            'PW': '{alp}_{num}',
            'PSIMOD': '{alp}_{num}',
            'PR': '{alp}_{num}',
            'PATO': '{alp}_{num}',
            'OPB': '{alp}#{num}',
            'NCBITAXON': '{num}',
            'MAMO': '{num}',
            'GO': '{alp}_{num}',
            'FMA': '{alp}{num}',
            'EFO': '{alp}_{num}',
            'EDAM': '{num}',
            'ECO': '{alp}_{num}',
            'CL': '{alp}_{num}',
            'SBO': '{alp}:{num}',
            'UNIPROT': '{num}',
            'KEGG': '{num}',
        }

        if self.repository == 'pmr':
            self.__initPMR(ontoFolder)
        elif self.repository == 'bm':
            self.__initBM(ontoFolder)

    def __loadOntologyClasses(self, ontoFolder):
        # now we only consider csv and obo files
        self.ontologies = {}
        import pandas as pd
        for file in os.listdir(ontoFolder):
            ontoName = file[:file.rfind('.')]
            if  file.endswith('.csv'):
                if ontoName in self.servers:
                    file = os.path.join(ontoFolder,file)
                    df = pd.read_csv(file,sep=',',header=0)
                    mainUrl = df['Class ID'].tolist()[0]
                    mainUrl = mainUrl[:mainUrl.rfind('/')]
                    classIds = df['Class ID'].tolist()
                    prefLabels = df['Preferred Label'].tolist()
                    synonims = df['Synonyms'].tolist()
                    definitions = df['Definitions'].tolist()
                    data = {}
                    for i in range(len(classIds)):
                        classId = classIds[i][classIds[i].rfind('/')+1:].upper().strip()
                        pref = prefLabels[i] if isinstance(prefLabels[i],str) else ""
                        syn = synonims[i].split('|') if isinstance(synonims[i],str) else []
                        deff = definitions[i].split('|') if isinstance(definitions[i],str) else []
                        data[classId] = [pref, syn, deff]
                    self.ontologies[ontoName] = {'mainUrl':mainUrl, 'dataVars':['prefLabel','synonyms','definitions'], 'data':data}
            elif file.endswith('.obo') and ontoName in self.servers:
                file = os.path.join(ontoFolder,file)
                f = open(file, 'r')
                lines = f.readlines()
                f.close()
                # get main url
                for line in lines:
                    if 'auto-generated-by' in line:
                        mainUrl = line[line.find('http'):-2]
                        break
                # get attributes
                data={}
                for i in range(len(lines)):
                    if '[Term]' in lines[i]:
                        classId = lines[i+1][lines[i+1].find(' ')+1:].strip()
                        preff = [lines[i+2][lines[i+2].find(' ')+1:].strip()]
                        syn = ''
                        deff =  [lines[i+3][lines[i+3].find(' "')+2:lines[i+3].rfind('"')].strip()]
                        data[classId] = [preff, syn, deff]
                        i += 4
                self.ontologies[ontoName] = {'mainUrl':mainUrl, 'dataVars':['prefLabel','synonyms','definitions'], 'data':data}

    def __initPMR(self, ontoFolder):
        self.servers = {'MA','CHEBI','PR','GO','OPB','FMA','CL','UBERON'}
        self.__loadOntologyClasses(ontoFolder)

    def __initBM(self, ontoFolder):
        self.servers = {'SO','PW','PSIMOD','PR','PATO','OPB','NCBITAXON','MAMO',
                        'FMA','EFO','EDAM','ECO','CL','CHEBI','BTO','SBO',
                        'UNIPROT','KEGG','EC-CODE','ENSEMBL','GO','MA'}
        self.__loadOntologyClasses(ontoFolder)
        self.ontoMap = {'SO': 'SO',
                        'BIOMODELS.SBO': 'SBO',
                        'SBO':'SBO',
                        'PW': 'PW',
                        'OBO.PW': 'PW',
                        'MOD': 'MOD',
                        'OBO.PSI-MOD': 'MOD',
                        'PSIMOD':'MOD',
                        'PR': 'PR',
                        'PATO': 'PATO',
                        'OBO.PATO': 'PATO',
                        'OPB': 'OPB',
                        'TAXONOMY': 'NCBITAXON',
                        'MAMO': 'MAMO',
                        'GO': 'GO',
                        'OBO.GO': 'GO',
                        'WWW.GENEONTOLOGY.ORG': 'GO',
                        'FMA': 'FMA',
                        'OBO.FMA': 'FMA',
                        'EFO': 'EFO',
                        'EDAM': 'EDAM',
                        'ECO': 'ECO',
                        'OBO.ECO': 'ECO',
                        'CL': 'CL',
                        'CHEBI': 'CHEBI',
                        'OBO.CHEBI': 'CHEBI',
                        'OBO.BTO': 'BTO',
                        'BTO':'BTO',
                        }

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
            bioClass = bioClass.upper()
            cls = bioClass[bioClass.rfind('/') + 1:].strip()
            clsId = cls if cls.find(':') < 0 else cls[cls.find(':') + 1:]
            clsOnto = bioClass[:bioClass.rfind(
                '/')][bioClass[:bioClass.rfind('/')].rfind('/') + 1:]
            clsOnto = cls[0:cls.find(':')] if cls.find(':') > 0 else clsOnto
            if clsOnto in self.ontoMap:
                clsOnto = self.ontoMap[clsOnto]
                # if any(x in bioClass.lower() for x in ['/so','/pw','/mod_', '/mod:','/pr','/pato','/opb','/mamo','/fma','/edam','/eco','/cl',]):
                #     print(bioClass)
                # if any(x in bioClass.lower() for x in ['edam',]):
                #     print({'status': True, 'reg': clsOnto, 'id': clsId, 'text': bioClass})
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
        listLinks = self._loadFromFlatFile('tmp','listOfObjects.txt')
        mapClass = {}
        for obj in listLinks:
            cls = self.getOboId(obj)
            if cls['status'] is True:
                clsId = cls['reg'] + ':' + cls['id']
                if clsId in mapClass:
                    content = mapClass[clsId]
                    content['link'] = content['link'] + [cls['text']]
                else:
                    id = self.ontoIdPattern[cls['reg'].upper()].replace('{num}', cls['id']).replace('{alp}',cls['reg'].upper())
                    if id in self.ontologies[cls['reg'].upper()]['data']:
                        data = self.ontologies[cls['reg'].upper()]['data'][id]
                        content = {'link': [cls['text']], 'prefLabel': data[0],
                                       'synonym': data[1], 'definition': data[2]}
                        mapClass[clsId] = content
        self._dumpJson(mapClass, 'tmp', 'mapClass.json')

    def __collectClassAttributesBM(self):
        self.idx_object = self._loadJson('tmp', 'BM_object.json')
        totObject = len(self.idx_object)
        count = 0
        found = 0
        mapClass = {}
        print(totObject)
        # print(self.ontologies.keys())
        # print(self.ontologies['CL']['data'].keys())
        for obj, objId in self.idx_object.items():
            cls = self.getClassId(obj)
            if cls['status'] is True:
                clsId = cls['reg'] + ':' + cls['id']
                if clsId in mapClass:
                    content = mapClass[clsId]
                    content['link'] += [objId]
                else:
                    # if 'EDAM' in cls['reg'].upper():
                    #     print('   ',cls['reg'].upper())
                    ontoType = cls['reg'].upper() if cls['reg'].upper() != 'MOD' else 'PSIMOD'
                    id = self.ontoIdPattern[ontoType].replace('{num}', cls['id']).replace('{alp}',cls['reg'].upper())
                    # if 'EDAM' in id:
                    #      print(id, '   ', self.ontoIdPattern[ontoType])
                    if id in self.ontologies[ontoType]['data']:
                        data = self.ontologies[ontoType]['data'][id]
                        content = {'link': [objId], 'prefLabel': data[0],
                                       'synonym': data[1], 'definition': data[2]}
                        mapClass[clsId] = content
                        found += 1
            count += 1
            if count % 1000000 == 0:
                print("extract %d of %d objects, found %d" %
                      (count, totObject, found))
        self._dumpJson(mapClass, 'tmp', 'BM_mapClass.json')

    """EXTRACTING FEATURES AND BUILD INVERTED INDEX"""

    def developInvertedIndex(self):
        if self.repository == 'pmr':
            self.__developInvertedIndexPMR()
        elif self.repository == 'bm':
            self.__developInvertedIndexBM()
        self._copyToIndexes(['inv_index', 'BM_inv_index',
                             'BM_selected_object.json', 'BM_selected_rdfPaths'])

    def __developInvertedIndexPMR(self):
        dataObo = self._loadJson('tmp', 'mapClass.json')
        idx_sbj_obj = self._loadJson('tmp', 'idx_sbj_obj')
        idx_id_object = self._loadJson('tmp', 'idx_id_object')
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
        self._dumpJson(inv_index, 'indexes', 'inv_index')

    def __developInvertedIndexBM(self):
        # load map class and obolibrary features from file
        dataClasses = self._loadJson('tmp', 'BM_mapClass.json')
        idx_object_id = self._loadJson('tmp', 'BM_object.json')
        idx_id_object = {idObj: objText for objText,
                         idObj in idx_object_id.items()}
        print("indexes have been extracted")

        # load sbj-obj from file
        idx_sbj_obj = {}
        idx_sbjobj_tracks = {}
        rdfPath = self._loadBinaryInteger('tmp', 'BM_rdfPaths')
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
                word for words in featVal if words is not None for word in self.stopAndToken(words)}
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
        self._dumpJson(inv_index, 'tmp', 'BM_inv_index')
        # save selected (subject,path,object) index
        selected = []
        for sbjobj, tracks in selected_sbj_track_obj.items():
            for track in tracks:
                selected += [sbjobj[0], track, sbjobj[1]]
        print("%d %d" % (len(selected_sbj_track_obj), len(selected)))
        self._saveBinaryInteger(selected, 'tmp', 'BM_selected_rdfPaths')
        # select obj
        selected_id_obj = {
            objId: idx_id_object[objId] for objId in objWithHttp}
        self._dumpJson(selected_id_obj, 'tmp', 'BM_selected_object.json')
