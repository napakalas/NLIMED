"""MODUL: SPARQL"""
from SPARQLWrapper import SPARQLWrapper, JSON
import itertools
import copy
import json
from pprint import pformat
from textwrap import indent
class SPARQLGenerator:
    def __init__(self):
        self.idxs = {}
        self.idxs['idx_object_id'] = self.__loadJson('idx_object_id')
        self.idxs['idx_subject_id'] = self.__loadJson('idx_subject_id')
        self.idxs['idx_obj_sbj'] = self.__loadJson('idx_obj_sbj')
        self.idxs['idx_sbjobj_tracks'] = self.__loadJson('idx_sbjobj_tracks')
        self.idxs['idx_id_track'] = self.__loadJson('idx_id_track')
        self.idxs['idx_id_pred'] = self.__loadJson('idx_id_pred')
        self.idxs['idx_pref_ns'] = self.__loadJson('idx_pref_ns')
        self.idxs['idx_id_object'] = self.__loadJson('idx_id_object')
        self.idxs['idx_id_subject'] = self.__loadJson('idx_id_subject')
        #initialized based query for each subject
        self.header_1 = 'SELECT ?graph ?Model_entity ?desc WHERE { GRAPH ?graph { '
        self.header_2 = 'SELECT ?graph ?Model_entity WHERE { GRAPH ?graph { '
        self.tail_1 = ' ?Model_entity <http://purl.org/dc/terms/description> ?desc . }}'
        self.tail_2 = ' }}'
        #get id predicate description
        for predId, value in self.idxs['idx_id_pred'].items():
            if value[1] == 'description':
                nsId = value[0]
                if self.idxs['idx_pref_ns'][str(nsId)]=='http://purl.org/dc/terms/':
                    for trackId, track in self.idxs['idx_id_track'].items():
                        if predId in track:
                            self.trackDesc = trackId
                            break
                    break

    def constructSPARQL(self, *objs):
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
            index_sbj_track[tmp_index_sbjobj_track[0][0]] = val if tmp_index_sbjobj_track[0][0] not in index_sbj_track else index_sbj_track[tmp_index_sbjobj_track[0][0]] + val
        index_track = copy.deepcopy(self.idxs['idx_id_track'])
        index_predicate = copy.deepcopy(self.idxs['idx_id_pred'])
        index_prefix = copy.deepcopy(self.idxs['idx_pref_ns'])
        index_id_obj = copy.deepcopy(self.idxs['idx_id_object'])
        index_id_sbj = copy.deepcopy(self.idxs['idx_id_subject'])
        #get list subject
        list_sbj = set()
        list_obj = []
        for i in range(len(objs)):
            if objs[i] in index_obj:
                obj_id = index_obj[objs[i]]
                list_obj += [obj_id]
                nextList = set(index_obj_sbj[str(obj_id)])
                if i==0:
                    list_sbj = nextList
                else:
                    list_sbj = list_sbj.intersection(nextList)
            else:
                print('\t%s is not in cellml, it is ignored'%objs[i])

        if len(list_sbj) is 0:
            return []
        else:
            #get all possible track_id combination
            query_seq_track_ids=[]
            hasDescription = {}
            for sbj in list_sbj:
                query_track_ids = []
                for obj in list_obj:
                    query_track_ids += [index_sbjobj_tracks[(sbj,obj)]]
                query_track_ids = list(itertools.product(*query_track_ids))
                query_seq_track_ids += query_track_ids
                for query_track_id in query_track_ids:
                    hasDescription[query_track_id] = True if self.trackDesc in index_sbj_track[sbj] else False
            #remove duplicate, there is possibility more than 1 query
            query_seq_track_ids = set(query_seq_track_ids)
            #construct query for each possible query
            possibleSparql = set()
            for seq_track_ids in query_seq_track_ids:
                longestTrack =0
                seq_pred_ids = [] # one sequence of query
                seq_obj_ids = [] # to store object connector
                for track_id in seq_track_ids:
                    longestTrack = len(index_track[track_id]) if len(index_track[track_id])>longestTrack else longestTrack
                    seq_pred_ids += [copy.deepcopy(index_track[track_id])]
                    seq_obj_ids += [['' for x in range(len(index_track[track_id]))]]
                # identified conjunction object to create path between subject and object
                init_seq = 'a'
                conj_obj = 'a'
                for col in range(longestTrack):
                    tmpPredIds = {}
                    for row in range(len(seq_pred_ids)):
                        if col < len(seq_pred_ids[row]):
                            currSeq = tuple(seq_pred_ids[row][0:col+1])
                            if currSeq not in tmpPredIds:
                                tmpPredIds[currSeq] =  conj_obj
                                conj_obj = chr(ord(conj_obj)+1)
                            seq_obj_ids[row][col] = tmpPredIds[currSeq]
#                 generate full query link for each object
                seq_query = set()
                for obj_pos in range(len(seq_pred_ids)):
                    for col in range(len(seq_pred_ids[obj_pos])):
                        pred = index_predicate[seq_pred_ids[obj_pos][col]]
                        ns = index_prefix[str(pred[0])]
                        nsPred = ' <'+ns+pred[1]+'> '
                        nsPred = ' ?Model_entity ' + nsPred if col==0 else ' ?'+seq_obj_ids[obj_pos][col-1]+' '+nsPred
                        nsPred += '<'+ index_id_obj[str(list_obj[obj_pos])] +'> . ' if col == len(seq_pred_ids[obj_pos])-1 else '?'+seq_obj_ids[obj_pos][col]+' . '
                        seq_query.add(nsPred)
                sparQl = self.header_1 if hasDescription[seq_track_ids] else self.header_2
                for nsPred in seq_query:
                    sparQl+=nsPred
                sparQl +=  self.tail_1 if hasDescription[seq_track_ids] else self.tail_2
                possibleSparql.add(sparQl)
            return possibleSparql

    def runSparQL(self, query):
        sparqlendpoint = 'https://models.physiomeproject.org/pmr2_virtuoso_search'
        sparql = SPARQLWrapper(sparqlendpoint)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        return sparql.query().convert()

    def print_results(self, results, printType): #printType: 'verbose', 'summary', 'flat'
        for key, items in results['results'].items():
            if not isinstance(items,(bool)):
                print(indent(pformat("# of tuples is " + str(len(items))),'         '))
                if printType == 'verbose':
                    print(indent(pformat(results['head']['vars']),'         '))
                    for item in items:
                        for key2, item2 in item.items():
                            print(indent(pformat(item2['value']),'         '))
                elif printType == 'flat':
                    print(results['head']['vars'])
                    for item in items:
                        for key2, item2 in item.items():
                            print(item2)
                        print('\n')

    def __loadJson(self, fileName):
        with open(fileName, 'r') as fp:
            data = json.load(fp)
        return data
