if [ $pyver ]; then
    pip install codecov
    make cpython pytestdeps
    py.test -vv --cov=./py_src/ ./py_src/
    python setup.py sdist --universal && pip install --no-index --find-links=./dist/ py2p
    mv .coverage .covvv
    make cpytest cov=true
    mv .covvv .coverage.1
    mv .coverage .coverage.2
    coverage combine
    coverage xml
    codecov --token=d89f9bd9-27a3-4560-8dbb-39ee3ba020a5 --file=coverage.xml
elif [ $jsver ]; then
    make jstest
    make ES5test
fi
