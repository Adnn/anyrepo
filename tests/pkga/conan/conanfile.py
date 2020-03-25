from conans import ConanFile, CMake


class PkgAConan(ConanFile):
    name = "pkga"
    settings = (
        "os",
        "compiler",
        "build_type",
        "arch")
    options = {
        "shared": [True, False],
        "build_tests": [True, False],
    }
    default_options = {
        "shared": False,
        "build_tests": False,
    }

    requires = ("boost/1.71.0@conan/stable",)

    build_requires = ("cmake_installer/[>=3.16]@conan/stable",)

    build_policy = "missing"
    generators = "cmake"

    scm = {
        "type": "git",
        "url": "auto",
        "revision": "auto",
        "submodule": "recursive",
    }


    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["BUILD_tests"] = self.options.build_tests
        cmake.configure()
        return cmake


    def build(self):
        cmake = self._configure_cmake()
        cmake.build()


    def package(self):
        cmake = self._configure_cmake()
        cmake.install()
