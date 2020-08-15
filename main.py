#!/usr/bin/python3
# -*- coding=utf-8 -*-
import sys, getopt
from absl import app
from absl import flags

sys.path.append("lib")
from lib import image
from lib import utils
from lib import client

FLAGS = flags.FLAGS
flags.DEFINE_string("host", None, "cluster host. example: 127.0.0.1:6060")
flags.DEFINE_string("image", None, "image name")
flags.DEFINE_string("user", None, "user name")
flags.DEFINE_bool("server", False, "run a server")
flags.DEFINE_bool("pull", False, "welcome to cli")
flags.DEFINE_bool("tag", False, "welcome to cli")


def main(argv):
    del argv
    repo, tag = "", ""
    if FLAGS.image:
        repo, tag = utils.parse(FLAGS.image)
    i = image.Image(repo, tag)
    c = client.Client()
    # c.tar(i)
    c.auth(i)
    c.pull(i)

    print("image name [{}]".format(i.string()))

    if FLAGS.pull:
        exit()
    if FLAGS.tag:
        c.tar(i)
        exit()
    # if FLAGS.cli:
    #     exit()

    print("update successfully")


if __name__ == "__main__":
    app.run(main)
