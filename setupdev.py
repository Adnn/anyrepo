#!/usr/bin/env python3

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
        self.conanfilepath = os.path.join(self.conanpath, "conanfile.py")

    def __str__(self):
        return self.name

    def folder_present(self):
        return os.path.exists(self.folder)

    def ensure_cloned(self):
        if (not self.folder_present()):
            clone(self)
        else:
            print_section("Repo {} already present: skip cloning".format(self))
        return self


def make_repo(upstream, buildfolder):
    if isinstance(upstream, list):
        return Repository(upstream[0], upstream[1], buildfolder=buildfolder)
    else:
        return Repository(upstream, buildfolder=buildfolder)


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
    print_section("Create lock file for {}".format(repo.name))
    cmd(["conan", "lock", "create", "--build=missing", "-pr", profile, repo.conanfilepath])


def generate(repo, lockfile, references_map, packagepath, cleanbuild=False):
    print_section("Generate {}".format(repo.name))
    if cleanbuild and os.path.exists(repo.buildpath):
        print("Remove build folder '{}'".format(repo.buildpath))
        shutil.rmtree(repo.buildpath)
    cmd(["conan", "install",
          "--build=missing",
          "--install-folder={}".format(repo.buildpath),
          "--lockfile={}".format(lockfile),
          repo.conanpath,
          references_map[repo.name]])
    cmd(["conan", "build",
         "--source-folder={}".format(repo.folder),
         "--build-folder={}".format(repo.buildpath),
         "--package-folder={}".format(os.path.join(packagepath, repo.name)),
         repo.conanpath])

def reconfigure(repo, upstreams):
    print_section("Reconfigure {}".format(repo.name))
    defines = ["-D{}_DIR={}".format(up.name.capitalize(), up.buildpath) for up in upstreams if up.name != repo.name]
    cmd(["cmake", "-S", repo.folder, "-B", repo.buildpath, *defines])


def check_system():
    """ Ensures the sytem is in the expected state """
    """ Terminates with an appropriates diagnostic if it is not """
    packages = check_output(["conan", "search", "--raw", "*/local"])
    if packages:
        print ("Aborting: local packages already present in global conan cache:\n{}".format(packages.decode("utf-8")))
        exit(1)


def map_requirements(repo):
    """ Return a map whose key are 'project names' (the name in the recipe) """
    """ and associated values are the correponding recipe reference """
    """ (optionally appending a '@' if the reference does not contain one already) """
    requirement = run(["conan", "info", "-n", "None", repo.conanpath],
                      capture_output=True, text=True)
    result = {};
    for line in requirement.stdout.splitlines():
        # The line for downstream will be "conanfile.py (downstream/xxx)".
        line = line.removeprefix("conanfile.py (").removesuffix(")")
        # There are "messages" in addition to the list of requirements, they tend to have spaces.
        if not ' ' in line:
            # Append a '@' after the reference if it does not contain one.
            result[line.split("/", 1)[0]] = line if "@" in line else (line + "@")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup a development folder with several related repositories")
    parser.add_argument("repositories",
                        help="Path to a Json file containing the repositories setups")
    parser.add_argument("--profile", default="default",
                        help="Conan profile to build against")
    parser.add_argument("--package-prefix", default="SDK/",
                        help="The installation prefix for package() command")
    parser.add_argument("--build-folder", default="build",
                        help="The subpath in each repository where build takes place")
    parser.add_argument("--clean-build", action="store_true",
                        help="The build folder of each repository will be removed before build")
    args = parser.parse_args()

    check_system()

    with open(args.repositories) as openfile:
        config = json.load(openfile)
        upstreams = [make_repo(upstream, args.build_folder).ensure_cloned() for upstream in config["dependencies"]]
        upstream_references = [export(up) for up in upstreams]

        downstream = make_repo(config["downstream"], args.build_folder).ensure_cloned()
        lock(downstream, args.profile)
        references_map = map_requirements(downstream)

        for repo in chain(upstreams, [downstream]):
            generate(repo, "conan.lock", references_map, args.package_prefix, args.clean_build)

        # Generate all before reconfiguring all:
        # Otherwise first repos would be reconfigured with non-gerated dependencies
        for repo in chain(upstreams, [downstream]):
            reconfigure(repo, upstreams)

        for ref in upstream_references:
            remove_export(ref)
