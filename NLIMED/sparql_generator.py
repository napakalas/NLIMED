"""MODUL: SPARQL GENERATOR"""
import itertools
from pprint import pformat
from textwrap import indent
from NLIMED.general import *
from rdflib import Graph

class SPARQLGenerator(GeneralNLIMED):
    def __init__(self, repository):
        super(SPARQLGenerator, self).__init__()
        self.repository = repository
        self.__setupSPARQLEP()
        if repository == 'pmr':
            self.__initPMR()
        elif repository in ['bm','bm-omex']:
            self.__init_BM_BMOmex()

    def __initPMR(self):  # initialisation of PMR
        self.idxs = {}
        self.idxs['object_id'] = self._loadJson('indexes',self.repository + '_idx_object_id')
        self.idxs['subject_id'] = self._loadJson('indexes',self.repository + '_idx_subject_id')
        self.idxs['obj_sbj'] = self._loadJson('indexes',self.repository + '_idx_obj_sbj')
        self.idxs['sbjobj_tracks'] = {tuple(sbjobj_track[0]):sbjobj_track[1] for sbjobj_track in self._loadJson('indexes',self.repository + '_idx_sbjobj_tracks')}
        self.idxs['id_track'] = self._loadJson('indexes',self.repository + '_idx_id_track')
        self.idxs['id_pred'] = self._loadJson('indexes',self.repository + '_idx_id_pred')
        self.idxs['pref_ns'] = self._loadJson('indexes',self.repository + '_idx_pref_ns')
        self.idxs['id_object'] = self._loadJson('indexes',self.repository + '_idx_id_object')
        self.idxs['id_subject'] = self._loadJson('indexes',self.repository + '_idx_id_subject')
        # initialized based query for each subject
        self.header = 'SELECT ?graph ?Model_entity ?desc WHERE { GRAPH ?graph {{ '
        self.union = ' } UNION { '
        self.tail = [' ?Model_entity <http://purl.org/dc/terms/description> ?desc . ',
                     ' FILTER NOT EXISTS {?Model_entity <http://purl.org/dc/terms/description> ?dsc .} ']
        self.closer = ' }}} '

    def __init_BM_BMOmex(self):  # initialisation of BioModels or OMEX-BioModels
        self.idxs = {}
        self.idxs['id_object'] = self._loadJson('indexes',self.repository + '_object.json')
        self.idxs['object_id'] = {val: key for key, val in self.idxs['id_object'].items()}
        self.idxs['obj_sbj'] = {}
        self.idxs['sbjobj_track'] = {}
        self.idxs['id_track'] = self._loadJson('indexes',self.repository + '_track.json')
        self.idxs['id_pred'] =  self._loadJson('indexes',self.repository + '_predicate.json')
        rdfPath = self._loadBinaryInteger('indexes',self.repository + '_rdfPaths')
        for i in range(0, len(rdfPath), 3):
            sbj, track, obj = rdfPath[i], rdfPath[i + 1], rdfPath[i + 2]
            self.idxs['obj_sbj'][obj] = self.idxs['obj_sbj'][obj] if obj in self.idxs['obj_sbj'] else set()
            self.idxs['obj_sbj'][obj].add(sbj)
            self.idxs['sbjobj_track'][(sbj, obj)] = self.idxs['sbjobj_track'][(
                sbj, obj)] if (sbj, obj) in self.idxs['sbjobj_track'] else set()
            self.idxs['sbjobj_track'][(sbj, obj)].add(track)
        # initialized based query for each subject
        if self.repository == 'bm':
            self.select = 'SELECT ?model ?type ?element ?notes ?name '
            self.where = """
                WHERE {
                    ?model ?type ?element ."""
            # get id predicate description
            self.whereOptional = {' OPTIONAL{?element <http://identifiers.org/biomodels.vocabulary#notes> ?notas .}  BIND(COALESCE(?notas, "") as ?notes) ',
                                  ' OPTIONAL{?element <http://identifiers.org/biomodels.vocabulary#name> ?nama .}  BIND(COALESCE(?nama, "") as ?name) '}
        elif self.repository == 'bm-omex':
            self.select = 'SELECT ?graph ?element WHERE { GRAPH ?graph { '
            self.closer = ' }} '

    def __setupSPARQLEP(self):
        """
            Setup endpoint executing the SOARQL
        """
        if self.repository == 'pmr':
            sparqlendpoint = 'https://models.physiomeproject.org/pmr2_virtuoso_search'
            self.sparqlEP = SPARQLWrapper(sparqlendpoint)
        elif self.repository == 'bm':
            sparqlendpoint = 'https://www.ebi.ac.uk/rdf/services/sparql'
            self.sparqlEP = SPARQLWrapper(sparqlendpoint)
        elif self.repository == 'bm-omex':
            sparqlendpoint = 'https://teaching.physiomeproject.org/pmr2_virtuoso_search'
            self.sparqlEP = SPARQLWrapper(sparqlendpoint)
            self.sparqlEP.setHTTPAuth(BASIC)
            self.sparqlEP.setCredentials("tbs", "andreshouse123_")
            self.sparqlEP.setMethod(POST)
            self.sparqlEP.setReturnFormat(JSON)

    def constructSPARQL(self, instances, preds=[]):
        if self.repository == 'pmr':
            return self.__constructSPARQLPMR(instances, preds)
        elif self.repository in ['bm','bm-omex']:
            return self.__constructSPARQL_BM_BMOmex(instances, preds)
        
    def __constructSPARQLPMR(self, instances, preds):
        objs = instances[0]
        list_sbj = set()
        list_obj = []

        # get possible subjects
        for i in range(len(objs)):
            if objs[i] in self.idxs['object_id']:
                obj_id = self.idxs['object_id'][objs[i]]
                list_obj += [obj_id]
                nextList = set(self.idxs['obj_sbj'][str(obj_id)])
                if i == 0:
                    list_sbj = nextList
                else:
                    list_sbj = list_sbj.intersection(nextList)
            else:
                print('\t%s is not in cellml, it is ignored' % objs[i])

        if len(list_sbj) == 0:
            return []

        # get all possible track_id combination
        query_seq_track_ids = []
        for sbj in list_sbj:
            query_track_ids = []
            for obj in list_obj:
                query_track_ids += [copy.deepcopy(self.idxs['sbjobj_tracks'][(sbj, obj)])]
            query_track_ids = list(itertools.product(*query_track_ids))
            query_seq_track_ids += query_track_ids
        # remove duplicate, there is possibility more than 1 query
        query_seq_track_ids = set(query_seq_track_ids)
        # construct query for each possible query
        possibleSparql = set()
        for seq_track_ids in query_seq_track_ids:
            longestTrack = 0
            objsVal = instances[1] # initiate weight for this SPARQL candidate
            seq_pred_ids = []  # one sequence of query
            seq_obj_ids = []  # to store object connector
            # access each track in a possible query
            for i in range(len(seq_track_ids)):
                track_id = seq_track_ids[i]
                longestTrack = len(self.idxs['id_track'][track_id]) if len(self.idxs['id_track'][track_id]) > longestTrack else longestTrack
                seq_pred_id = copy.deepcopy(self.idxs['id_track'][track_id])
                seq_pred_ids += [seq_pred_id]
                seq_obj_ids += [['' for x in range(len(self.idxs['id_track'][track_id]))]]
                # checking the available predicate for additional weighting
                if len(preds) > 0:
                    if len(preds[i]) > 0:
                        for pred in preds[i]:
                            if pred[0] in seq_pred_id:
                                objsVal += pred[1] # adding appeared predicate (can be modified)
            # identified conjunction object to create path between subject and object
            init_seq = 'a'
            conj_obj = 'a'
            for col in range(longestTrack):
                tmpPredIds = {}
                for row in range(len(seq_pred_ids)):
                    if col < len(seq_pred_ids[row]):
                        currSeq = tuple(seq_pred_ids[row][0:col + 1])
                        if currSeq not in tmpPredIds:
                            tmpPredIds[currSeq] = conj_obj
                            conj_obj = chr(ord(conj_obj) + 1)
                        seq_obj_ids[row][col] = tmpPredIds[currSeq]

            # generate full query link for each object
            seq_query = set()
            for obj_pos in range(len(seq_pred_ids)):
                for col in range(len(seq_pred_ids[obj_pos])):
                    pred = copy.deepcopy(self.idxs['id_pred'][seq_pred_ids[obj_pos][col]])
                    ns = self.idxs['pref_ns'][str(pred[0])]
                    nsPred = ' <' + ns + pred[1] + '> '
                    nsPred = ' ?Model_entity ' + nsPred if col == 0 else ' ?' + \
                        seq_obj_ids[obj_pos][col - 1] + ' ' + nsPred
                    nsPred += '<' + self.idxs['id_object'][str(list_obj[obj_pos])] + '> . ' if col == len(seq_pred_ids[obj_pos]) - 1 else '?' + seq_obj_ids[obj_pos][col] + ' . '
                    seq_query.add(nsPred)
            sparql = ''
            for nsPred in seq_query:
                if nsPred.find('?Model_entity') > -1:
                    nsModelEntity = nsPred[:-3]
                    nsModelEntity = nsModelEntity[:nsModelEntity.rfind(' ')+1]+'?desc . '
                sparql += nsPred
            sparql0 = sparql + self.tail[0]
            sparql1 = sparql + nsModelEntity + self.tail[1]
            unionSparql = self.header+sparql0+self.union+sparql1+self.closer
            possibleSparql.add((unionSparql, objsVal))
        return possibleSparql

    def __constructSPARQL_BM_BMOmex(self, instances, preds):
        objs = instances[0]
        # get list subject
        list_sbj = set()
        list_obj = []
        for i in range(len(objs)):
            if objs[i] in self.idxs['object_id']:
                obj_id = self.idxs['object_id'][objs[i]]
                list_obj += [obj_id]
                nextList = set(copy.deepcopy(self.idxs['obj_sbj'][int(obj_id)]))
                if i == 0:
                    list_sbj = nextList
                else:
                    list_sbj = list_sbj.intersection(nextList)
            else:
                print('\t%s is not in %s, it is ignored' %(objs[i],self.repository))

        if len(list_sbj) == 0:
            return []

        # get all possible track_id combination
        query_seq_track_ids = []
        hasDescription = {}
        for sbj in list_sbj:
            query_track_ids = [copy.deepcopy(self.idxs['sbjobj_track'][(sbj, int(obj))]) for obj in list_obj]
            query_track_ids = list(itertools.product(*query_track_ids))
            query_seq_track_ids += query_track_ids

        # construct query for each possible query
        possibleSparql = set()
        for seq_track_ids in query_seq_track_ids:
            longestTrack = 0
            objsVal = instances[1] # initiate weight for this SPARQL candidate
            seq_pred_ids = []  # one sequence of query
            seq_obj_ids = []  # to store object connector
            for i in range(len(seq_track_ids)):
                track_id = seq_track_ids[i]
                longestTrack = len(self.idxs['id_track'][str(track_id)]) if len(self.idxs['id_track'][str(track_id)]) > longestTrack else longestTrack
                seq_pred_id = copy.deepcopy(self.idxs['id_track'][str(track_id)])
                seq_pred_ids += [seq_pred_id]
                seq_obj_ids += [['' for x in range(len(self.idxs['id_track'][str(track_id)]))]]

                # checking the available predicate for additional weighting
                if len(preds) > 0:
                    if len(preds[i]) > 0:
                        for pred in preds[i]:
                            if self.idxs['id_pred'][pred[0]] in seq_pred_id:
                                objsVal += pred[1] # adding appeared predicate (can be modified)

            # identified conjunction object to create path between subject and object
            init_seq = 'a'
            conj_obj = 'a'
            for col in range(longestTrack):
                tmpPredIds = {}
                for row in range(len(seq_pred_ids)):
                    if col < len(seq_pred_ids[row]):
                        currSeq = tuple(seq_pred_ids[row][0:col + 1])
                        if currSeq not in tmpPredIds:
                            tmpPredIds[currSeq] = conj_obj
                            conj_obj = chr(ord(conj_obj) + 1)
                        seq_obj_ids[row][col] = tmpPredIds[currSeq]

            # generate full query link for each object
            seq_query = set()
            for obj_pos in range(len(seq_pred_ids)):
                for col in range(len(seq_pred_ids[obj_pos])):
                    pred = ' <' + seq_pred_ids[obj_pos][col] + '> '
                    nsPred = ' ?element ' + pred if col == 0 else ' ?' + \
                        seq_obj_ids[obj_pos][col - 1] + ' ' + pred
                    nsPred += '<' + self.idxs['id_object'][list_obj[obj_pos]] + '> . ' if col == len(seq_pred_ids[obj_pos]) - 1 else '?' + seq_obj_ids[obj_pos][col] + ' . '
                    seq_query.add(nsPred)

            if self.repository == 'bm':
                select = self.select
                where = self.where
                for nspred in seq_query:
                    where += nspred
                for optional in self.whereOptional:
                    where += optional
                sparql = select + where + ' }'
                possibleSparql.add(sparql)
            elif self.repository == 'bm-omex':
                select = self.select
                where = ''
                for nspred in seq_query:
                    where += '\n' + nspred
                sparql = select + where + self.closer
                possibleSparql.add((sparql, objsVal))
        return possibleSparql

    def runSparQL(self, query):
        self.sparqlEP.setQuery(query)
        self.sparqlEP.setReturnFormat(JSON)
        return self.sparqlEP.query().convert()

    # printType: 'verbose', 'summary', 'flat'
    def print_results(self, results, printType):
        for key, items in results['results'].items():
            if not isinstance(items, (bool)):
                print(indent(pformat("# of tuples is " + str(len(items))), '         '))
                if printType == 'verbose':
                    print(
                        indent(pformat(results['head']['vars']), '         '))
                    for item in items:
                        for key2, item2 in item.items():
                            print(indent(pformat(item2['value']), '         '))
