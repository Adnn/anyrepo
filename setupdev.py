#!/usr/bin/env python

from itertools import chain
from subprocess import check_output, run
from urllib.parse import urlparse

import argparse, json, os, shutil, tempfile

class ChDir(object):
    """
    Scoped change directory
    """
    def __init__(self, path):
        self.old_dir = os.getcwd()
        self.new_dir = path

    def __enter__(self):
        os.chdir(self.new_dir)

    def __exit__(self, *args):
        os.chdir(self.old_dir)

class Repository(object):
    def __init__(self, url, branch="develop", buildfolder="build", conanfolder="conan"):
        self.url = url
        self.branch = branch
        self.name = urlparse(url, scheme="ssh").path.split("/")[-1].replace(".git", "")
        # TODO should be made more resilient
        self.folder = os.path.join(os.getcwd(), self.name)
        self.buildpath = os.path.join(self.folder, buildfolder)
        self.conanpath = os.path.join(self.folder, conanfolder)

    def __str__(self):
        return self.name


def make_repo(upstream):
    if isinstance(upstream, list):
        return Repository(upstream[0], upstream[1])
    else:
        return Repository(upstream)


def cmd(*args):
    run(*args, check=True)


def print_section(section):
    print("\n###\n### {}\n###".format(section))


def clone(repo):
    print_section("Clone {}".format(repo))
    cmd(["git", "clone", "--recurse-submodules", "-b", repo.branch, repo.url])
    return repo


def export(repo, reference="local@"):
    print_section("Export {}".format(repo))
    cmd(["conan", "export", repo.conanpath, reference])
    # TODO make more robust when export has a json output
    # see: https://github.com/conan-io/conan/issues/6554#issuecomment-587950528
    return repo.name + "/" + reference


def remove_export(recipe_reference):
    cmd(["conan", "remove", "-f", recipe_reference])


def lock(repo, profile):
    print_section("Graph-lock for {}".format(repo.name))
    cmd(["conan", "graph", "lock", "-pr", profile, repo.conanpath])


def generate(repo, lockfile, packagepath):
    print_section("Generate {}".format(repo.name))
    cmd(["conan", "install",
          "--install-folder={}".format(repo.buildpath),
          "--lockfile={}".format(lockfile),
          repo.conanpath])
    cmd(["conan", "build",
         "--source-folder={}".format(repo.folder),
         "--build-folder={}".format(repo.buildpath),
         "--package-folder={}".format(os.path.join(packagepath, repo.name)),
         repo.conanpath])

def reconfigure(repo, upstreams):
    print_section("Reconfigure {}".format(repo.name))
    defines = ["-D{}_DIR={}".format(up.name, up.buildpath) for up in upstreams if up.name != repo.name]
    cmd(["cmake", "-S", repo.folder, "-B", repo.buildpath, *defines])


def check_system():
    """ Ensures the sytem is in the expected state """
    """ Terminates with an appropriates diagnostic if it is not """
    packages = check_output(["conan", "search", "--raw", "*/local"])
    if packages:
        print ("Aborting: local packages already present in global conan cache:\n{}".format(packages.decode("utf-8")))
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup a development folder with several related repositories")
    parser.add_argument("repositories",
                    help="Json file containing the repositories setups")
    parser.add_argument("profile",
                    help="Conan profile to build against")
    parser.add_argument("--package-path", default="SDK/")
    args = parser.parse_args()

    check_system()

    with open(args.repositories) as openfile:
        config = json.load(openfile)
        upstreams = [clone(make_repo(upstream)) for upstream in config["dependencies"]]
        upstream_references = [export(up) for up in upstreams]

        downstream = clone(make_repo(config["downstream"]))
        lock(downstream, args.profile)

        for repo in chain(upstreams, [downstream]):
            generate(repo, "conan.lock", args.package_path)
            reconfigure(repo, upstreams)

        for ref in upstream_references:
            remove_export(ref)
