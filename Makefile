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

#End python setup section
#Begin C section

## Initialize submodules
submodules:
	@git submodule update --init --recursive

build:
	@mkdir -p build

#End C section
#Begin Javascript section

jsver = $(shell node -p "require('./package.json').version")

## Install Javascript dependencies, preferring to use yarn, but using npm if it must
jsdeps:
	@cd js2p; $(MAKE) jsdeps

## Copying documentation from C-like language into the proper Restructred Text files
jsdocs:
	@echo "Copying documentation comments..."
	@node docs/docs_walker.js

## Run Javascript test code
jstest:
	@cd js2p; $(MAKE) jstest

## Run Javascript tests AND upload results to codecov (testing services only)
js_codecov:
	@cd js2p; $(MAKE) js_codecov

## Package Javascript code into browser bundles
browser: build
	@cd js2p; $(MAKE) browser
	@cp -fur -t build js2p/build/*

## Package Javascript code into browser bundles and minify them
browser-min: build
	@cd js2p; $(MAKE) browser-min
	@cp -fur -t build js2p/build/*

## Transpile Javascript code into a non ES6 format, for older browsers or Node.js v4
js-compat: build
	@cd js2p; $(MAKE) js-compat
	@cp -fur -t build js2p/build/*

## Transpile Javascript code into a non ES6 format, for older browsers or Node.js v4 AND test this code
js_compat_test: build
	@cd js2p; $(MAKE) js_compat_test
	@cp -fur -t build js2p/build/*

## Transpile Javascript code into a non ES6 format, for older browsers or Node.js v4 AND test this code AND upload it to codecov (testing services only)
js_compat_codecov: build
	@cd js2p; $(MAKE) js_compat_codecov
	@cp -fur -t build js2p/build/*

## Transpile Javascript code into a non ES6 format, for older browsers or Node.js v4 AND package it into browser bundles
browser-compat: build
	@cd js2p; $(MAKE) browser-compat
	@cp -fur -t build js2p/build/*

## Transpile Javascript code into a non ES6 format, for older browsers or Node.js v4 AND package it into browser bundles, then minify it
browser-compat-min: build
	@cd js2p; $(MAKE) browser-compat-min
	@cp -fur -t build js2p/build/*

## Alias for the above
browser-min-compat: browser-compat-min

#End Javascript section
#Begin Python section

## Build python-only code for whatever your default system python is
python: build
	@cd py2p; $(MAKE) python
	@cp -fur -t build py2p/build/*

## Build python-only code for whatever your system python3 version is
python3: build
	@cd py2p; $(MAKE) python3
	@cp -fur -t build py2p/build/*

## Build python-only code for whatever your system python2 version is
python2: build
	@cd py2p; $(MAKE) python2
	@cp -fur -t build py2p/build/*

## Build python-only code for whatever your system pypy version is
pypy: build
	@cd py2p; $(MAKE) pypy
	@cp -fur -t build py2p/build/*

cpython: build
	@cd py2p; $(MAKE) cpython
	@cp -fur -t build py2p/build/*

## Build binary and python code for whatever your system python3 version is
cpython3: build
	@cd py2p; $(MAKE) cpython3
	@cp -fur -t build py2p/build/*

## Build binary and python code for whatever your system python2 version is
cpython2: build
	@cd py2p; $(MAKE) cpython2
	@cp -fur -t build py2p/build/*

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
cpytest: build
	@cd py2p; $(MAKE) cpytest
	@cp -fur -t build py2p/build/*

## Run cpython2 tests
cpy2test: build
	@cd py2p; $(MAKE) cpy2test
	@cp -fur -t build py2p/build/*

## Run cpython3 tests
cpy3test: build
	@cd py2p; $(MAKE) cpy3test
	@cp -fur -t build py2p/build/*

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
	@rm -rf .cache build docs/py2p
	@find docs/c          ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@find docs/cpp        ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@find docs/java       ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@find docs/javascript ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@cd docs; $(MAKE) clean
	@cd py2p; $(MAKE) clean
	@cd js2p; $(MAKE) clean

## Run all python-related build recipes
py_all:
	@cd py2p; $(MAKE) all

## Run all Javascript-related build recipes
js_all:
	@cd js2p; $(MAKE) all

## Run all test-related recipes
test_all: LICENSE clean jstest js_compat_test mypy pytest cpy2test cpy3test
