"""MODULE: GET ALL URI DATA FROM BioPortal AND BUILD Cellml INVERTED INDEX FOR AUTOMATIC ANNOTATION"""
import struct
from NLIMED.general import *

class IndexAnnotation(GeneralNLIMED, GeneralNLP):
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
            'OPB': '{alp}#{alp}_{num}',
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
        self.__featureTypes = ['prefLabel', 'synonyms', 'definitions', 'parentLabels']
        if self.repository == 'pmr':
            self.__initPMR(ontoFolder)
        elif self.repository in ('bm', 'bm-omex'):
            self.__initData(ontoFolder)

    def __loadOntologyClasses(self, ontoFolder):
        """
            Loading ontology classes from csv and obo files. Only classes found
            in PMR, BioModels, and BM-Omex is extracted
        """
        """
            It is funny that the ontology classes are not always available in
            the downloaded obo or csv files. It will be better to collaborate
            all available file types although it will take more time
        """
        self.ontologies = {}
        allFiles = self.getAllFilesInDir('tmp')
        fileName = os.path.join(self.currentPath, 'tmp', self.repository + '_onto.gz')
        # if organised ontologies file is available than load this file
        if any(file.endswith(fileName) for file in allFiles):
            self.ontologies = self.loadPickle(fileName)
            return
        # if the organised ontologies file is not available than proceed
        import pandas as pd
        import re
        ontoFiles = os.listdir(ontoFolder)
        def getStandardId(classId):
            classId = classId.split(' ')[0]
            if ':' in classId:
                reg, num = classId.strip().split(':')
                if reg in self.ontoIdPattern:
                    return self.ontoIdPattern[reg].replace('{num}', num).replace('{alp}',reg)
            return ''

        for ontoName in self.servers:
            # get ontology file name
            files = [ontoName.lower()+'.obo', ontoName.upper()+'.obo', ontoName.lower()+'.csv', ontoName.upper()+'.csv']
            data = {}
            for file in files:
                if file not in ontoFiles: continue
                fileName = os.path.join(ontoFolder,file)
                if fileName.endswith('.obo'):
                    print(ontoName+" : Extracting", fileName)
                    f = open(fileName, 'r'); lines = f.readlines(); f.close()
                    # get main url
                    mainUrl = '' # temporarily emptying the main URL
                    with open(fileName, 'r') as f:
                        contents = f.read()
                    ontoClasses = contents.split('[Term]\n')
                    for ontoClass in ontoClasses:
                        classId, preff, syn, deff, parentIds = '', '', [], [], []
                        for line in ontoClass.strip().split('\n'):
                            tmpLine = line.split(': ')
                            if len(tmpLine) != 2: continue
                            label, value = line.split(': ')
                            if label == 'id': classId = getStandardId(value)
                            if label == 'name': preff += value.strip()
                            if label == 'def': deff += re.findall('\"(.*?)\"',value)
                            if label == 'synonym': syn += re.findall('\"(.*?)\"',value)
                            if label == 'is_a': parentIds += [getStandardId(value.split(' ! ')[0])]
                        if classId != '':
                            if classId not in data:
                                data[classId] = [preff, syn, deff, parentIds]
                            else:
                                if len(syn) > len(data[classId][1]): data[classId][1] = syn
                                if len(deff) > len(data[classId][2]): data[classId][2] = deff
                                if len(parentIds) > len(data[classId][3]): data[classId][3] = parentIds

                    # now convert parentId in data to prefered label
                    for classId, val in data.items():
                        tmpLabel = [data[parentId][0] for parentId in val[3] if parentId in data]
                        val[3] = tmpLabel

                if fileName.endswith('.csv'):
                    print(ontoName+" : Extracting", fileName)
                    df = pd.read_csv(fileName,sep=',',header=0, index_col=0, dtype = str)
                    # df = df.dropna(axis=1, how='all')
                    for id in df.index:
                        classId = id[id.rfind('/')+1:].upper().strip()
                        # get prefered label
                        pref = df.loc[id, 'Preferred Label']
                        # get synonyms
                        synonims = [synonim for synonim in df.loc[id].filter(regex='synonym|Synonym') if isinstance(synonim, str)]
                        syn = list(set([syn for synonim in synonims for syn in synonim.split('|')]))
                        # get deffinition
                        deff = df.loc[id, 'Definitions'].split('|') if isinstance(df.loc[id, 'Definitions'], str) else []
                        # get parent and grand parent labels
                        parentLabel = []
                        if not isinstance(df.loc[id, 'Parents'], str): continue
                        for parentId in df.loc[id, 'Parents'].split('|'):
                            if parentId in df.index:
                                parentLabel += [df.loc[parentId, 'Preferred Label']]
                        # store as map in dictionary
                        if classId not in data:
                            data[classId] = [pref, syn, deff, parentLabel]
                        else:
                            if len(syn) > len(data[classId][1]): data[classId][1] = syn
                            if len(deff) > len(data[classId][2]): data[classId][2] = deff
                            if len(parentLabel) > len(data[classId][3]): data[classId][3] = parentLabel
                    mainUrl = id[:id.rfind('/')]

            self.ontologies[ontoName] = {'mainUrl':mainUrl, 'dataVars':self.__featureTypes, 'data':data}

        self.dumpPickle(self.ontologies, 'tmp', self.repository + '_onto.gz')

    def __initPMR(self, ontoFolder):
        self.servers = {'MA','CHEBI','PR','GO','OPB','FMA','CL','UBERON'}
        self.__loadOntologyClasses(ontoFolder)

    def __initData(self, ontoFolder):
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
            clsId = clsId.split('_')[-1] if 'OPB' in clsId else clsId
            clsOnto = bioClass[:bioClass.rfind('/')][bioClass[:bioClass.rfind('/')].rfind('/') + 1:]
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
        elif self.repository in ['bm', 'bm-omex']:
            self.__collectClassAttributesBM()
        self.__collectClassAttributesPredicate()

    def __collectClassAttributesPMR(self):
        listLinks = self._loadFromFlatFile('tmp',self.repository + '_listOfObjects.txt')
        mapClass = {}
        for obj in listLinks:
            cls = self.getOboId(obj)
            if cls['status'] is True:
                clsId = cls['reg'] + ':' + cls['id']
                if clsId in mapClass:
                    content = mapClass[clsId]
                    content['link'] += [cls['text']]
                else:
                    id = self.ontoIdPattern[cls['reg'].upper()].replace('{num}', cls['id']).replace('{alp}',cls['reg'].upper())
                    if id in self.ontologies[cls['reg'].upper()]['data']:
                        vars = self.ontologies[cls['reg'].upper()]['dataVars']
                        data = self.ontologies[cls['reg'].upper()]['data'][id]
                        content = {**{'link':[cls['text']]},**dict(zip(vars,data))}
                        mapClass[clsId] = content
        self._dumpJson(mapClass, 'tmp', self.repository + '_mapClass.json')

    def __collectClassAttributesBM(self):
        self.idx_object = self._loadJson('tmp', self.repository + '_object.json')
        totObject = len(self.idx_object)
        count = 0
        found = 0
        mapClass = {}
        print('Total objects: ', totObject)
        for obj, objId in self.idx_object.items():
            cls = self.getClassId(obj)
            if cls['status'] is True:
                clsId = cls['reg'] + ':' + cls['id']
                if clsId in mapClass:
                    content = mapClass[clsId]
                    content['link'] += [objId]
                else:
                    ontoType = cls['reg'].upper() if cls['reg'].upper() != 'MOD' else 'PSIMOD'
                    id = self.ontoIdPattern[ontoType].replace('{num}', cls['id']).replace('{alp}',cls['reg'].upper())
                    if id in self.ontologies[ontoType]['data']:
                        vars = self.ontologies[ontoType]['dataVars']
                        data = self.ontologies[ontoType]['data'][id]
                        content = {**{'link':[objId]},**dict(zip(vars,data))}
                        mapClass[clsId] = content
                        found += 1
            count += 1
            if count % 1000000 == 0:
                print("extract %d of %d objects, found %d" %
                      (count, totObject, found))
        self._dumpJson(mapClass, 'tmp', self.repository + '_mapClass.json')

    def __collectClassAttributesPredicate(self):
        try:
            from BeautifulSoup import BeautifulSoup, Tag
        except ImportError:
            from bs4 import BeautifulSoup, Tag
        import re

        if  self.repository == 'pmr':
            ns = self._loadJson('indexes', self.repository + '_idx_pref_ns')
            preds = self._loadJson('indexes', self.repository + '_idx_id_pred')
            predicates = {ns[str(val[0])]+val[1]:key for key, val in preds.items()}
        else:
            predicates = self._loadJson('tmp', self.repository + '_predicate.json')
        g01 = rdflib.Graph().parse(source='http://www.w3.org/2001/vcard-rdf/3.0')
        g99 = rdflib.Graph().parse(source='https://www.w3.org/1999/02/22-rdf-syntax-ns')
        predicateDict = {}
        for p, pId in predicates.items():
            if p != '':
                if 'biomodels.net' in p:
                    page_source = requests.get(p).text
                    parsed_html = BeautifulSoup(page_source)
                    label = re.sub("([a-z])([A-Z])","\g<1> \g<2>",parsed_html.body.find('h1').text).lower()
                    definition = parsed_html.body.find('blockquote').text.lower()
                    synonym = parsed_html.body.find('li').text.lower()
                    predicateDict[p] = {'id':str(pId), 'link':p, 'label':label, 'definition':definition, 'synonym':synonym}
                if 'purl.org' in p or 'dublincore' in p:
                    origP = p
                    if 'dublincore' in p:
                        p = 'http://purl.org/dc/elements/1.1/' + p.rsplit('/',1)[-1]
                    try:
                        page_source = requests.get(p).text
                        parsed_html = BeautifulSoup(page_source)
                        bodyEl = parsed_html.body.find('tr', attrs={'id':p})
                        sibling = bodyEl.next_sibling.next_sibling.next_sibling.next_sibling
                        label = sibling.next_element.next_element.nextSibling.nextSibling.text.lower()
                        definition = sibling.nextSibling.nextSibling.next_element.next_element.nextSibling.nextSibling.text.lower()
                        synonym = ""
                        predicateDict[origP] = {'id':str(pId), 'link':origP, 'label':label, 'definition':definition, 'synonym':synonym}
                    except:
                        label = re.sub("([a-z])([A-Z])","\g<1> \g<2>",p.split('/')[-1]).lower()
                        predicateDict[origP] = {'id':str(pId), 'link':origP, 'label':label, 'definition':'', 'synonym':''}
                if 'www.bhi.washington.edu' in p:
                    label = re.sub("([a-z])([A-Z])","\g<1> \g<2>",p.split('#')[-1]).lower()
                    predicateDict[p] = {'id':str(pId), 'link':p, 'label':label, 'definition':'', 'synonym':''}
                if 'www.cellml.org' in p:
                    label = re.sub("([a-z])([A-Z])","\g<1> \g<2>",p.split('#')[-1]).lower().replace('_',' ').replace('-',' ')
                    predicateDict[p] = {'id':str(pId), 'link':p, 'label':label, 'definition':'', 'synonym':''}
                if 'www.obofoundry.org' in p:
                    label = re.sub("([a-z])([A-Z])","\g<1> \g<2>",p.split('#')[-1]).lower().replace('_',' ').replace('-',' ')
                    predicateDict[p] = {'id':str(pId), 'link':p, 'label':label, 'definition':'', 'synonym':''}
                if 'http://www.w3.org/2001' in p:
                    np = rdflib.URIRef(p.replace('3.0#',''))
                    label = ''; definition = ''
                    for o in g01.objects(subject=np, predicate=rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#label')):
                        label += o.lower()
                    for o in g01.objects(subject=np, predicate=rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#comment')):
                        definition += o.lower()
                    if len(label)>0:
                        predicateDict[p] = {'id':str(pId), 'link':p, 'label':label, 'definition':definition, 'synonym':''}
                if 'http://www.w3.org/1999' in p:
                    label = ''; definition = ''
                    for o in g99.objects(subject=rdflib.URIRef(p), predicate=rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#label')):
                        label += o.lower()
                    for o in g99.objects(subject=rdflib.URIRef(p), predicate=rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#comment')):
                        definition += o.lower()
                    if len(label)>0:
                        predicateDict[p] = {'id':str(pId), 'link':p, 'label':label, 'definition':definition, 'synonym':''}
        self._dumpJson(predicateDict, 'tmp', self.repository + '_predicate_def.json')

    """EXTRACTING FEATURES AND BUILD INVERTED INDEX"""

    def developInvertedIndex(self):
        if self.repository == 'pmr':
            self.__developInvertedIndexPMR()
        elif self.repository in ('bm', 'bm-omex'):
            self.__developInvertedIndex()
        self.__developPredicateInvertedIndex()

    def __developInvertedIndexPMR(self):
        dataObo = self._loadJson('tmp', self.repository + '_mapClass.json')
        idx_sbj_obj = self._loadJson('tmp', self.repository + '_idx_sbj_obj')
        idx_id_object = self._loadJson('tmp', self.repository + '_idx_id_object')

        inv_index = {}
        inv_index_onto = {}
        print("Extract %d class ontologies"%len(dataObo), flush=True)
        for count, (key, value) in enumerate(dataObo.items()):
            for featName, featVal in value.items():
                if featName not in self.__featureTypes: continue
                indexPos = self.__featureTypes.index(featName)

                if isinstance(featVal, str):featVal = [featVal] # the data type of prefered label is string
                # else:featVal += [value['prefLabel']] # anticipate empty synonym, description, and parent label
                # else:featVal += [value['prefLabel']+value['prefLabel']] # anticipate empty synonym, description, and parent label
                # elif len(featVal)==0: featVal += [value['prefLabel']]

                # try collapse features  except prefered label:
                # if indexPos == 0: featVal = [featVal]
                # elif indexPos == 2: featVal += value[self.__featureTypes[indexPos-1]] + value[self.__featureTypes[indexPos+1]]
                # else: featVal = []

                # if indexPos == 0: featVal = [featVal] + value[self.__featureTypes[1]]
                # elif indexPos == 1: continue

                deepDependency = self.getDictDeepDependency(featVal)
                feature = set()
                feature = {word for words in featVal if words is not None for word in self.stopAndToken(words)}
                for link in value['link']:
                    for term in feature:
                        content = inv_index[term] if term in inv_index else {}
                        content[link] = content[link] if link in content else [0]*len(self.__featureTypes)*2+[0,0]
                        content[link][indexPos] = 1
                        if term in deepDependency:
                            content[link][indexPos + len(self.__featureTypes)] = deepDependency[term]
                        inv_index[term] = content
                    if link not in inv_index_onto:
                        inv_index_onto[link] = [0]*len(self.__featureTypes)+[0,0]
                    inv_index_onto[link][indexPos] = len(feature)
            print(count if count%50==0 or count==len(dataObo)-1 else '.' if count%11==0 else '', flush=True, end='')
        print('Finish extract class ontologies')

        # extract textual feature in description for each subject
        print("Extract textual features in cellml, sedml, or rdf description for %d sbj-obj pairs"%len(idx_sbj_obj), flush=True)
        dictSbjTermFreq = {}
        for count, (subject, objects) in enumerate(idx_sbj_obj.items()):
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
            print(count if count%50==0 or count==len(dataObo)-1 else '.' if count%11==0 else '', flush=True, end='')
        print("Finish extract textual features in cellml, sedml, or rdf description", flush=True)

        # construct textual index
        print("Construct %d textual index"%len(dictSbjTermFreq), flush=True)
        for count, (sbjId, termFreq) in enumerate(dictSbjTermFreq.items()):
            listObjId = idx_sbj_obj[sbjId]
            for objId in listObjId:
                for term, freq in termFreq.items():
                    objFreq = {} if term not in inv_index else inv_index[term]
                    if idx_id_object[str(objId)][0:4] == 'http':
                        if idx_id_object[str(objId)] not in objFreq:
                            objFreq[idx_id_object[str(objId)]] = [0]*len(self.__featureTypes)*2+[freq,1]
                        else:
                            objFreq[idx_id_object[str(objId)]][-2] += freq
                            objFreq[idx_id_object[str(objId)]][-1] += 1
                    inv_index[term] = objFreq
                if idx_id_object[str(objId)] not in inv_index_onto:
                    inv_index_onto[idx_id_object[str(objId)]] = [0]*len(self.__featureTypes)+[1,len(termFreq)]
                else:
                    inv_index_onto[idx_id_object[str(objId)]][-2] += 1
                    inv_index_onto[idx_id_object[str(objId)]][-1] += len(termFreq)
            print(count if count%50==0 or count==len(dataObo)-1 else '.' if count%11==0 else '', flush=True, end='')
        print('Finish construct textual index')

        self._dumpJson(inv_index, 'indexes', self.repository + '_inv_index')
        self._dumpJson(inv_index_onto, 'indexes', self.repository + '_inv_index_onto')

    def __developInvertedIndex(self):
        # load map class and obolibrary features from file
        dataClasses = self._loadJson('tmp', self.repository + '_mapClass.json')
        idx_object_id = self._loadJson('tmp', self.repository + '_object.json')
        idx_id_object = {idObj: objText for objText, idObj in idx_object_id.items()}
        idx_predicate_id = self._loadJson('tmp', self.repository + '_predicate.json')
        idx_id_predicate = {idPred: pred for pred, idPred in idx_predicate_id.items()}
        print("indexes have been extracted")

        # load sbj-obj from file
        idx_sbj_obj = {}
        idx_sbjobj_tracks = {}
        rdfPath = self._loadBinaryInteger('tmp', self.repository + '_rdfPaths')
        print("subjecs, tracks, objects have been loaded")

        for i in range(0, len(rdfPath), 3):
            sbj, track, obj = rdfPath[i], rdfPath[i + 1], rdfPath[i + 2]
            idx_sbj_obj[sbj] = [obj] if sbj not in idx_sbj_obj else idx_sbj_obj[sbj] + [obj]
            idx_sbjobj_tracks[(sbj, obj)] = [track] if (sbj, obj) not in idx_sbjobj_tracks else idx_sbjobj_tracks[(sbj, obj)] + [track]
        for key in idx_sbj_obj:
            idx_sbj_obj[key] = set(idx_sbj_obj[key])
        print("subjects, tracks, objects have been organised")
        print("# of subjects-object is %d" % len(idx_sbjobj_tracks))

        # extracting bioontology features
        inv_index = {}
        inv_index_onto = {}
        objWithHttp = set()

        # extract obolibrary features for each class
        for key, value in dataClasses.items():
            for featName, featVal in value.items():
                if featName not in self.__featureTypes: continue
                indexPos = self.__featureTypes.index(featName)
                if isinstance(featVal, str):featVal = [featVal] # the data type of prefered label is string
                # else:featVal += [value['prefLabel']] # anticipate empty synonym, description, and parent label
                deepDependency = self.getDictDeepDependency(value[featName])
                feature = {word for words in featVal if words is not None for word in self.stopAndToken(words)}
                for objId in value['link']:
                    link = idx_id_object[objId]
                    for term in feature:
                        content = inv_index[term] if term in inv_index else {}
                        content[link] = content[link] if link in content else [0]*len(self.__featureTypes)*2+[0,0]
                        content[link][indexPos] = 1
                        if term in deepDependency:
                            content[link][indexPos + len(self.__featureTypes)] = deepDependency[term]
                        inv_index[term] = content
                        objWithHttp.add(objId)
                    if link not in inv_index_onto:
                        inv_index_onto[link] = [0]*len(self.__featureTypes)+[0,0]
                    inv_index_onto[link][indexPos] = len(feature)

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
                    selected_sbj_track_obj[(sbjId, objId)] = set(idx_sbjobj_tracks[(sbjId, objId)])

            if len(setObj) > 0:
                for text in setText:
                    for term in self.stopAndToken(text):
                        dictTerm[term] = 1 if term not in dictTerm else dictTerm[term] + 1

            for objId in setObj:
                link = idx_id_object[objId]
                for term, freq in dictTerm.items():
                    inv_index[term] = {} if term not in inv_index else inv_index[term]
                    inv_index[term][link] = [0]*len(self.__featureTypes)*2+[0,0] if link not in inv_index[term] else inv_index[term][link]
                    inv_index[term][link][-2] += freq
                    inv_index[term][link][-1] += 1
                inv_index_onto[link][-2] += 1
                inv_index_onto[link][-1] += len(dictTerm)
            count += 1
            if count % 100000 == 0:
                print('excecute %d subjects out of %d' %(count, len(idx_sbj_obj)))

        # save inverted index index
        self._dumpJson(inv_index, 'indexes', self.repository + '_inv_index')
        self._dumpJson(inv_index_onto, 'indexes', self.repository + '_inv_index_onto')
        # save selected (subject,path,object) index
        selected = []
        for sbjobj, tracks in selected_sbj_track_obj.items():
            for track in tracks:
                selected += [sbjobj[0], track, sbjobj[1]]
        print("%d %d" % (len(selected_sbj_track_obj), len(selected)))
        self._saveBinaryInteger(selected, 'indexes', self.repository + '_rdfPaths')
        # select obj and save it
        selected_id_obj = {objId: idx_id_object[objId] for objId in objWithHttp}
        self._dumpJson(selected_id_obj, 'indexes', self.repository + '_object.json')
        # save predicates
        self._dumpJson(idx_id_predicate, 'indexes', self.repository + '_predicate.json')

    def __developPredicateInvertedIndex(self):
        predicateDict = self._loadJson('tmp',self. repository + '_predicate_def.json')
        inv_index = {}
        inv_index_onto = {}
        for pred, val in predicateDict.items():
            # load label, synonym, and definition
            for valType, valText in val.items():
                if valType not in ['label', 'synonym', 'definition']: continue
                valText = val['label'] + '. ' + valText if valType != 'label' else valText
                indexPos = 0 if valType == 'label' else 1 if valType == 'synonym' else 2
                deepDependency = self.getDictDeepDependency(valText, getLemma=True)
                for term in deepDependency:
                    content = inv_index[term] if term in inv_index else {}
                    content[val['id']] = content[val['id']] if val['id'] in content else [0, 0, 0, 0, 0, 0, 0, 0]
                    content[val['id']][indexPos] = 1
                    content[val['id']][indexPos + 5] = deepDependency[term]
                    inv_index[term] = content
                if val['id'] not in inv_index_onto: inv_index_onto[val['id']] = [0, 0, 0, 0, 0]
                inv_index_onto[val['id']][indexPos] = len(deepDependency)

        self._dumpJson(inv_index, 'indexes', self.repository + '_pred_inv_index')
        self._dumpJson(inv_index_onto, 'indexes', self.repository + '_pred_inv_index_onto')
