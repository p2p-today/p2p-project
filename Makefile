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

## Initialize the msgpack module (and incidentally other submodules)
msgpack_module:
	@git submodule update --init

#End C section
#Begin Javascript section

jsver = $(shell node -p "require('./package.json').version")

## Install Javascript dependencies, preferring to use yarn, but using npm if it must
jsdeps: LICENSE
	@yarn || npm install

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
python: LICENSE setup.py
	@echo "Checking dependencies..."
	@python $(py_deps) --upgrade
	@python $(pip) -r requirements.txt --upgrade $(user_postfix)
	@echo "Building python-only version..."
	@python setup.py build --universal

## Build python-only code for whatever your system python3 version is
python3: LICENSE setup.py
	@echo "Checking dependencies..."
	@$(python3) $(py_deps) --upgrade
	@$(python3) $(pip) -r requirements.txt --upgrade $(user_postfix)
	@echo "Building python-only version..."
	@$(python3) setup.py build --universal

## Build python-only code for whatever your system python2 version is
python2: LICENSE setup.py
	@echo "Checking dependencies..."
	@$(python2) $(py_deps) --upgrade
	@$(python2) $(pip) -r requirements.txt --upgrade $(user_postfix)
	@echo "Building python-only version..."
	@$(python2) setup.py build --universal

## Build python-only code for whatever your system pypy version is
pypy: LICENSE setup.py
	@echo "Checking dependencies..."
	@pypy $(py_deps) --upgrade
	@pypy $(pip) -r requirements.txt --upgrade $(user_postfix)
	@echo "Building python-only version..."
	@pypy setup.py build --universal

ifeq ($(pypy), True)
cpython: python

else
## Build binary and python code for whatever your default system python is (python-only if that's pypy)
cpython: python msgpack_module
	@echo "Building with C extensions..."
ifeq ($(debug), true)
	@python setup.py build --debug
else
	@python setup.py build
endif
endif

## Build binary and python code for whatever your system python3 version is
cpython3: python3 msgpack_module
	@echo "Building with C extensions..."
ifeq ($(debug), true)
	@$(python3) setup.py build --debug
else
	@$(python3) setup.py build
endif

## Build binary and python code for whatever your system python2 version is
cpython2: python2 msgpack_module
	@echo "Building with C extensions..."
ifeq ($(debug), true)
	@$(python2) setup.py build --debug
else
	@$(python2) setup.py build
endif

## Install python test dependencies
pytestdeps:
	@echo "Checking test dependencies..."
	@python $(py_test_deps) --upgrade

## Install python2 test dependencies
py2testdeps:
	@echo "Checking test dependencies..."
	@$(python2) $(py_test_deps) --upgrade

## Install python3 test dependencies
py3testdeps:
	@echo "Checking test dependencies..."
	@$(python3) $(py_test_deps) --upgrade

## Run python tests
pytest: LICENSE setup.py setup.cfg python pytestdeps
ifeq ($(cov), true)
	@python -m pytest -c ./setup.cfg --cov=build/$(pyunvlibdir) build/$(pyunvlibdir)
else
	@python -m pytest -c ./setup.cfg build/$(pyunvlibdir)
endif

## Run python2 tests
py2test: LICENSE setup.py setup.cfg python2 py2testdeps
ifeq ($(cov), true)
	@$(python2) -m pytest -c ./setup.cfg --cov=build/$(py2libdir) build/$(py2libdir)
else
	@$(python2) -m pytest -c ./setup.cfg build/$(py2libdir)
endif

## Run python3 tests
py3test: LICENSE setup.py setup.cfg python3 py3testdeps
	@echo $(py3libdir)
ifeq ($(cov), true)
	@$(python3) -m pytest -c ./setup.cfg --cov=build/lib build/lib
else
	@$(python3) -m pytest -c ./setup.cfg build/lib
endif

ifeq ($(pypy), True)
cpytest: pytest

else
## Run cpython tests
cpytest: LICENSE setup.py setup.cfg cpython pytestdeps
ifeq ($(cov), true)
	@python -m pytest -c ./setup.cfg --cov=build/$(pylibdir) build/$(pylibdir)
else
	@python -m pytest -c ./setup.cfg build/$(pylibdir)
endif
endif

## Run cpython2 tests
cpy2test: LICENSE setup.py setup.cfg cpython2 py2testdeps
ifeq ($(cov), true)
	@$(python2) -m pytest -c ./setup.cfg --cov=build/$(py2libdir) build/$(py2libdir)
else
	@$(python2) -m pytest -c ./setup.cfg build/$(py2libdir)
endif

## Run cpython3 tests
cpy3test: LICENSE setup.py setup.cfg cpython3 py3testdeps
ifeq ($(cov), true)
	@$(python3) -m pytest -c ./setup.cfg --cov=build/$(py3libdir) build/$(py3libdir)
else
	@$(python3) -m pytest -c ./setup.cfg build/$(py3libdir)
endif

## Format the python code in place with YAPF
pyformat: clean
	@$(python3) -m pip install yapf --upgrade $(user_postfix)
	@$(python3) -m yapf py_src -ri
	@$(MAKE) mypy pytest

## Run mypy tests
mypy:
	@$(python3) -m pip install mypy --upgrade $(user_postfix)
	@$(python3) -m mypy . --check-untyped-defs --ignore-missing-imports --disallow-untyped-calls --disallow-untyped-defs

## Build html documentation
html: jsdocs msgpack_module
	@python $(docs_deps)
	@cd docs; $(MAKE) clean html

#End Python section
#Begin General section

## Clean up local folders, including Javascript depenedencies
clean:
	@rm -rf .benchmarks .cache build coverage dist docs/py2p node_modules py2p venv py_src/__pycache__ \
	py_src/test/__pycache__ py_src/*.pyc py_src/test/*.pyc py_src/*.so
	@find docs/c          ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@find docs/cpp        ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@find docs/java       ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@find docs/javascript ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@cd docs; $(MAKE) clean

## Run all python-related build recipes
py_all: LICENSE setup.py setup.cfg python2 python3 html cpython2 cpython3 pypy

## Run all Javascript-related build recipes
js_all: LICENSE ES5 html browser browser-min browser-compat browser-compat-min

## Run all test-related recipes
test_all: LICENSE clean jstest js_compat_test mypy pytest cpy2test cpy3test
