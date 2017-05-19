#Python setup section

#This help message was taken from https://gist.github.com/rcmachado/af3db315e31383502660
## Show this help.
help:
	@printf "Available targets\n\n"
	@awk '/^[a-zA-Z\-\_0-9]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf "%-20s %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)

pip = -m pip install
py_deps = $(pip) cryptography --upgrade
py_test_deps = $(pip) pytest-coverage pytest-benchmark pytest-ordering
docs_deps = $(pip) sphinx sphinxcontrib-napoleon sphinx_rtd_theme

ifeq ($(shell python -c 'import sys; print(int(hasattr(sys, "real_prefix")))'), 0) # check for virtualenv
	py_deps += --user
	py_test_deps += --user
	docs_deps += --user
	user_postfix = --user
else
	user_postfix =
endif

ifeq ($(shell python -c 'import sys; print((sys.version_info[0]))'), 3)
	python2 = python2
	python3 = python
else
	python2 = python
	python3 = python3
endif

ifeq ($(shell python -c "import sys; print(hasattr(sys, 'pypy_version_info'))"), True)
	pypy = True
	ifeq ($(python2), python)
		python2 = python2
	endif
else
	pypy = False
endif

pylibdir = $(shell python -c "import sys, sysconfig; print('lib.{}-{v[0]}.{v[1]}'.format(sysconfig.get_platform(), v=sys.version_info))")
py2libdir = $(shell $(python2) -c "import sys, sysconfig; print('lib.{}-{v[0]}.{v[1]}'.format(sysconfig.get_platform(), v=sys.version_info))")
py3libdir = $(shell $(python3) -c "import sys, sysconfig; print('lib.{}-{v[0]}.{v[1]}'.format(sysconfig.get_platform(), v=sys.version_info))")
ifeq ($(python2), python)
	pyunvlibdir = $(pylibdir)
else
	pyunvlibdir = lib
endif

#End python setup section
#Begin C section

## Initialize submodules
submodules:
	@git submodule update --init --recursive

#End C section
#Begin Javascript section

jsver = $(shell node -p "require('./package.json').version")

## Install Javascript dependencies, preferring to use yarn, but using npm if it must
jsdeps: LICENSE
	@mv npm-shrinkwrap.json .npm-shrinkwrap.json; \
	yarn || npm install; \
	mv .npm-shrinkwrap.json npm-shrinkwrap.json

## Copying documentation from C-like language into the proper Restructred Text files
jsdocs:
	@echo "Copying documentation comments..."
	@node js_src/docs_test.js

## Run Javascript test code
jstest: jsdeps
	@node node_modules/istanbul/lib/cli.js cover node_modules/mocha/bin/_mocha js_src/test/*

## Run Javascript tests AND upload results to codecov (testing services only)
js_codecov: jstest
	@node node_modules/codecov/bin/codecov -f coverage/coverage.json --token=d89f9bd9-27a3-4560-8dbb-39ee3ba020a5

## Package Javascript code into browser bundles
browser: jsdeps
	@mkdir -p build/browser
	@echo "Building browser version..."
	@cd js_src;\
	node ../node_modules/browserify/bin/cmd.js -r ./base.js -o ../build/browser/js2p-browser-$(jsver)-base.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../node_modules/browserify/bin/cmd.js -x ./base.js -r ./mesh.js -o ../build/browser/js2p-browser-$(jsver)-mesh.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../node_modules/browserify/bin/cmd.js -x ./base.js -x ./mesh.js -r ./sync.js -o ../build/browser/js2p-browser-$(jsver)-sync.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../node_modules/browserify/bin/cmd.js -x ./base.js -x ./mesh.js -r ./chord.js -o ../build/browser/js2p-browser-$(jsver)-chord.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../node_modules/browserify/bin/cmd.js -x ./base.js -x ./mesh.js -x ./sync.js -x ./chord.js -e ./js2p.js -o ../build/browser/js2p-browser-$(jsver).js -s js2p

## Package Javascript code into browser bundles and minify them
browser-min: browser
	@mkdir -p build/browser-min
	@echo "Minifying..."
	@node node_modules/babel-cli/bin/babel.js ./build/browser/js2p-browser-$(jsver).js       -o ./build/browser-min/js2p-browser-$(jsver).min.js       --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser/js2p-browser-$(jsver)-base.js  -o ./build/browser-min/js2p-browser-$(jsver)-base.min.js  --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser/js2p-browser-$(jsver)-mesh.js  -o ./build/browser-min/js2p-browser-$(jsver)-mesh.min.js  --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser/js2p-browser-$(jsver)-sync.js  -o ./build/browser-min/js2p-browser-$(jsver)-sync.min.js  --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser/js2p-browser-$(jsver)-chord.js -o ./build/browser-min/js2p-browser-$(jsver)-chord.min.js --minified --no-comments --no-babelrc

## Transpile Javascript code into a non ES6 format, for older browsers or Node.js v4
js-compat: jsdeps
	@mkdir -p build/browser-compat build/babel
	@echo "Transpiling..."
	@node node_modules/babel-cli/bin/babel.js js_src -d build/babel

## Transpile Javascript code into a non ES6 format, for older browsers or Node.js v4 AND test this code
js_compat_test: js-compat
	@echo "Testing transpilation..."
	@node node_modules/istanbul/lib/cli.js cover node_modules/mocha/bin/_mocha build/babel/test/*

## Transpile Javascript code into a non ES6 format, for older browsers or Node.js v4 AND test this code AND upload it to codecov (testing services only)
js_compat_codecov: js_compat_test
	@node node_modules/codecov/bin/codecov -f coverage/coverage.json --token=d89f9bd9-27a3-4560-8dbb-39ee3ba020a5

## Transpile Javascript code into a non ES6 format, for older browsers or Node.js v4 AND package it into browser bundles
browser-compat: js-compat
	@echo "Building browser version..."
	@cd build/babel;\
	node ../../node_modules/browserify/bin/cmd.js -r ./base.js -o ../browser-compat/js2p-browser-$(jsver)-base.babel.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../../node_modules/browserify/bin/cmd.js -x ./base.js -r ./mesh.js -o ../browser-compat/js2p-browser-$(jsver)-mesh.babel.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../../node_modules/browserify/bin/cmd.js -x ./base.js -x ./mesh.js -r ./sync.js -o ../browser-compat/js2p-browser-$(jsver)-sync.babel.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../../node_modules/browserify/bin/cmd.js -x ./base.js -x ./mesh.js -r ./chord.js -o ../browser-compat/js2p-browser-$(jsver)-chord.babel.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../../node_modules/browserify/bin/cmd.js -x ./base.js -x ./mesh.js -x ./sync.js -x ./chord.js -e ./js2p.js -o ../browser-compat/js2p-browser-$(jsver).babel.js -s js2p

## Transpile Javascript code into a non ES6 format, for older browsers or Node.js v4 AND package it into browser bundles, then minify it
browser-compat-min: browser-compat
	@mkdir -p build/browser-compat-min
	@echo "Minifying..."
	@node node_modules/babel-cli/bin/babel.js ./build/browser-compat/js2p-browser-$(jsver).babel.js       -o ./build/browser-compat-min/js2p-browser-$(jsver).babel.min.js       --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser-compat/js2p-browser-$(jsver)-base.babel.js  -o ./build/browser-compat-min/js2p-browser-$(jsver)-base.babel.min.js  --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser-compat/js2p-browser-$(jsver)-mesh.babel.js  -o ./build/browser-compat-min/js2p-browser-$(jsver)-mesh.babel.min.js  --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser-compat/js2p-browser-$(jsver)-sync.babel.js  -o ./build/browser-compat-min/js2p-browser-$(jsver)-sync.babel.min.js  --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser-compat/js2p-browser-$(jsver)-chord.babel.js -o ./build/browser-compat-min/js2p-browser-$(jsver)-chord.babel.min.js --minified --no-comments --no-babelrc

## Alias for the above
browser-min-compat: browser-compat-min

#End Javascript section
#Begin Python section

## Build python-only code for whatever your default system python is
python:
	@cd py2p; $(MAKE) python

## Build python-only code for whatever your system python3 version is
python3:
	@cd py2p; $(MAKE) python3

## Build python-only code for whatever your system python2 version is
python2:
	@cd py2p; $(MAKE) python2

## Build python-only code for whatever your system pypy version is
pypy:
	@cd py2p; $(MAKE) pypy

cpython:
	@cd py2p; $(MAKE) cpython

## Build binary and python code for whatever your system python3 version is
cpython3:
	@cd py2p; $(MAKE) cpython3

## Build binary and python code for whatever your system python2 version is
cpython2:
	@cd py2p; $(MAKE) cpython2

## Install python test dependencies
pytestdeps:
	@cd py2p; $(MAKE) pytestdeps

## Install python2 test dependencies
py2testdeps:
	@cd py2p; $(MAKE) py2testdeps

## Install python3 test dependencies
py3testdeps:
	@cd py2p; $(MAKE) py3testdeps

## Run python tests
pytest:
	@cd py2p; $(MAKE) pytest

## Run python2 tests
py2test:
	@cd py2p; $(MAKE) py2test

## Run python3 tests
py3test:
	@cd py2p; $(MAKE) py3test

## Run cpython tests
cpytest:
	@cd py2p; $(MAKE) cpytest

## Run cpython2 tests
cpy2test:
	@cd py2p; $(MAKE) cpy2test

## Run cpython3 tests
cpy3test:
	@cd py2p; $(MAKE) cpy3test

## Format the python code in place with YAPF
pyformat:
	@cd py2p; $(MAKE) pyformat

## Run mypy tests
mypy:
	@cd py2p; $(MAKE) mypy

## Build html documentation
html: jsdocs submodules
	@python $(docs_deps)
	@cd docs; $(MAKE) clean html

#End Python section
#Begin General section

## Clean up local folders, including Javascript depenedencies
clean:
	@rm -rf .cache build docs/py2p node_modules
	@find docs/c          ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@find docs/cpp        ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@find docs/java       ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@find docs/javascript ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@cd docs; $(MAKE) clean
	@cd py2p; $(MAKE) clean

## Run all python-related build recipes
py_all:
	@cd py2p; $(MAKE) all

## Run all Javascript-related build recipes
js_all: LICENSE ES5 html browser browser-min browser-compat browser-compat-min

## Run all test-related recipes
test_all: LICENSE clean jstest js_compat_test mypy pytest cpy2test cpy3test
