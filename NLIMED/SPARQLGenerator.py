"""MODUL: SPARQL GENERATOR"""
import itertools
from pprint import pformat
from textwrap import indent
from NLIMED.Settings import *


class SPARQLGenerator(GeneralNLIMED):
    def __init__(self, repository):
        super(SPARQLGenerator, self).__init__()
        self.repository = repository
        if repository == 'pmr':
            self.__initPMR()
        elif repository == 'bm':
            self.__initBM()

    def __initPMR(self):  # initialisation of PMR
        self.idxs = {}
        self.idxs['idx_object_id'] = self._loadJson('indexes/idx_object_id')
        self.idxs['idx_subject_id'] = self._loadJson('indexes/idx_subject_id')
        self.idxs['idx_obj_sbj'] = self._loadJson('indexes/idx_obj_sbj')
        self.idxs['idx_sbjobj_tracks'] = self._loadJson('indexes/idx_sbjobj_tracks')
        self.idxs['idx_id_track'] = self._loadJson('indexes/idx_id_track')
        self.idxs['idx_id_pred'] = self._loadJson('indexes/idx_id_pred')
        self.idxs['idx_pref_ns'] = self._loadJson('indexes/idx_pref_ns')
        self.idxs['idx_id_object'] = self._loadJson('indexes/idx_id_object')
        self.idxs['idx_id_subject'] = self._loadJson('indexes/idx_id_subject')
        # initialized based query for each subject
        self.header = 'SELECT ?graph ?Model_entity ?desc WHERE { GRAPH ?graph { '
        self.tail = ' OPTIONAL{?Model_entity <http://purl.org/dc/terms/description> ?desc .} }}'

    def __initBM(self):  # initialisation of BioModels
        self.idxs = {}
        self.idxs['id_object'] = self._loadJson('indexes/BM_selected_object.json')
        self.idxs['obj_sbj'] = {}
        self.idxs['sbjobj_track'] = {}
        self.idxs['id_track'] = self._loadJson('indexes/BM_track.json')
        rdfPath = self._loadBinaryInteger("indexes/BM_selected_rdfPaths")
        for i in range(0, len(rdfPath), 3):
            sbj, track, obj = rdfPath[i], rdfPath[i + 1], rdfPath[i + 2]
            self.idxs['obj_sbj'][obj] = self.idxs['obj_sbj'][obj] if obj in self.idxs['obj_sbj'] else set()
            self.idxs['obj_sbj'][obj].add(sbj)
            self.idxs['sbjobj_track'][(sbj, obj)] = self.idxs['sbjobj_track'][(
                sbj, obj)] if (sbj, obj) in self.idxs['sbjobj_track'] else set()
            self.idxs['sbjobj_track'][(sbj, obj)].add(track)
        # initialized based query for each subject
        self.select = 'SELECT ?model ?type ?element ?notes ?name '
        self.where = """
            WHERE {
                ?model ?type ?element ."""
        # get id predicate description
        self.whereOptional = {' OPTIONAL{?element <http://identifiers.org/biomodels.vocabulary#notes> ?notes .} ',
                              ' OPTIONAL{?element <http://identifiers.org/biomodels.vocabulary#name> ?name .} '}

    def constructSPARQL(self, *objs):
        if self.repository == 'pmr':
            return self.__constructSPARQLPMR(*objs)
        elif self.repository == 'bm':
            return self.__constructSPARQLBM(*objs)

    def __constructSPARQLPMR(self, *objs):
        index_obj = copy.deepcopy(self.idxs['idx_object_id'])
        index_sbj = copy.deepcopy(self.idxs['idx_subject_id'])
        index_obj_sbj = copy.deepcopy(self.idxs['idx_obj_sbj'])
        tmp_index_sbjobj_tracks = copy.deepcopy(self.idxs['idx_sbjobj_tracks'])
        index_sbjobj_tracks = {}
        index_sbj_track = {}
        for tmp_index_sbjobj_track in tmp_index_sbjobj_tracks:
            key = tuple(tmp_index_sbjobj_track[0])
            val = tmp_index_sbjobj_track[1]
            index_sbjobj_tracks[key] = val
            index_sbj_track[tmp_index_sbjobj_track[0][0]] = val if tmp_index_sbjobj_track[0][
                0] not in index_sbj_track else index_sbj_track[tmp_index_sbjobj_track[0][0]] + val
        index_track = copy.deepcopy(self.idxs['idx_id_track'])
        index_predicate = copy.deepcopy(self.idxs['idx_id_pred'])
        index_prefix = copy.deepcopy(self.idxs['idx_pref_ns'])
        index_id_obj = copy.deepcopy(self.idxs['idx_id_object'])
        index_id_sbj = copy.deepcopy(self.idxs['idx_id_subject'])
        # get list subject
        list_sbj = set()
        list_obj = []
        for i in range(len(objs)):
            if objs[i] in index_obj:
                obj_id = index_obj[objs[i]]
                list_obj += [obj_id]
                nextList = set(index_obj_sbj[str(obj_id)])
                if i == 0:
                    list_sbj = nextList
                else:
                    list_sbj = list_sbj.intersection(nextList)
            else:
                print('\t%s is not in cellml, it is ignored' % objs[i])

        if len(list_sbj) == 0:
            return []
        else:
            # get all possible track_id combination
            query_seq_track_ids = []
            for sbj in list_sbj:
                query_track_ids = []
                for obj in list_obj:
                    query_track_ids += [index_sbjobj_tracks[(sbj, obj)]]
                query_track_ids = list(itertools.product(*query_track_ids))
                query_seq_track_ids += query_track_ids
            # remove duplicate, there is possibility more than 1 query
            query_seq_track_ids = set(query_seq_track_ids)
            # construct query for each possible query
            possibleSparql = set()
            for seq_track_ids in query_seq_track_ids:
                longestTrack = 0
                seq_pred_ids = []  # one sequence of query
                seq_obj_ids = []  # to store object connector
                for track_id in seq_track_ids:
                    longestTrack = len(index_track[track_id]) if len(
                        index_track[track_id]) > longestTrack else longestTrack
                    seq_pred_ids += [copy.deepcopy(index_track[track_id])]
                    seq_obj_ids += [
                        ['' for x in range(len(index_track[track_id]))]]
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
#                 generate full query link for each object
                seq_query = set()
                for obj_pos in range(len(seq_pred_ids)):
                    for col in range(len(seq_pred_ids[obj_pos])):
                        pred = index_predicate[seq_pred_ids[obj_pos][col]]
                        ns = index_prefix[str(pred[0])]
                        nsPred = ' <' + ns + pred[1] + '> '
                        nsPred = ' ?Model_entity ' + nsPred if col == 0 else ' ?' + \
                            seq_obj_ids[obj_pos][col - 1] + ' ' + nsPred
                        nsPred += '<' + index_id_obj[str(list_obj[obj_pos])] + '> . ' if col == len(
                            seq_pred_ids[obj_pos]) - 1 else '?' + seq_obj_ids[obj_pos][col] + ' . '
                        seq_query.add(nsPred)
                sparql = self.header
                for nsPred in seq_query:
                    sparql += nsPred
                sparql += self.tail
                possibleSparql.add(sparql)
            return possibleSparql

    def __constructSPARQLBM(self, *objs):
        index_obj = {val: key for key, val in copy.deepcopy(
            self.idxs['id_object']).items()}
        index_id_obj = copy.deepcopy(self.idxs['id_object'])
        index_obj_sbj = copy.deepcopy(self.idxs['obj_sbj'])
        index_sbjobj_tracks = copy.deepcopy(self.idxs['sbjobj_track'])
        index_track = copy.deepcopy(self.idxs['id_track'])

#         print(index_obj_sbj)
#         print(index_sbjobj_tracks)

        # get list subject
        list_sbj = set()
        list_obj = []
        for i in range(len(objs)):
            if objs[i] in index_obj:
                obj_id = index_obj[objs[i]]
                list_obj += [obj_id]
                nextList = set(index_obj_sbj[int(obj_id)])
                if i == 0:
                    list_sbj = nextList
                else:
                    list_sbj = list_sbj.intersection(nextList)
            else:
                print('\t%s is not in cellml, it is ignored' % objs[i])

        if len(list_sbj) == 0:
            return []
        else:
            # get all possible track_id combination
            query_seq_track_ids = []
            hasDescription = {}
            for sbj in list_sbj:
                query_track_ids = [index_sbjobj_tracks[(
                    sbj, int(obj))] for obj in list_obj]
                query_track_ids = list(itertools.product(*query_track_ids))
                query_seq_track_ids += query_track_ids
            # construct query for each possible query
            possibleSparql = set()
            for seq_track_ids in query_seq_track_ids:
                longestTrack = 0
                seq_pred_ids = []  # one sequence of query
                seq_obj_ids = []  # to store object connector
                for track_id in seq_track_ids:
                    longestTrack = len(index_track[str(track_id)]) if len(
                        index_track[str(track_id)]) > longestTrack else longestTrack
                    seq_pred_ids += [copy.deepcopy(index_track[str(track_id)])]
                    seq_obj_ids += [
                        ['' for x in range(len(index_track[str(track_id)]))]]
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
                        nsPred += '<' + index_id_obj[list_obj[obj_pos]] + '> . ' if col == len(
                            seq_pred_ids[obj_pos]) - 1 else '?' + seq_obj_ids[obj_pos][col] + ' . '
                        seq_query.add(nsPred)

                select = self.select
                where = self.where
                for nspred in seq_query:
                    where += nspred
                for optional in self.whereOptional:
                    where += optional
                sparql = select + where + ' }'
                possibleSparql.add(sparql)
            return possibleSparql

    def runSparQL(self, query):
        if self.repository == 'pmr':
            sparqlendpoint = 'https://models.physiomeproject.org/pmr2_virtuoso_search'
        elif self.repository == 'bm':
            sparqlendpoint = 'https://www.ebi.ac.uk/rdf/services/sparql'
        sparql = SPARQLWrapper(sparqlendpoint)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        return sparql.query().convert()

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
