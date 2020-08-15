#!/usr/bin/python3
# -*- coding=utf-8 -*-

import requests
import sys
import os
import urllib3
import gzip
import shutil
import json
import tarfile

urllib3.disable_warnings()


default_repository = "registry-1.docker.io"
default_auth_url = "https://auth.docker.io/token"
default_reg_service = "registry.docker.io"

# ref: https://docs.docker.com/registry/spec/manifest-v2-2/
# specifies the mediaType for the current version.
media_type_manifest = "application/vnd.docker.distribution.manifest.v2+json"
media_type_manifest_list = "application/vnd.docker.distribution.manifest.list.v2+json"


class Client(object):
    def __init__(self):
        self.reg_service = default_reg_service
        self.registry = default_repository
        self.auth_url = default_auth_url

    def remove(self, image):
        os.remove(image.root_path())

    def tar(self, image):
        img_dir = image.root_path()
        tar_file = img_dir + ".tar"
        tar = tarfile.open(tar_file, "w")
        tar.add(img_dir, arcname=os.path.sep)
        tar.close()

    # return manifest url
    def get_manifest_url(self, image):
        return "https://{}/v2/{}/manifests/{}".format(
            self.registry, image.repo, image.tag
        )

    # return auth url
    def get_auth_url(self, image):
        return "{}?service={}&scope=repository:{}:pull".format(
            self.auth_url, self.reg_service, image.repo
        )

    # return bolb url
    def get_bolb_url(self, image, digest=""):
        if not digest:
            digest = image.get_config_digest()
        return "https://{}/v2/{}/blobs/{}".format(self.registry, image.repo, digest)

    # pull image from image registry
    def pull(self, image):
        # fetch manifest info
        self.fetch_manifest_v2(image)

        # create dir to store the image
        imgdir = image.root_path()
        try:
            os.mkdir(imgdir)
        except OSError as error:
            print("mkdir {} faied:{}".format(imgdir, error))
            return

        # download config blob
        self.download_config_blob(image)
        file = open(image.config_path(), "wb")
        file.write(image.remote_config_blob)
        file.close()

        # init local manifest to store the remote manifest
        image.init_local_manifest()
        print("ds {}".format(image.layers))
        parentid = ""
        index = 0
        for layer in image.layers:
            digest = layer["digest"]
            layerdir = imgdir + "/" + digest[7:]
            os.mkdir(layerdir)

            # Creating VERSION file
            file = open(layerdir + "/VERSION", "w")
            file.write("1.0")
            file.close()

            # Creating layer.tar file
            sys.stdout.write(digest[7:19] + ": Downloading...")
            sys.stdout.flush()

            stream = requests.get(
                self.get_bolb_url(image, digest),
                headers=self.auth_head,
                stream=True,
                verify=False,
            )
            if stream.status_code != 200:  # When the layer is located at a custom URL
                stream = requests.get(
                    layer["urls"][0], headers=self.auth_head, stream=True, verify=False
                )
                if stream.status_code != 200:
                    print(
                        "\rERROR: Cannot download layer {} [HTTP {}] length {}".format(
                            digest[7:19],
                            stream.status_code,
                            stream.headers["Content-Length"],
                        )
                    )
                    print(stream.content)
                    exit(1)
            stream.raise_for_status()
            with open(layerdir + "/layer.gzip", "wb") as file:
                for chunk in stream.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            with open(
                layerdir + "/layer.tar", "wb"
            ) as file:  # Decompress gzip response
                unzLayer = gzip.open(layerdir + "/layer.gzip", "rb")
                shutil.copyfileobj(unzLayer, file)
                unzLayer.close()
            os.remove(layerdir + "/layer.gzip")
            image.append_local_layers(digest)

            file = open(layerdir + "/json", "w")
            json_obj = image.get_layer_json_by_index(index)
            json_obj["id"] = digest
            if parentid:
                json_obj["parent"] = parentid
            parentid = digest
            file.write(json.dumps(json_obj))
            file.close()
            index += 1

        file = open(image.manifest_path(), "w")
        file.write(json.dumps(image.local_manifest))
        file.close()

    def auth(self, image):
        self.get_reg_service()
        print("get reg service: {}".format(self.reg_service))

    def get_reg_service(self):
        resp = requests.get("https://{}/v2/".format(self.registry), verify=False)
        print("get reg code {}".format(resp.status_code))
        if resp.status_code == 401:
            self.auth_url = resp.headers["WWW-Authenticate"].split('"')[1]
            try:
                self.reg_service = resp.headers["WWW-Authenticate"].split('"')[3]
            except IndexError:
                self.reg_service = ""

    def fresh_auth_head(self, type, image):
        url = "{}?service={}&scope=repository:{}:pull".format(
            self.auth_url, self.reg_service, image.repo
        )
        resp = requests.get(url, verify=False)
        access_token = resp.json()["token"]
        self.auth_head = {"Authorization": "Bearer " + access_token, "Accept": type}
        return self.auth_head

    def fetch_manifest_v2(self, image):
        # Fetch manifest v2 and get image layer digests
        self.fresh_auth_head(media_type_manifest, image)
        resp = requests.get(
            self.get_manifest_url(image), headers=self.auth_head, verify=False
        )
        if resp.status_code != 200:
            print(
                "[-] Cannot fetch manifest for {} [HTTP {}]".format(
                    self.registry, resp.status_code
                )
            )
            print(resp.content)
            auth_head = self.fresh_auth_head(media_type_manifest_list, image)
            resp = requests.get(
                self.get_manifest_url(image), headers=auth_head, verify=False,
            )
            if resp.status_code == 200:
                print(
                    "[+] Manifests found for this tag (use the @digest format to pull the corresponding image):"
                )
                manifests = resp.json()["manifests"]
                for manifest in manifests:
                    for key, value in manifest["platform"].items():
                        sys.stdout.write("{}: {}, ".format(key, value))
                    print("digest: {}".format(manifest["digest"]))
            exit(1)
        image.set_remote_manifest(resp.json())

    # downloads config blog by the diest of image
    def download_config_blob(self, image):
        confresp = requests.get(
            self.get_bolb_url(image), headers=self.auth_head, verify=False,
        )
        image.set_remote_config(confresp.content)
