if [ $pyver ]; then
    pip install pytest-coverage codecov
    py.test -vv --cov=./py_src/ ./py_src/
    python setup.py sdist --universal && pip install --no-index --find-links=./dist/ py2p
    mv .coverage .covvv
    make cpytest cov=true
    mv .covvv .coverage.1
    mv .coverage .coverage.2
else
    make jstest;
    make ES5test;
fi