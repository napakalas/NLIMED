"""MODUL: COLLECTING CELLML DATA AND BUILD INDEX FOR SPARQL"""
import requests
from lxml import html
from SPARQLWrapper import SPARQLWrapper, JSON
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring
import rdflib
import json
import copy

"""
List of file:
 listOfLinks.json
 listOfTracks.txt
 idx_pref_ns
 idx_ns_pref
 idx_id_pred
 idx_id_subject
 idx_object_id
 idx_subject_id
 idx_id_object
 cellMlData.json
 rdfPaths.json
"""

# restructureRdfPath.json
class IndexSPARQL:
    def buildIndex(self,*args):
        """
        ALL PATHS IN cellml
        cellmlPath data structure:
        ['link':cellmlurl, 'namespace':[ns0,ns1,...] 'paths':[{'s':s0,'o':o0,'p':[p0]},{'s':s1,'o':o1,'p':[p1]},...,{'s':s2,'o':o2,'p':[p2]}]]
        cellmlPaths data structure:
        [cellmlPath0,cellmlPath1,cellmlPath2, ... ]
        """
        if len(args)>0:
            if args[0]=='-build':
                self.getAllCellmlLink()
                self.getAllUrlContents()
                self.getAllRdfs()
                self.createIndexPrefix()
                self.createIndexPredicate()
                self.createIndexObjectAndSubject()
                self.restructureRdfPath()
                self.createIndexTrack()
                self.fullyRestructureRdfPath()
                self.createIndexObjectSubjectPair()
                return
            elif args[0]=='-skip':
                if len(args)>1:
                    if args[1] == 'cellmlLinks':
                        self.getAllUrlContents()
                    if args[1] == 'getcellmlLinkContent' or args[1] == 'cellmlLinks':
                        self.getAllRdfs()
                    if args[1] == 'getAllRdfs' or args[1] == 'getcellmlLinkContent' or args[1] == 'cellmlLinks':
                        self.createIndexPrefix()
                    if args[1] == 'createIndexPrefix' or args[1] == 'getAllRdfs' or args[1] == 'getcellmlLinkContent' or args[1] == 'cellmlLinks':
                        self.createIndexPredicate()
                    if args[1] == 'createIndexPredicate' or args[1] == 'createIndexPrefix' or args[1] == 'getAllRdfs' or args[1] == 'getcellmlLinkContent' or args[1] == 'cellmlLinks':
                        self.createIndexObjectAndSubject()
                    if args[1] == 'createIndexObjectAndSubject' or args[1] == 'createIndexPredicate' or args[1] == 'createIndexPrefix' or args[1] == 'getAllRdfs' or args[1] == 'getcellmlLinkContent' or args[1] == 'cellmlLinks':
                        self.restructureRdfPath()
                    if args[1] == 'restructureRdfPath' or args[1] == 'createIndexObjectAndSubject' or args[1] == 'createIndexPredicate' or args[1] == 'createIndexPrefix' or args[1] == 'getAllRdfs' or args[1] == 'getcellmlLinkContent' or args[1] == 'cellmlLinks':
                        self.createIndexTrack()
                    if args[1] == 'createIndexTrack' or args[1] == 'restructureRdfPath' or args[1] == 'createIndexObjectAndSubject' or args[1] == 'createIndexPredicate' or args[1] == 'createIndexPrefix' or args[1] == 'getAllRdfs' or args[1] == 'getcellmlLinkContent' or args[1] == 'cellmlLinks':
                        self.fullyRestructureRdfPath()
                    if args[1] == 'fullyRestructureRdfPath' or args[1] == 'createIndexTrack' or args[1] == 'restructureRdfPath' or args[1] == 'createIndexObjectAndSubject' or args[1] == 'createIndexPredicate' or args[1] == 'createIndexPrefix' or args[1] == 'getAllRdfs' or args[1] == 'getcellmlLinkContent' or args[1] == 'cellmlLinks':
                        self.createIndexObjectSubjectPair()
                    return
                else:
                    print('-skip option is not complete (cellmlLinks|getcellmlLinkContent|getAllRdfs|createIndexPrefix|createIndexPredicate|createIndexObjectAndSubject|restructureRdfPath|createIndexTrack|fullyRestructureRdfPath)')
            print('Argument is not complete')
            print('-build ==> build index from the beginning')
            print('-skip {option} ==> update skip step')
            return

    def saveToFlatFile(self, data, fileName):
        f = open(fileName, 'w+')
        for datum in data:
            f.write(str(datum).replace('\n',' ').replace('\r',' ')+'\n')
        f.close()

    def loadFromFlatFile(self, fileName):
        try:
            f = open(fileName, 'r')
            return f.readlines()
        except:
            return []

    def loadJson(self, fileName):
        with open(fileName, 'r') as fp:
            data = json.load(fp)
        return data

    def dumpJson(self, data, fileName):
        with open(fileName, 'w') as fp:
            json.dump(data, fp)

    def getAllUrlContents(self):
        cellMlLinks = self.loadJson('listOfLinks.json')
        data = {}
        for cellMlLink in cellMlLinks:
            text = requests.get(cellMlLink).text
            data[cellMlLink] = text
        self.dumpJson(data,'cellMlData.json')


    #GET ALL cellml LINK FROM PROVIDED GRAPH
    def getCellmlLinks(self,url):
        r = requests.get(url)
        tree = html.fromstring(r.text)
        count=0
        listLinks = []
        for item in tree.xpath("//span"):
            if 'wsfmenu' in item.classes:
                hrefs = item.xpath(".//a")
                for href in hrefs:
                    theLink = href.attrib['href']
                    if theLink[len(theLink)-7:len(theLink)] == '.cellml':
                        listLinks += [theLink.replace('/file/','/rawfile/')]
                    elif '.' not in theLink[theLink.rfind('/'):len(theLink)]:
                        listLinks += self.getCellmlLinks(theLink)
        return listLinks

    #GET ALL cellml LINK FROM PMR WEBSITE
    def getAllCellmlLink(self):
        #get all graphs
        __queryGraph = """ SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o }}"""
        sparqlendpoint = 'https://models.physiomeproject.org/pmr2_virtuoso_search'
        sparql = SPARQLWrapper(sparqlendpoint)
        sparql.setQuery(__queryGraph)
        sparql.setReturnFormat(JSON)
        graphs = sparql.query().convert()
        #get list of cellml link by calling getCellmlLinks(url) function
        listLinks = []
        for key, items in graphs['results'].items():
            if not isinstance(items,(bool)):
                for item in items:
                    for key2, graph in item.items():
                        listLinks += self.getCellmlLinks(graph['value'])
        self.dumpJson(listLinks,'listOfLinks.json')
        print('Number of cellml links with rdf is %d'%len(listLinks))
        return listLinks

    #GET SEQUENCE ON PATH BETWEEN THE MOST LEFT SUBJECT AND THE MOST RIGHT OBJECT
    def getSbjObjPaths(self,tree,preds):
        children = tree.getchildren()
        if len(children) == 0:
            if '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource' in tree.attrib:
                obj = tree.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource']
            elif tree.text is not None:
                obj = tree.text
            else:
                obj = ''
            return [{'o':obj,'p':[]}]
        else:
            objects= []
            for child in children:
                objAndPaths = self.getSbjObjPaths(child,preds)
                for objAndPath in objAndPaths:
                    tag = child.tag.replace('{','').replace('}','')
                    if tag in preds:
                        objAndPath['p'].insert(0,tag)
                objects += objAndPaths
            return objects

    #BUILD OF SIMPLIFIED RDF TRIPPLETS FROM GIVEN url
    def getAllRdfs(self):
        cellMlData = self.loadJson('cellMlData.json')
        cellmlPaths=[]
        for cellmlLink, content in cellMlData.items():
            root = ET.fromstring(content)
            rdfElement = root.findall('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF')
            if len(rdfElement) > 0:
                paths = []
                """get name spaces"""
                rdfData = ''
                namespaces = []
                for element in rdfElement:
                    rdfData = tostring(element, encoding='unicode')
                    try:
                        rdf = rdflib.Graph().parse(data=rdfData,format='xml')
                        predicates = rdf.predicates(subject=None, object=None)
                        preds = [p.n3()[1:-1] for p in predicates]
                    except Exception as e:
                        logger.error('Failed to upload to ftp: '+ str(e))
                    namespaces = [ns[1] for ns in rdf.namespaces() if 'ns' in ns[0]]
                    """get all RDF roots in a cellml link"""
                    for rdfRoots in rdfElement:
                        """get all main RDF subjects and path"""
                        for rdfMainSubject in rdfRoots:
                            if '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about' in rdfMainSubject.attrib:
                                mainSubject = rdfMainSubject.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about']
                                objects = self.getSbjObjPaths(rdfMainSubject,preds)
                                for obj in objects:
                                    obj['s'] = mainSubject
                                    paths += [obj]
                cellmlPaths +=[{'link':cellmlLink,'namespaces':namespaces,'paths':paths}]
        self.dumpJson(cellmlPaths,'rdfPaths.json')
        return cellmlPaths

    def getNameSpaceAndVal(self,uri):
        pos= uri.find('#') if '#' in uri else uri.rfind('/')
        ns = uri[0:pos+1]
        val = uri[pos+1:]
        return (ns,val)

    def getNsIdAndVal(self,uri,index_ns_pref):
        pos= uri.find('#') if '#' in uri else uri.rfind('/')
        ns = index_ns_pref[uri[0:pos+1]]
        val = uri[pos+1:]
        return (ns,val)

    """
    #BUILD INDEX Oi => Si, Si => Oi, Si+Oi => Psi, Psi => [Pi], Pi => P, Si => S, Oi => O, O => Oi, S => Si
     index_pref_ns = {pref0:ns0, pref1:ns1, ...}
     index_ns_pref = {ns0:pref0, ns1:pref1, ...}
     index_predi_pred = {predId0:(pref0,val0), predId1:(pref1,val1), ...}
     index_pred_predi = {(pref0,val0):predId0, (pref1,val1):predId0, ...}
     index_object_oi = {obj0:objId0,obj1:objId1,...}
     index_oi_object = {objId0:obj0,objId1:obj1,...}
     index_subject_si = {sbj0:sbjId0,sbj1:sbjId1,...}
     index_si_subject = {sbjId0:sbj0,sbjId1:sbj1,...}
     index_tracki_track = {trackId0:[predId00,predId01,...],trackId1:[predId10,predId11,...], ...}
     index_track_tracki = {[predId00,predId01,...]:trackId0,[predId10,predId11,...]:trackId1, ...}
     index_obj_sbj = {idObj0:[idSbj01,idSbj02,...], idObj1:[idSbj11,idSbj12,...]}
     index_sbj_obj = {idSbj0:[idObj01,idObj02,...], idSbj1:[idObj11,idObj12,...]}
     index_sbjobj_tracks = [[sbj_id0,obj_id0]:[trackId00, trackId01,...],...,(sbj_id1,obj_id1):[trackId10, trackId11,...]]
    """

    def createIndexPrefix(self):
        #create index of prefix and namespace
        with open('rdfPaths.json', 'r') as fp:
            data = json.load(fp)
        index_pref_ns = {} # {pref0:ns0, pref1:ns1, ...}
        index_ns_pref = {} # {ns0:pref0, ns1:pref1, ...}
        list_namespaces = []
        for cellmlPath in data:
            """get identified namespaces"""
            list_namespaces += [ns for ns in cellmlPath['namespaces'] if ns not in list_namespaces]
            """get unidentified namespaces"""
            for paths in cellmlPath['paths']:
                for pred in paths['p']:
                    predNsVal = self.getNameSpaceAndVal(pred)
                    list_namespaces+=[predNsVal[0]] if predNsVal[0] not in list_namespaces else []
#         list_namespaces = list(set(list_namespaces))
        print('# of distinct namespace %d'%len(list_namespaces))
        for i in range(len(list_namespaces)):
            index_pref_ns[i] = list_namespaces[i]
            index_ns_pref[list_namespaces[i]] = i
        with open('idx_pref_ns', 'w') as fp:
            json.dump(index_pref_ns,fp)
        with open('idx_ns_pref', 'w') as fp:
            json.dump(index_ns_pref,fp)

    def createIndexPredicate(self):
        #create index of predicate
        with open('rdfPaths.json', 'r') as fp:
            data = json.load(fp)
        with open('idx_ns_pref', 'r') as fp:
            index_ns_pref = json.load(fp)
        index_predi_pred = {} # {predId0:(pref0,val0), predId1:(pref1,val1), ...}
        index_pred_predi = {} # {(pref0,val0):predId0, (pref1,val1):predId1, ...}
        list_predicate = []
        list_ns = list(index_ns_pref.keys())
        for cellmlPath in data:
            for paths in cellmlPath['paths']:
                for pred in paths['p']:
                    predNsVal = self.getNameSpaceAndVal(pred)
                    if predNsVal[0] in list_ns:
                        list_predicate +=[(index_ns_pref[predNsVal[0]],predNsVal[1])]
                    else:
                        list_predicate +=[(-1,predNsVal[1])]
        list_predicate = list(set(list_predicate))
        print('# of distinct predicate %d'%len(list_predicate))
        for i in range(len(list_predicate)):
            index_predi_pred[i] = list_predicate[i]
        with open('idx_id_pred', 'w') as fp:
            json.dump(index_predi_pred,fp)
        #save predicate to file
        with open('idx_pref_ns', 'r') as fp:
            index_pref_ns = json.load(fp)
        myPredList=[]
        for myPred in list_predicate:
            myPredList+=[index_pref_ns[str(myPred[0])]+myPred[1]]
        self.saveToFlatFile(myPredList, 'listOfPredicates.txt')

    def createIndexObjectAndSubject(self):
        #create index of object and index of subject
        with open('rdfPaths.json', 'r') as fp:
            data = json.load(fp)
        index_object_oi = {} # {obj0:objId0,obj1:objId1,...}
        index_oi_object = {} # {objId0:obj0,objId1:obj1,...}
        index_subject_si = {} # {sbj0:sbjId0,sbj1:sbjId1,...}
        index_si_subject = {} # {sbjId0:sbj0,sbjId1:sbj1,...}
        list_object = []
        list_subject = []
        for cellmlPath in data:
            for path in cellmlPath['paths']:
                obj = path['o']
                list_object+=[obj]
                sbj = path['s']
                list_subject+=[sbj]
        list_object = list(set(list_object))
        list_subject = list(set(list_subject))
        for i in range(len(list_object)):
            index_object_oi[list_object[i]]=i
            index_oi_object[i]=list_object[i]
        for i in range(len(list_subject)):
            index_subject_si[list_subject[i]]=i
            index_si_subject[i]=list_subject[i]
        print('# of distinct object %d'%len(index_object_oi))
        print('# of distinct subject %d'%len(index_si_subject))
        with open('idx_id_object', 'w') as fp:
            json.dump(index_oi_object,fp)
        with open('idx_object_id', 'w') as fp:
            json.dump(index_object_oi,fp)
        with open('idx_id_subject', 'w') as fp:
            json.dump(index_si_subject,fp)
        with open('idx_subject_id', 'w') as fp:
            json.dump(index_subject_si,fp)
        #save obj to file
        self.saveToFlatFile(list_object, 'listOfObjects.txt')
        #save sbj to file
        self.saveToFlatFile(list_subject, 'listOfSubjects.txt')

    def restructureRdfPath(self):
        #restructured cellmlPaths so it only contains id, not full text
        #cellMlPath=['link':cellmlurl, 'namespace':[ns0,ns1,...] 'paths':[{'s':s0,'o':o0,'p':[p0]},{'s':s1,'o':o1,'p':[p1]},...,{'s':s2,'o':o2,'p':[p2]}]]
        #res_cellMlPaths = [[sbjId0,objId0,[predId00,predId01,...]] ... [sbjIdn,objIdn,[predIdn0,predIdn1,...]]]
        with open('rdfPaths.json', 'r') as fp:
            data = json.load(fp)
        with open('idx_object_id', 'r') as fp:
            index_object_oi = json.load(fp)
        with open('idx_subject_id', 'r') as fp:
            index_subject_si = json.load(fp)
        with open('idx_ns_pref', 'r') as fp:
            index_ns_pref = json.load(fp)
        with open('idx_id_pred', 'r') as fp:
            index_id_pred = json.load(fp)
        index_pred_predi={}
        for key, val in index_id_pred.items():
            index_pred_predi[tuple(val)]=key
        restructuredPaths = []
        for cellmlPath in data:
            for path in cellmlPath['paths']:
                obj = path['o']
                sbj = path['s']
                obj_id = index_object_oi[obj]
                sbj_id = index_subject_si[sbj]
                pred_ids = []
                for pred in path['p']:
                    predNsIdAndVal = self.getNsIdAndVal(pred,index_ns_pref)
                    pred_id = index_pred_predi[predNsIdAndVal]
                    pred_ids+=[pred_id]
                restructuredPaths+=[[sbj_id,obj_id,tuple(pred_ids)]]
        print('# of path %d'%len(restructuredPaths))
        with open('restructureRdfPath.json', 'w') as fp:
            json.dump(restructuredPaths,fp)

    def createIndexTrack(self):
        #create index of track
        data = self.loadJson('restructureRdfPath.json')
        index_tracki_track = {} # {trackId0:[predId00,predId01,...],trackId1:[predId10,predId11,...], ...}
        list_track = []
        for res_cellMlPath in data:
            list_track += [tuple(res_cellMlPath[2])]
        list_track = list(set(list_track))
        for i in range(len(list_track)):
            index_tracki_track[i] = list_track[i]
        print('# of distinct track %d'%len(index_tracki_track))
        #save to index file
        self.dumpJson(index_tracki_track,'idx_id_track')
        #save track to file
        self.saveToFlatFile(list_track, 'listOfTracks.txt')

    def fullyRestructureRdfPath(self):
        #restructure res_cellMlPath so it fully contain subject id, object id, and list of track id
        #res_res_cellMlPath = [[sid0,oid0,trackid0] ... [sidn,oidn,trackidn]]
        #then removing any duplicate
        data = self.loadJson('restructureRdfPath.json')
        index_track_tracki={}
        index_tracki_track = self.loadJson('idx_id_track')
        for key, val in index_tracki_track.items():
            index_track_tracki[tuple(val)]=key
        fullyResPaths=[]
        for res_cellMlPath in data:
            sbj_id = res_cellMlPath[0]
            obj_id = res_cellMlPath[1]
            track_id = index_track_tracki[tuple(res_cellMlPath[2])]
            fullyResPaths += [((sbj_id, obj_id), track_id)]
        fullyResPaths=list(set(fullyResPaths))
        print('# of distinct path %d'%len(fullyResPaths))
        self.dumpJson(fullyResPaths,'fullyRestructureRdfPath.json')

    def createIndexObjectSubjectPair(self):
        #create index of object=>subject, subject=>object, subject,object=>predicate
        data = self.loadJson('fullyRestructureRdfPath.json')
        index_obj_sbj = {} # {idObj0:[idSbj01,idSbj02,...], idObj1:[idSbj11,idSbj12,...]}
        index_sbj_obj = {} # {idSbj0:[idObj01,idObj02,...], idSbj1:[idObj11,idObj12,...]}
        list_sbj_obj = []
        for path in data:
            list_sbj_obj+=[tuple(path[0])]
        list_sbj_obj = list(set(list_sbj_obj))
        for sbj_id, obj_id in list_sbj_obj:
            index_obj_sbj[obj_id] = [sbj_id] if obj_id not in index_obj_sbj else index_obj_sbj[obj_id]+[sbj_id]
            index_sbj_obj[sbj_id] = [obj_id] if sbj_id not in index_sbj_obj else index_sbj_obj[sbj_id]+[obj_id]
        #create index of subject,object=>tracks
        index_sbjobj_tracks = {} # {(sbj_id0,obj_id0):[trackId00, trackId01,...],...,(sbj_id1,obj_id1):[trackId10, trackId11,...]}
        for path in data:
            key = tuple(path[0])
            listTrack = path[1]
            if key not in index_sbjobj_tracks:
                index_sbjobj_tracks[key] = [listTrack]
            else:
                index_sbjobj_tracks[key] = index_sbjobj_tracks[key]+[listTrack]
        print('# of distinct subject-object pair %d'%len(index_sbjobj_tracks))
        self.dumpJson(index_obj_sbj,'idx_obj_sbj')
        self.dumpJson(index_sbj_obj,'idx_sbj_obj')
        tmp_index_sbjobj_tracks = []
        for key, val in index_sbjobj_tracks.items():
            tmp_index_sbjobj_tracks+=[[list(key),val]]
        self.dumpJson(tmp_index_sbjobj_tracks,'idx_sbjobj_tracks')
