#!/usr/bin/python3
# -*- coding=utf-8 -*-

import json

empty_json = '{"created":"1970-01-01T00:00:00Z","container_config":{"Hostname":"","Domainname":"","User":"","AttachStdin":false, \
	"AttachStdout":false,"AttachStderr":false,"Tty":false,"OpenStdin":false, "StdinOnce":false,"Env":null,"Cmd":null,"Image":"", \
	"Volumes":null,"WorkingDir":"","Entrypoint":null,"OnBuild":null,"Labels":null}}'

default_root_path = ""


class Image(object):
    def __init__(self, repo, tag):
        self.repo = repo
        self.tag = tag

    # print image full name
    def string(self):
        return "{}:{}".format(self.repo, self.tag)

    def root_path(self):
        return (
            "{}/{}".format(default_root_path, self.string())
            .replace(":", "@")
            .replace("/", "_")
        )

    def manifest_path(self):
        return "{}/manifest.json".format(self.root_path())

    def config_path(self):
        return "{}/{}.json".format(self.root_path(), self.get_config_digest()[7:])

    def set_remote_manifest(self, manifest):
        self.remote_manifest = manifest
        self.layers = manifest["layers"]
        self.config = manifest["config"]

    def get_config_digest(self):
        return self.config["digest"]

    def init_local_manifest(self):
        self.local_manifest = [
            {
                "Config": self.get_config_digest()[7:] + ".json",
                "RepoTags": [self.string()],
                "Layers": [],
            }
        ]

    def append_local_layers(self, layer):
        self.local_manifest[0]["Layers"].append(layer[7:] + "/layer.tar")

    def set_remote_config(self, content):
        self.remote_config_blob = content

    def get_layer_json_by_index(self, index):
        if index == len(self.layers) - 1:
            # FIXME: json.loads() automatically converts to unicode, thus decoding values whereas Docker doesn't
            json_obj = json.loads(self.remote_config_blob)
            del json_obj["history"]
            try:
                del json_obj["rootfs"]
            except:  # Because Microsoft loves case insensitiveness
                del json_obj["rootfS"]
        else:
            json_obj = json.loads(empty_json)
        return json_obj

