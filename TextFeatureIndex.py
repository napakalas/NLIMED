""" MODULE: GET ALL URI DATA FROM BIOONTOLOGY AND BUILD INVERTED INDEX FOR AUTOMATIC ANNOTATION """
import requests
import json
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
import .Settings

class IndexAnnotation:
    """COLLECTING DATA FROM OBOLIBRARY"""
    apikey =  '?apikey='+Settings.apikey
    servers = {
                'MA':'http://data.bioontology.org/ontologies/MA/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FMA_{id}'+apikey,
                'CHEBI':'http://data.bioontology.org/ontologies/CHEBI/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FCHEBI_{id}'+apikey,
                'PR':'http://data.bioontology.org/ontologies/PR/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FPR_{id}'+apikey,
                'GO':'http://data.bioontology.org/ontologies/GO/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_{id}'+apikey,
                'OPB':'http://data.bioontology.org/ontologies/OPB/classes/http%3A%2F%2Fbhi.washington.edu%2FOPB%23OPB_{id}'+apikey,
                'FMA':'http://data.bioontology.org/ontologies/FMA/classes/http%3A%2F%2Fpurl.org%2Fsig%2Font%2Ffma%2Ffma{id}'+apikey,
                'CL':'http://data.bioontology.org/ontologies/CL/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FCL_{id}'+apikey,
                'UBERON':'http://data.bioontology.org/ontologies/UBERON/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FUBERON_{id}'+apikey
              }

    def getOboId(self,bioClass):
        txtClass = bioClass.replace('<','').replace('>','').strip(' \t\n\r')
        if txtClass[0:4]=='http':
            oboId = txtClass[txtClass.rfind('/')+1:]
            if any(x in oboId for x in ['_',':']):
                oboId = oboId.replace('_',':')
                return {'status':True,'reg':oboId[0:oboId.find(':')],'id':oboId[oboId.find(':')+1:],'text':txtClass}
        return {'status':False,'text':txtClass}

    # obo structure: {'status':True,'reg':FMA,'id':123,'text':'http://purl.obolibrary.org/obo/FMA_123'}
    # mapObo structure: {'FMA:123':{'link':['http://purl.obolibrary.org/obo/FMA_123',...],'prefLabel':'','synonim':[],'definition':[]}, 'FMA:124':{...}, ...}
    def collectOboAttributes(self):
        f = open('listOfObjects.txt', 'r')
        listLinks = f.readlines()
        mapObo={}
        for obj in listLinks:
            obo = self.getOboId(obj)
            if obo['status'] is True:
                oboId = obo['reg']+':'+obo['id']
                if oboId in mapObo:
                    content = mapObo[oboId]
                    content['link'] = content['link']+[obo['text']]
                else:
                    url = IndexAnnotation.servers[obo['reg']].replace('{id}',obo['id'])
                    r = requests.get(url)
                    res = r.json()
                    if r.status_code == 200:
                        content = {'link':[obo['text']],'prefLabel':res['prefLabel'],'synonym':res['synonym'],'definition':res['definition']}
                        mapObo[oboId]=content
        with open('mapObo.json', 'w') as fp:
            json.dump(mapObo, fp)

    """EXTRACTING FEATURES AND BUILD INVERTED INDEX"""
    def removeStopWordAndTokenise(self,text):
        stWords = stopwords.words('english')
        tokenizer = RegexpTokenizer(r'\w+')
        word_tokens = tokenizer.tokenize(text.lower())
        filtered_sentence = [w for w in word_tokens if not w in stWords]
        return filtered_sentence

    def developInvertedIndex(self):
        with open('mapObo.json', 'r') as fp:
            dataObo = json.load(fp)
        with open('idx_sbj_obj', 'r') as fp:
            idx_sbj_obj = json.load(fp)
        with open('idx_id_object', 'r') as fp:
            idx_id_object = json.load(fp)

        inv_index={} #{'term0':{'OPB00': [inPrefLabel, lenPrefLabel, inSynonym, lenSynonym, inDefinition, lenDefinition, freq, totDocLength, totSubject], 'OPB01': [ ... ],...},'term1': {...}, ... }

        for key, value in dataObo.items():
            prefLabel = set(self.removeStopWordAndTokenise(value['prefLabel']))
            synonym = set([word for words in value['synonym'] for word in self.removeStopWordAndTokenise(words)])
            definition = set([word for words in value['definition'] for word in self.removeStopWordAndTokenise(words)])
            for label in prefLabel:
                for oboId in value['link']:
                    if label in inv_index:
                        content = inv_index[label]
                        if oboId in content:
                            content[oboId] = [1,len(prefLabel),content[oboId][2],content[oboId][3],content[oboId][4],content[oboIdkey][5],0,0,0]
                        else:
                            content[oboId] = [1,len(prefLabel),0,0,0,0,0,0,0]
                    else:
                        content = {oboId:[1,len(prefLabel),0,0,0,0,0,0,0]}
                        inv_index[label]=content
            for syn in synonym:
                for oboId in value['link']:
                    if syn in inv_index:
                        content = inv_index[syn]
                        if oboId in content:
                            content[oboId] = [content[oboId][0],content[oboId][1],1,len(synonym),content[oboId][4],content[oboId][5],0,0,0]
                        else:
                            content[oboId] = [0,0,1,len(synonym),0,0,0,0,0]
                    else:
                        content = {oboId:[0,0,1,len(synonym),0,0,0,0,0]}
                        inv_index[syn]=content
            for define in definition:
                for oboId in value['link']:
                    if define in inv_index:
                        content = inv_index[define]
                        if oboId in content:
                            content[oboId] = [content[oboId][0],content[oboId][1],content[oboId][2],content[oboId][3],1,len(definition),0,0,0]
                        else:
                            content[oboId] = [0,0,0,0,1,len(definition),0,0,0]
                    else:
                        content = {oboId:[0,0,0,0,1,len(definition),0,0,0]}
                        inv_index[define]=content

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
                listTerm = self.removeStopWordAndTokenise(text)
                for term in listTerm:
                    if term not in dictTerm:
                        dictTerm[term]=1
                    else:
                        dictTerm[term]+=1
            dictSbjTermFreq[subject] = dictTerm
        # construct textual index
        for sbjId, termFreq in dictSbjTermFreq.items():
            listObjId = idx_sbj_obj[sbjId]
            for term, freq in termFreq.items():
                if term not in inv_index:
                    objFreq = {}
                    for objId in listObjId:
                        if idx_id_object[str(objId)][0:4] == 'http':
                            objFreq[idx_id_object[str(objId)]] = [0,0,0,0,0,0,freq,len(termFreq),1]
                else:
                    objFreq = inv_index[term]
                    for objId in listObjId:
                        if idx_id_object[str(objId)][0:4] == 'http':
                            if idx_id_object[str(objId)] not in objFreq:
                                objFreq[idx_id_object[str(objId)]] = [0,0,0,0,0,0,freq,len(termFreq),1]
                            else:
                                objFreq[idx_id_object[str(objId)]][6] += freq
                                objFreq[idx_id_object[str(objId)]][7] += len(termFreq)
                                objFreq[idx_id_object[str(objId)]][8] += 1
                inv_index[term]=objFreq
        with open('inv_index', 'w') as fp:
            json.dump(inv_index, fp)
