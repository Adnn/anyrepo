#!/usr/bin/env python3

from subprocess import run
import argparse, json, os, shutil, tempfile


class ChDir(object):
    """
    Step into a directory temporarily.
    """
    def __init__(self, path):
        self.old_dir = os.getcwd()
        self.new_dir = path

    def __enter__(self):
        os.chdir(self.new_dir)

    def __exit__(self, *args):
        os.chdir(self.old_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup a development folder with several related repositories")
    parser.add_argument("upstreams", metavar='U', nargs='+',
                    help="Upstream repositories already cloned")
    args = parser.parse_args()

    references = {}

    tempdir = tempfile.mkdtemp()
    with ChDir(tempdir):
        for folder in args.upstreams:
            lockfile = "{}.lock".format(folder)
            run(["conan", "graph", "lock", "-l", lockfile, "{}/conan".format(folder)], check=True)
            jsonfile = "{}.json".format(folder)
            run(["conan", "graph", "build-order", "-b", "--json", jsonfile, lockfile], check=True)

            with open(jsonfile) as openfile:
                graph = json.load(openfile)
                for group in graph:
                    for dependency in group:
                        references[dependency[1].split("/")[0]] = dependency[1].split("#")[0]

    shutil.rmtree(tempdir)

    for k, v in references.items():
        print("{} {}".format(k,v))
