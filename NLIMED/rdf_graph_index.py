"""MODUL: COLLECTING CELLML OR SBML DATA AND BUILD INDEX FOR SPARQL"""
from lxml import html
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring, parse
import time
from NLIMED.general import *

# List of file:
# listOfLinks.json # listOfTracks.txt # idx_pref_ns # idx_ns_pref # idx_id_pred # idx_id_subject
# idx_object_id # idx_subject_id # idx_id_object # cellMlData.json # rdfPaths.json
# restructureRdfPath.json


class IndexSPARQL(GeneralNLIMED):

    def __init__(self, repository):
        super(IndexSPARQL, self).__init__()
        # self.isUpdate = True if 'update' not in args else args['update']
        self.repository = repository

    def buildIndex(self, *args):
        if self.repository == 'pmr':
            self.__buildIndexPMR(*args)
        elif self.repository == 'bm':
            self.__buildIndexBM(*args)
        elif self.repository == 'bm-omex':
            self.__buildIndexBMOmex(*args)
        self._copyToIndexes([self.repository + '_idx_object_id', \
                self.repository + '_idx_subject_id', \
                self.repository + '_idx_obj_sbj', \
                self.repository + '_idx_sbjobj_tracks',\
                self.repository + '_idx_id_track', \
                self.repository + '_idx_id_pred', \
                self.repository + '_idx_pref_ns', \
                self.repository + '_idx_id_subject', \
                self.repository + '_idx_id_object', \
                self.repository + '_track.json'])

    def __buildIndexPMR(self, *args):
        # ALL PATHS IN cellml
        # cellmlPath data structure:
        # ['link':cellmlurl, 'namespace':[ns0,ns1,...] 'paths':[{'s':s0,'o':o0,'p':[p0]},{'s':s1,'o':o1,'p':[p1]},...,{'s':s2,'o':o2,'p':[p2]}]]
        # cellmlPaths data structure:
        #[cellmlPath0,cellmlPath1,cellmlPath2, ... ]
        if len(args) > 0:
            if args[0] == '-build':
                self.getAllCellmlLink()
                self.__getAllUrlContents()
                self.getAllRdfs()
                self.createIndexPrefix()
                self.createIndexPredicate()
                self.createIndexObjectAndSubject()
                self.restructureRdfPath()
                self.createIndexTrack()
                self.fullyRestructureRdfPath()
                self.createIndexObjectSubjectPair()
                return
            elif args[0] == '-skip':
                if len(args) > 1:
                    if args[1] == 'cellmlLinks':
                        self.__getAllUrlContents()
                        args[1] == 'getcellmlLinkContent'
                    if args[1] == 'getcellmlLinkContent':
                        self.getAllRdfs()
                        args[1] == 'getAllRdfs'
                    if args[1] == 'getAllRdfs':
                        self.createIndexPrefix()
                        args[1] == 'createIndexPrefix'
                    if args[1] == 'createIndexPrefix':
                        self.createIndexPredicate()
                        args[1] == 'createIndexPredicate'
                    if args[1] == 'createIndexPredicate':
                        self.createIndexObjectAndSubject()
                        args[1] == 'createIndexObjectAndSubject'
                    if args[1] == 'createIndexObjectAndSubject':
                        self.restructureRdfPath()
                        args[1] == 'restructureRdfPath'
                    if args[1] == 'restructureRdfPath':
                        self.createIndexTrack()
                        args[1] == 'createIndexTrack'
                    if args[1] == 'createIndexTrack':
                        self.fullyRestructureRdfPath()
                        args[1] == 'fullyRestructureRdfPath'
                    if args[1] == 'fullyRestructureRdfPath':
                        self.createIndexObjectSubjectPair()
                    return
                else:
                    print('-skip option is not complete (cellmlLinks|getcellmlLinkContent|getAllRdfs|createIndexPrefix|createIndexPredicate|createIndexObjectAndSubject|restructureRdfPath|createIndexTrack|fullyRestructureRdfPath)')
            print('Argument is not complete')
            print('-build ==> build index from the beginning')
            print('-skip {option} ==> update skip step')
            return

    def __buildIndexBM(self, *args):
        """GET SEQUENCE ON PATH BETWEEN THE MOST LEFT SUBJECT AND THE MOST RIGHT OBJECT"""
        def getSbjObjPaths(tree):
            children = tree.getchildren()
            if len(children) == 0:
                obj = ''
                for attrib, value in tree.attrib.items():
                    if 'http' == value[0:4]:
                        obj = value
                        break
                obj = tree.text if obj == '' and tree.text is not None else obj
                return [{'o': obj, 'p': []}]
            else:
                objects = []
                for child in children:
                    objAndPaths = getSbjObjPaths(child)
                    for objAndPath in objAndPaths:
                        tag = child.tag.replace('{', '').replace('}', '')
                        objAndPath['p'].insert(0, tag)
                    objects += objAndPaths
                return objects

        # get all rdfs for BioModels only
        seconds = time.time()
        dictMainSubjects = {}
        dictObjects = {}
        dictPredicates = {}
        dictTracks = {}
        namespaces = []
        entityTypes = set()
        count = 0
        path = args[-1]
        cellmlPaths = []
        threads = []
        # r=root, d=directories, f = files
        for r, d, files in os.walk(path):
            for file in files:
                file = os.path.join(r, file)
                root = parse(file).getroot()

                """get all main RDF subjects and path"""
                for rdfMainSubject in root:
                    if len(rdfMainSubject.attrib) > 0:
                        att = list(rdfMainSubject.attrib.keys())[0]
                        entityTypes.add(att)
                        mainSubject = rdfMainSubject.attrib[att]
                        # normalise subject
                        if mainSubject not in dictMainSubjects:
                            dictMainSubjects[mainSubject] = len(dictMainSubjects)
                        idSubj = dictMainSubjects[mainSubject]
                        objects = getSbjObjPaths(rdfMainSubject)
                        for obj in objects:
                            # normalising object
                            if obj['o'] not in dictObjects:
                                idObj = len(dictObjects)
                                dictObjects[obj['o']] = idObj
                            idObj = dictObjects[obj['o']]
                            # normalising track
                            track = tuple(obj['p'])
                            if track not in dictTracks:
                                idTrack = len(dictTracks)
                                dictTracks[track] = idTrack
                            idTrack = dictTracks[track]
                            cellmlPaths += [idSubj, idTrack, idObj]
                        # normalising predicate
                        for p in objects['p']:
                            dictPredicates[p] = dictPredicates[p] if p in dictPredicates else len(dictPredicates)

        self._saveBinaryInteger(cellmlPaths, 'tmp', self.repository + '_rdfPaths')
        self._dumpJson(dictMainSubjects, 'tmp', self.repository + '_subject.json')
        self._dumpJson(dictObjects, 'tmp', self.repository + '_object.json')
        self._dumpJson(dictPredicates, 'tmp', self.repository + '_predicate.json')

        # modify track so it store --> idTrack, [track]
        reverseDictTracks = {value: list(key)for key, value in dictTracks.items()}
        self._dumpJson(reverseDictTracks, 'tmp', self.repository + '_track.json')
        self._dumpJson(list(entityTypes), 'tmp', self.repository + '_entityTypes')
        print("Seconds since epoch =", time.time() - seconds)

    def __buildIndexBMOmex(self, *args):
        def getPathToObjs(s, g):
            pathToObjs = []
            tmpObjPath = {o:[p] for p, o in g.predicate_objects(subject=s)}
            while len(tmpObjPath) > 0:
                objKeys = tmpObjPath.copy()
                for o in objKeys:
                    children = list(g.predicate_objects(subject=o))
                    if len(children) == 0:
                        pathToObjs += [{'p': tmpObjPath[o], 'o': o}]
                    else:
                        for pred, obj in children:
                            tmpObjPath[obj] = tmpObjPath[o] + [pred]
                    del tmpObjPath[o]
            return pathToObjs

        # initialisation:
        seconds = time.time()
        sbjPathObjs = []
        rdfPaths = []
        dictTracks = {}
        dictObjects = {}
        dictEntities = {}
        dictPredicates = {}

        #load bm-omex rdf
        import io
        filename = os.path.join(self.currentPath, 'tmp', self.repository + '_rdf.rdf')
        with io.open(filename, 'r', encoding='"ISO-8859-1"') as f:
            text = f.read()
        g = rdflib.Graph()
        g.parse(data=text)

        #get all entities / subjects, objects, tracks:
        for s, p, o in g:
            if len(list(g.subject_predicates(object=s))) == 0:
                if s not in dictEntities:
                    dictEntities[s] = len(dictEntities)
                idSbj = dictEntities[s]
                predicates_objs = getPathToObjs(s, g)
                for predicates_obj in predicates_objs:
                    # normalised object
                    if predicates_obj['o'] not in dictObjects:
                        dictObjects[predicates_obj['o']] = len(dictObjects)
                    idObj = dictObjects[predicates_obj['o']]
                    # normalise track
                    track = tuple(predicates_obj['p'])
                    if track not in dictTracks:
                        dictTracks[track] = len(dictTracks)
                    idTrack = dictTracks[track]
                    rdfPaths += [idSbj, idTrack, idObj]

            dictPredicates[p] = dictPredicates[p] if p in dictPredicates else len(dictPredicates)

        self._saveBinaryInteger(rdfPaths, 'tmp', self.repository + '_rdfPaths')
        self._dumpJson(dictEntities, 'tmp', self.repository + '_subject.json')
        self._dumpJson(dictObjects, 'tmp', self.repository + '_object.json')
        self._dumpJson(dictPredicates, 'tmp', self.repository + '_predicate.json')

        # modify trac so it store --> idTrack, [track]
        reverseDictTracks = {value: list(key)for key, value in dictTracks.items()}
        self._dumpJson(reverseDictTracks, 'tmp', self.repository + '_track.json')
        print("Seconds since epoch =", time.time() - seconds)
        return rdfPaths

    def __getAllUrlContents(self):
        links = self._loadJson('tmp', self.repository + '_listOfLinks.json')
        data = self._loadJson('tmp', self.repository + '_cellMlData.json')
        for link, isUpdate in links.items():
            if bool(isUpdate):
                text = requests.get(link).text
                data[link] = text
        print(len(data))
        self._dumpJson(data, 'tmp', self.repository + '_cellMlData.json')

    # GET ALL cellml LINK FROM PROVIDED GRAPH
    def getCellmlLinks(self, url):
        r = requests.get(url)
        tree = html.fromstring(r.text)
        count = 0
        listLinks = []
        for item in tree.xpath("//span"):
            if 'wsfmenu' in item.classes:
                hrefs = item.xpath(".//a")
                for href in hrefs:
                    theLink = href.attrib['href']
                    if theLink[-7:] == '.cellml' or theLink[-4:] == '.rdf':
                        listLinks += [theLink.replace('/file/', '/rawfile/')]
                    elif '.' not in theLink[theLink.rfind('/'):len(theLink)]:
                        listLinks += self.getCellmlLinks(theLink)
        return listLinks

    # GET ALL cellml LINK FROM PMR WEBSITE
    def getAllCellmlLink(self):
        # check available link
        listLinks = {link: False for link in self._loadJson(
            'tmp', self.repository + '_listOfLinks.json')} if self.isUpdate else {}
        # get all graphs
        __queryGraph = """ SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o }}"""
        sparqlendpoint = 'https://models.physiomeproject.org/pmr2_virtuoso_search'
        sparql = SPARQLWrapper(sparqlendpoint)
        sparql.setQuery(__queryGraph)
        sparql.setReturnFormat(JSON)
        graphs = sparql.query().convert()
        # get list of cellml link by calling getCellmlLinks(url) function
        for key, items in graphs['results'].items():
            if not isinstance(items, (bool)):
                for item in items:
                    for key2, graph in item.items():
                        currLinks = self.getCellmlLinks(graph['value'])
                        for link in currLinks:
                            listLinks[link] = True if link not in listLinks else False
        self._dumpJson(listLinks, 'tmp', self.repository + '_listOfLinks.json')
        print('Number of cellml and rdf links with rdf is %d' % len(listLinks))

    # GET SEQUENCE ON PATH BETWEEN THE MOST LEFT SUBJECT AND THE MOST RIGHT OBJECT
    def getSbjObjPaths(self, tree, preds):
        children = tree.getchildren()
        ontoClass = ['/opb/', '/fma/', '/chebi/',
                     '/ma/', '/pr/', '/go/', '/cl/', '/obo/']
        if len(children) == 0:
            obj = ''
            for attrib, value in tree.attrib.items():
                if any(ont in value for ont in ontoClass):
                    obj = value
                    break
            obj = tree.text if obj == '' and tree.text is not None else obj
            return [{'o': obj, 'p': []}]
        else:
            objects = []
            for child in children:
                objAndPaths = self.getSbjObjPaths(child, preds)
                for objAndPath in objAndPaths:
                    tag = child.tag.replace('{', '').replace('}', '')
                    if tag in preds:
                        objAndPath['p'].insert(0, tag)
                objects += objAndPaths
            return objects

    # BUILD OF SIMPLIFIED RDF TRIPPLETS FROM GIVEN url
    def getAllRdfs(self):
        cellMlData = self._loadJson('tmp', self.repository + '_cellMlData.json')
        cellmlPaths = []
        for cellmlLink, content in cellMlData.items():
            try:
                root = ET.fromstring(content)
                rdfElement = root.findall(
                    '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF')
                if len(rdfElement) > 0:
                    paths = []
                    """get name spaces"""
                    rdfData = ''
                    namespaces = []
                    for element in rdfElement:
                        rdfData = tostring(element, encoding='unicode')
                        try:
                            rdf = rdflib.Graph().parse(data=rdfData, format='xml')
                            predicates = rdf.predicates(
                                subject=None, object=None)
                            preds = [p.n3()[1:-1] for p in predicates]
                        except Exception as e:
                            logger.error("some error")
                        namespaces = [ns[1]
                                      for ns in rdf.namespaces() if 'ns' in ns[0]]
                        """get all RDF roots in a cellml link"""
                        for rdfRoots in rdfElement:
                            """get all main RDF subjects and path"""
                            for rdfMainSubject in rdfRoots:
                                if '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about' in rdfMainSubject.attrib:
                                    mainSubject = rdfMainSubject.attrib[
                                        '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about']
                                    objects = self.getSbjObjPaths(
                                        rdfMainSubject, preds)
                                    for obj in objects:
                                        obj['s'] = mainSubject
                                        paths += [obj]
                    cellmlPaths += [{'link': cellmlLink,
                                     'namespaces': namespaces, 'paths': paths}]
            except:
                print("RDF format error: %s" % cellmlLink)
        self._dumpJson(cellmlPaths, 'tmp', self.repository + '_rdfPaths.json')
        return cellmlPaths

    def getNameSpaceAndVal(self, uri):
        pos = uri.find('#') if '#' in uri else uri.rfind('/')
        ns = uri[0:pos + 1]
        val = uri[pos + 1:]
        return (ns, val)

    def getNsIdAndVal(self, uri, index_ns_pref):
        pos = uri.find('#') if '#' in uri else uri.rfind('/')
        ns = index_ns_pref[uri[0:pos + 1]]
        val = uri[pos + 1:]
        return (ns, val)

    # BUILD INDEX Oi => Si, Si => Oi, Si+Oi => Psi, Psi => [Pi], Pi => P, Si => S, Oi => O, O => Oi, S => Si
    # index_pref_ns = {pref0:ns0, pref1:ns1, ...}
    # index_ns_pref = {ns0:pref0, ns1:pref1, ...}
    # index_predi_pred = {predId0:(pref0,val0), predId1:(pref1,val1), ...}
    # index_pred_predi = {(pref0,val0):predId0, (pref1,val1):predId0, ...}
    # index_object_oi = {obj0:objId0,obj1:objId1,...}
    # index_oi_object = {objId0:obj0,objId1:obj1,...}
    # index_subject_si = {sbj0:sbjId0,sbj1:sbjId1,...}
    # index_si_subject = {sbjId0:sbj0,sbjId1:sbj1,...}
    # index_tracki_track = {trackId0:[predId00,predId01,...],trackId1:[predId10,predId11,...], ...}
    # index_track_tracki = {[predId00,predId01,...]:trackId0,[predId10,predId11,...]:trackId1, ...}
    # index_obj_sbj = {idObj0:[idSbj01,idSbj02,...], idObj1:[idSbj11,idSbj12,...]}
    # index_sbj_obj = {idSbj0:[idObj01,idObj02,...], idSbj1:[idObj11,idObj12,...]}
    # index_sbjobj_tracks = [[sbj_id0,obj_id0]:[trackId00, trackId01,...],...,(sbj_id1,obj_id1):[trackId10, trackId11,...]]

    def createIndexPrefix(self):
        # create index of prefix and namespace
        data = self._loadJson('tmp', self.repository + '_rdfPaths.json')
        index_pref_ns = {}  # {pref0:ns0, pref1:ns1, ...}
        index_ns_pref = {}  # {ns0:pref0, ns1:pref1, ...}
        list_namespaces = []
        for cellmlPath in data:
            """get identified namespaces"""
            list_namespaces += [ns for ns in cellmlPath['namespaces']
                                if ns not in list_namespaces]
            """get unidentified namespaces"""
            for paths in cellmlPath['paths']:
                for pred in paths['p']:
                    predNsVal = self.getNameSpaceAndVal(pred)
                    list_namespaces += [predNsVal[0]
                                        ] if predNsVal[0] not in list_namespaces else []
        #         list_namespaces = list(set(list_namespaces))
        print('# of distinct namespace %d' % len(list_namespaces))
        for i in range(len(list_namespaces)):
            index_pref_ns[i] = list_namespaces[i]
            index_ns_pref[list_namespaces[i]] = i
        self._dumpJson(index_pref_ns, 'tmp', self.repository + '_idx_pref_ns')
        self._dumpJson(index_ns_pref, 'tmp', self.repository + '_idx_ns_pref')

    def createIndexPredicate(self):
        # create index of predicate
        data = self._loadJson('tmp', self.repository + '_rdfPaths.json')
        index_ns_pref = self._loadJson('tmp', self.repository + '_idx_ns_pref')
        # {predId0:(pref0,val0), predId1:(pref1,val1), ...}
        index_predi_pred = {}
        # {(pref0,val0):predId0, (pref1,val1):predId1, ...}
        index_pred_predi = {}
        list_predicate = []
        list_ns = list(index_ns_pref.keys())
        for cellmlPath in data:
            for paths in cellmlPath['paths']:
                for pred in paths['p']:
                    predNsVal = self.getNameSpaceAndVal(pred)
                    if predNsVal[0] in list_ns:
                        list_predicate += [(index_ns_pref[predNsVal[0]],
                                            predNsVal[1])]
                    else:
                        list_predicate += [(-1, predNsVal[1])]
        list_predicate = list(set(list_predicate))
        print('# of distinct predicate %d' % len(list_predicate))
        for i in range(len(list_predicate)):
            index_predi_pred[i] = list_predicate[i]
        self._dumpJson(index_predi_pred, 'tmp', self.repository + '_idx_id_pred')
        # save predicate to file
        index_pref_ns = self._loadJson('tmp', self.repository + '_idx_pref_ns')
        dictPredicates = {}
        for k, pred in index_predi_pred.items():
            dictPredicates[index_pref_ns[str(pred[0])] + pred[1]] = k
        self._dumpJson(dictPredicates, 'tmp', self.repository + '_predicate.json')

    def createIndexObjectAndSubject(self):
        # create index of object and index of subject
        data = self._loadJson('tmp', self.repository + '_rdfPaths.json')
        index_object_oi = {}  # {obj0:objId0,obj1:objId1,...}
        index_oi_object = {}  # {objId0:obj0,objId1:obj1,...}
        index_subject_si = {}  # {sbj0:sbjId0,sbj1:sbjId1,...}
        index_si_subject = {}  # {sbjId0:sbj0,sbjId1:sbj1,...}
        list_object = []
        list_subject = []
        for cellmlPath in data:
            for path in cellmlPath['paths']:
                obj = path['o']
                list_object += [obj]
                sbj = path['s']
                list_subject += [sbj]
        list_object = list(set(list_object))
        list_subject = list(set(list_subject))
        for i in range(len(list_object)):
            index_object_oi[list_object[i]] = i
            index_oi_object[i] = list_object[i]
        for i in range(len(list_subject)):
            index_subject_si[list_subject[i]] = i
            index_si_subject[i] = list_subject[i]
        print('# of distinct object %d' % len(index_object_oi))
        print('# of distinct subject %d' % len(index_si_subject))
        self._dumpJson(index_oi_object, 'tmp', self.repository + '_idx_id_object')
        self._dumpJson(index_object_oi, 'tmp', self.repository + '_idx_object_id')
        self._dumpJson(index_si_subject, 'tmp', self.repository + '_idx_id_subject')
        self._dumpJson(index_subject_si, 'tmp', self.repository + '_idx_subject_id')
        # save obj to file
        self._saveToFlatFile(list_object, 'tmp', self.repository + '_listOfObjects.txt')
        # save sbj to file
        self._saveToFlatFile(list_subject, 'tmp', self.repository + '_listOfSubjects.txt')

    def restructureRdfPath(self):
        # restructured cellmlPaths so it only contains id, not full text
        # cellMlPath=['link':cellmlurl, 'namespace':[ns0,ns1,...] 'paths':[{'s':s0,'o':o0,'p':[p0]},{'s':s1,'o':o1,'p':[p1]},...,{'s':s2,'o':o2,'p':[p2]}]]
        # res_cellMlPaths = [[sbjId0,objId0,[predId00,predId01,...]] ... [sbjIdn,objIdn,[predIdn0,predIdn1,...]]]
        data = self._loadJson('tmp', self.repository + '_rdfPaths.json')
        index_object_oi = self._loadJson('tmp', self.repository + '_idx_object_id')
        index_subject_si = self._loadJson('tmp', self.repository + '_idx_subject_id')
        index_ns_pref = self._loadJson('tmp', self.repository + '_idx_ns_pref')
        index_id_pred = self._loadJson('tmp', self.repository + '_idx_id_pred')
        index_pred_predi = {}
        for key, val in index_id_pred.items():
            index_pred_predi[tuple(val)] = key
        restructuredPaths = []
        for cellmlPath in data:
            for path in cellmlPath['paths']:
                obj = path['o']
                sbj = path['s']
                obj_id = index_object_oi[obj]
                sbj_id = index_subject_si[sbj]
                pred_ids = []
                for pred in path['p']:
                    predNsIdAndVal = self.getNsIdAndVal(pred, index_ns_pref)
                    pred_id = index_pred_predi[predNsIdAndVal]
                    pred_ids += [pred_id]
                restructuredPaths += [[sbj_id, obj_id, tuple(pred_ids)]]
        print('# of path %d' % len(restructuredPaths))
        self._dumpJson(restructuredPaths, 'tmp', self.repository + '_restructureRdfPath.json')

    def createIndexTrack(self):
        # create index of track
        data = self._loadJson('tmp', self.repository + '_restructureRdfPath.json')
        # {trackId0:[predId00,predId01,...],trackId1:[predId10,predId11,...], ...}
        index_tracki_track = {}
        list_track = []
        for res_cellMlPath in data:
            list_track += [tuple(res_cellMlPath[2])]
        list_track = list(set(list_track))
        for i in range(len(list_track)):
            index_tracki_track[i] = list_track[i]
        print('# of distinct track %d' % len(index_tracki_track))
        # save to index file
        self._dumpJson(index_tracki_track, 'tmp', self.repository + '_idx_id_track')
        # save track to file
        self._saveToFlatFile(list_track, 'tmp', self.repository + '_listOfTracks.txt')

    def fullyRestructureRdfPath(self):
        # restructure res_cellMlPath so it fully contain subject id, object id, and list of track id
        # res_res_cellMlPath = [[sid0,oid0,trackid0] ... [sidn,oidn,trackidn]]
        # then removing any duplicate
        data = self._loadJson('tmp', self.repository + '_restructureRdfPath.json')
        index_track_tracki = {}
        index_tracki_track = self._loadJson('tmp', self.repository + '_idx_id_track')
        for key, val in index_tracki_track.items():
            index_track_tracki[tuple(val)] = key
        fullyResPaths = []
        for res_cellMlPath in data:
            sbj_id = res_cellMlPath[0]
            obj_id = res_cellMlPath[1]
            track_id = index_track_tracki[tuple(res_cellMlPath[2])]
            fullyResPaths += [((sbj_id, obj_id), track_id)]
        fullyResPaths = list(set(fullyResPaths))
        print('# of distinct path %d' % len(fullyResPaths))
        self._dumpJson(fullyResPaths, 'tmp', self.repository + '_fullyRestructureRdfPath.json')

    def createIndexObjectSubjectPair(self):
        # create index of object=>subject, subject=>object, subject,object=>predicate
        data = self._loadJson('tmp', self.repository + '_fullyRestructureRdfPath.json')
        # {idObj0:[idSbj01,idSbj02,...], idObj1:[idSbj11,idSbj12,...]}
        index_obj_sbj = {}
        # {idSbj0:[idObj01,idObj02,...], idSbj1:[idObj11,idObj12,...]}
        index_sbj_obj = {}
        list_sbj_obj = []
        for path in data:
            list_sbj_obj += [tuple(path[0])]
        list_sbj_obj = list(set(list_sbj_obj))
        for sbj_id, obj_id in list_sbj_obj:
            index_obj_sbj[obj_id] = [
                sbj_id] if obj_id not in index_obj_sbj else index_obj_sbj[obj_id] + [sbj_id]
            index_sbj_obj[sbj_id] = [
                obj_id] if sbj_id not in index_sbj_obj else index_sbj_obj[sbj_id] + [obj_id]
        # create index of subject,object=>tracks
        # {(sbj_id0,obj_id0):[trackId00, trackId01,...],...,(sbj_id1,obj_id1):[trackId10, trackId11,...]}
        index_sbjobj_tracks = {}
        for path in data:
            key = tuple(path[0])
            listTrack = path[1]
            if key not in index_sbjobj_tracks:
                index_sbjobj_tracks[key] = [listTrack]
            else:
                index_sbjobj_tracks[key] = index_sbjobj_tracks[key] + [listTrack]
        print('# of distinct subject-object pair %d' %
              len(index_sbjobj_tracks))
        self._dumpJson(index_obj_sbj, 'tmp', self.repository + '_idx_obj_sbj')
        self._dumpJson(index_sbj_obj, 'tmp', self.repository + '_idx_sbj_obj')
        tmp_index_sbjobj_tracks = []
        for key, val in index_sbjobj_tracks.items():
            tmp_index_sbjobj_tracks += [[list(key), val]]
        self._dumpJson(tmp_index_sbjobj_tracks, 'tmp', self.repository + '_idx_sbjobj_tracks')
