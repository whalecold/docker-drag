#!/usr/bin/python3
# -*- coding=utf-8 -*-


class Layer(object):
    def __init__(self, digest, id):
        self.__digest = digest
        self.__digest = id

    def version_path(self):
        return self.__digest + "VERSION"

    def layer_tar_path(self):
        return self.__digest + "layer.tar"

    def json_path(self):
        return self.__digest + "json"
