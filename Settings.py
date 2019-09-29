"""GENERAL CLASS: performing method used by all classes"""

from abc import ABCMeta, abstractmethod, ABC
import json
import os.path
import requests
from nltk.corpus import stopwords
from nltk.tree import ParentedTree
from SPARQLWrapper import SPARQLWrapper, JSON
import copy
import rdflib


class GeneralNLIMED(ABC):
    def __init__(self):
        self.oboAPIKey = 'fc5d5241-1e8e-4b44-b401-310ca39573f6'
        self.oboUrl = "http://data.bioontology.org/ontologies/"

    def _loadJson(self, fileName):
        isExist = os.path.exists(fileName)
        if isExist:
            with open(fileName, 'r') as fp:
                data = json.load(fp)
            return data
        else:
            return {}

    def _dumpJson(self, data, fileName):
        with open(fileName, 'w') as fp:
            json.dump(data, fp)

    def _saveToFlatFile(self, data, fileName):
        f = open(fileName, 'w+')
        for datum in data:
            f.write(str(datum).replace('\n', ' ').replace('\r', ' ') + '\n')
        f.close()

    def _loadFromFlatFile(self, fileName):
        try:
            f = open(fileName, 'r')
            lines = f.readlines()
            f.close()
            return lines
        except:
            return []

    def _saveBinaryInteger(self, data, filename):
        import struct
        with open(filename, "wb") as f:
            for x in data:
                f.write(struct.pack('i', x))  # 4bytes

    def _loadBinaryInteger(self, filename):
        import struct
        with open(filename, 'rb') as f:
            bdata = []
            while True:
                bytes = f.read(4)
                if bytes == b'':
                    break
                else:
                    bdata.append(struct.unpack('i', bytes)[0])  # 4bytes
        return bdata
