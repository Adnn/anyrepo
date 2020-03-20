conan remove -f pkga
conan remove -f pkgb
conan remove -f app
rm -rf tmpbuild

mkdir tmpbuild
pushd tmpbuild

# recursive clone and export of all upstreams in an external list
#git clone --recursive ../pkga
cp -R ../pkga .
conan export pkga/conan local@

cp -R ../pkgb .
conan export pkgb/conan local@

# recursive clone of the downstream
#git clone --recursive ../pkgb
cp -R ../app .

conan graph lock -pr am-macos app/conan/

## for each node: install & build
## providing overrides for local projects
pushd pkga
rm -rf build/ #in case it existed
conan install --install-folder=build --lockfile=../conan.lock conan/
conan build --source-folder=./ --build-folder=build --package-folder=../SDK/pkga conan/
popd

pushd pkgb
rm -rf build/ #in case it existed
conan install --install-folder=build --lockfile=../conan.lock conan/
conan build --source-folder=./ --build-folder=build --package-folder=../sdk/pkgb conan/
pushd build
cmake -dpkga_dir=$(pwd)/../../pkga/build/ ..
popd
popd

pushd app
rm -rf build/ #in case it existed
conan install --install-folder=build --lockfile=../conan.lock conan/
conan build --source-folder=./ --build-folder=build --package-folder=../sdk/app conan/
pushd build
cmake -dpkgb_dir=$(pwd)/../../pkgb/build/ ..
popd
popd

popd #tmpbuild
