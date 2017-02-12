#Python setup section

pip = -m pip install
py_deps = $(pip) cryptography --upgrade
py_test_deps = $(pip) pytest-coverage pytest-benchmark
docs_deps = $(pip) sphinx sphinxcontrib-napoleon sphinx_rtd_theme

ifeq ($(shell python -c 'import sys; print(int(hasattr(sys, "real_prefix")))'), 0) # check for virtualenv
	py_deps += --user
	py_test_deps += --user
	docs_deps += --user
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

msgpack_module:
	@git submodule update --init

#End C section
#Begin Javascript section

jsver = $(shell node -p "require('./package.json').version")

jsdeps: LICENSE
	@yarn || npm install

jsdocs:
	@echo "Copying documentation comments..."
	@node js_src/docs_test.js

jstest: jsdeps
	@node node_modules/istanbul/lib/cli.js cover node_modules/mocha/bin/_mocha js_src/test/*

js_codecov: jstest
	@node node_modules/codecov/bin/codecov -f coverage/coverage.json --token=d89f9bd9-27a3-4560-8dbb-39ee3ba020a5

browser: jsdeps
	@mkdir -p build/browser
	@echo "Building browser version..."
	@cd js_src;\
	node ../node_modules/browserify/bin/cmd.js -r ./base.js -o ../build/browser/js2p-browser-$(jsver)-base.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../node_modules/browserify/bin/cmd.js -x ./base.js -r ./mesh.js -o ../build/browser/js2p-browser-$(jsver)-mesh.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../node_modules/browserify/bin/cmd.js -x ./base.js -x ./mesh.js -r ./sync.js -o ../build/browser/js2p-browser-$(jsver)-sync.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../node_modules/browserify/bin/cmd.js -x ./base.js -x ./mesh.js -r ./sync.js -o ../build/browser/js2p-browser-$(jsver)-chord.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../node_modules/browserify/bin/cmd.js -x ./base.js -x ./mesh.js -x ./sync.js -x ./chord.js -e ./js2p.js -o ../build/browser/js2p-browser-$(jsver).js -s js2p

browser-min: browser
	@mkdir -p build/browser-min
	@echo "Minifying..."
	@node node_modules/babel-cli/bin/babel.js ./build/browser/js2p-browser-$(jsver).js       -o ./build/browser-min/js2p-browser-$(jsver).min.js       --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser/js2p-browser-$(jsver)-base.js  -o ./build/browser-min/js2p-browser-$(jsver)-base.min.js  --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser/js2p-browser-$(jsver)-mesh.js  -o ./build/browser-min/js2p-browser-$(jsver)-mesh.min.js  --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser/js2p-browser-$(jsver)-sync.js  -o ./build/browser-min/js2p-browser-$(jsver)-sync.min.js  --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser/js2p-browser-$(jsver)-chord.js -o ./build/browser-min/js2p-browser-$(jsver)-chord.min.js --minified --no-comments --no-babelrc

js-compat: jsdeps
	@mkdir -p build/browser-compat build/babel
	@echo "Transpiling..."
	@node node_modules/babel-cli/bin/babel.js js_src -d build/babel

js_compat_test: js-compat
	@echo "Testing transpilation..."
	@node node_modules/istanbul/lib/cli.js cover node_modules/mocha/bin/_mocha build/babel/test/*

js_compat_codecov: js_compat_test
	@node node_modules/codecov/bin/codecov -f coverage/coverage.json --token=d89f9bd9-27a3-4560-8dbb-39ee3ba020a5

browser-compat: js-compat
	@echo "Building browser version..."
	@cd build/babel;\
	node ../../node_modules/browserify/bin/cmd.js -r ./base.js -o ../browser-compat/js2p-browser-$(jsver)-base.babel.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../../node_modules/browserify/bin/cmd.js -x ./base.js -r ./mesh.js -o ../browser-compat/js2p-browser-$(jsver)-mesh.babel.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../../node_modules/browserify/bin/cmd.js -x ./base.js -x ./mesh.js -r ./sync.js -o ../browser-compat/js2p-browser-$(jsver)-sync.babel.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../../node_modules/browserify/bin/cmd.js -x ./base.js -x ./mesh.js -r ./sync.js -o ../browser-compat/js2p-browser-$(jsver)-chord.babel.js -u snappy -u nodejs-websocket -u node-forge;\
	node ../../node_modules/browserify/bin/cmd.js -x ./base.js -x ./mesh.js -x ./sync.js -x ./chord.js -e ./js2p.js -o ../browser-compat/js2p-browser-$(jsver).babel.js -s js2p

browser-compat-min: browser-compat
	@mkdir -p build/browser-compat-min
	@echo "Minifying..."
	@node node_modules/babel-cli/bin/babel.js ./build/browser-compat/js2p-browser-$(jsver).babel.js       -o ./build/browser-compat-min/js2p-browser-$(jsver).babel.min.js       --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser-compat/js2p-browser-$(jsver)-base.babel.js  -o ./build/browser-compat-min/js2p-browser-$(jsver)-base.babel.min.js  --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser-compat/js2p-browser-$(jsver)-mesh.babel.js  -o ./build/browser-compat-min/js2p-browser-$(jsver)-mesh.babel.min.js  --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser-compat/js2p-browser-$(jsver)-sync.babel.js  -o ./build/browser-compat-min/js2p-browser-$(jsver)-sync.babel.min.js  --minified --no-comments --no-babelrc
	@node node_modules/babel-cli/bin/babel.js ./build/browser-compat/js2p-browser-$(jsver)-chord.babel.js -o ./build/browser-compat-min/js2p-browser-$(jsver)-chord.babel.min.js --minified --no-comments --no-babelrc

browser-min-compat: browser-compat-min

#End Javascript section
#Begin Python section

python: LICENSE setup.py
	@echo "Checking dependencies..."
	@python $(py_deps) --upgrade
	@python $(pip) -r requirements.txt --user --upgrade
	@echo "Building python-only version..."
	@python setup.py build --universal

python3: LICENSE setup.py
	@echo "Checking dependencies..."
	@$(python3) $(py_deps) --upgrade
	@$(python3) $(pip) -r requirements.txt --user --upgrade
	@echo "Building python-only version..."
	@$(python3) setup.py build --universal

python2: LICENSE setup.py
	@echo "Checking dependencies..."
	@$(python2) $(py_deps) --upgrade
	@$(python2) $(pip) -r requirements.txt --user --upgrade
	@echo "Building python-only version..."
	@$(python2) setup.py build --universal

pypy: LICENSE setup.py
	@echo "Checking dependencies..."
	@pypy $(py_deps) --upgrade
	@pypy $(pip) -r requirements.txt --user --upgrade
	@echo "Building python-only version..."
	@pypy setup.py build --universal

ifeq ($(pypy), True)
cpython: python

else
cpython: python msgpack_module
	@echo "Building with C extensions..."
ifeq ($(debug), true)
	@python setup.py build --debug
else
	@python setup.py build
endif
endif

cpython3: python3 msgpack_module
	@echo "Building with C extensions..."
ifeq ($(debug), true)
	@$(python3) setup.py build --debug
else
	@$(python3) setup.py build
endif

cpython2: python2 msgpack_module
	@echo "Building with C extensions..."
ifeq ($(debug), true)
	@$(python2) setup.py build --debug
else
	@$(python2) setup.py build
endif

pytestdeps:
	@echo "Checking test dependencies..."
	@python $(py_test_deps) --upgrade

py2testdeps:
	@echo "Checking test dependencies..."
	@$(python2) $(py_test_deps) --upgrade

py3testdeps:
	@echo "Checking test dependencies..."
	@$(python3) $(py_test_deps) --upgrade

pytest: LICENSE setup.py setup.cfg python pytestdeps
ifeq ($(cov), true)
	@python -m pytest -c ./setup.cfg --cov=build/$(pyunvlibdir) build/$(pyunvlibdir)
else
	@python -m pytest -c ./setup.cfg build/$(pyunvlibdir)
endif

py2test: LICENSE setup.py setup.cfg python2 py2testdeps
ifeq ($(cov), true)
	@$(python2) -m pytest -c ./setup.cfg --cov=build/$(py2libdir) build/$(py2libdir)
else
	@$(python2) -m pytest -c ./setup.cfg build/$(py2libdir)
endif

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
cpytest: LICENSE setup.py setup.cfg cpython pytestdeps
ifeq ($(cov), true)
	@python -m pytest -c ./setup.cfg --cov=build/$(pylibdir) build/$(pylibdir)
else
	@python -m pytest -c ./setup.cfg build/$(pylibdir)
endif
endif

cpy2test: LICENSE setup.py setup.cfg cpython2 py2testdeps
ifeq ($(cov), true)
	@$(python2) -m pytest -c ./setup.cfg --cov=build/$(py2libdir) build/$(py2libdir)
else
	@$(python2) -m pytest -c ./setup.cfg build/$(py2libdir)
endif

cpy3test: LICENSE setup.py setup.cfg cpython3 py3testdeps
ifeq ($(cov), true)
	@$(python3) -m pytest -c ./setup.cfg --cov=build/$(py3libdir) build/$(py3libdir)
else
	@$(python3) -m pytest -c ./setup.cfg build/$(py3libdir)
endif

pyformat: clean
	@python3 -m pip install yapf --user --upgrade
	@python3 -m yapf py_src -ri
	@$(MAKE) pytest

html: jsdocs msgpack_module
	@python $(docs_deps)
	@cd docs; $(MAKE) clean html

#End Python section
#Begin General section

clean:
	@rm -rf .benchmarks .cache build coverage dist docs/py2p node_modules py2p venv py_src/__pycache__ \
	py_src/test/__pycache__ py_src/*.pyc py_src/test/*.pyc py_src/*.so
	@find docs/c          ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@find docs/cpp        ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@find docs/java       ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@find docs/javascript ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@find docs/go         ! -name 'tutorial.rst' ! -wholename '*/tutorial/*' -type f -exec rm -f {} +
	@cd docs; $(MAKE) clean

py_all: LICENSE setup.py setup.cfg python2 python3 html cpython2 cpython3 pypy

js_all: LICENSE ES5 html browser browser-min browser-compat browser-compat-min

test_all: LICENSE clean jstest ES5test pytest cpy2test cpy3test
