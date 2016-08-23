python: LICENSE setup.py
	python -m pip install cryptography --user; python setup.py build --universal

python3: LICENSE setup.py
	python3 -m pip install cryptography --user; python3 setup.py build --universal

python2: LICENSE setup.py
	python2 -m pip install cryptography --user; python2 setup.py build --universal

cpython: LICENSE setup.py
	python -m pip install cryptography --user; python setup.py build

cpython3: LICENSE setup.py
	python3 -m pip install cryptography --user; python3 setup.py build

cpython2: LICENSE setup.py
	python2 -m pip install cryptography --user; python2 setup.py build

pytest: LICENSE setup.py setup.cfg
	make python; python -m pip install pytest-coverage --user; python -m pytest -c ./setup.cfg build/lib

py2test: LICENSE setup.py setup.cfg
	make python2; python2 -m pip install pytest-coverage --user;  python2 -m pytest -c ./setup.cfg build/lib

py3test: LICENSE setup.py setup.cfg
	make python3; python3 -m pip install pytest-coverage --user;  python3 -m pytest -c ./setup.cfg build/lib

cpytest: LICENSE setup.py setup.cfg
	make cpython; python -m pip install pytest-coverage --user;  python -m pytest -c ./setup.cfg build/lib.*

cpy2test: LICENSE setup.py setup.cfg
	make cpython2; python2 -m pip install pytest-coverage --user;  python2 -m pytest -c ./setup.cfg build/lib.*2*

cpy3test: LICENSE setup.py setup.cfg
	make cpython3; python3 -m pip install pytest-coverage --user;  python3 -m pytest -c ./setup.cfg build/lib.*3*

html:
	cd ./docs; rm -r .build; make html

py_all: LICENSE setup.py setup.cfg
	make python; make cpython3; make cpython2; python -m pip install sphinx sphinxcontrib-napoleon --user; make html