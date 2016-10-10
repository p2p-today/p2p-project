IF DEFINED PIP (
    ECHO %PYTHON% %PYTHON_VERSION%%APPVEYOR_BUILD_FOLDER%
    set HOME=%APPVEYOR_BUILD_FOLDER%
    %PYPY%
    %PIP% install pytest-coverage codecov cryptography
    cd %HOME%
    %RUN% -m pytest -c setup.cfg --cov=./py_src/ ./py_src/
    %RUN% setup.py sdist --universal
    %PIP% install --no-index --find-links=.\\dist\\ py2p
    %RUN% setup.py build
    FOR /F %%v IN ('%RUN% -c "import sys, sysconfig; print(\'{}.{}-{v[0]}.{v[1]}\'.format(\'lib\', sysconfig.get_platform(), v=sys.version_info))"') DO SET BUILD_DIR=%%v
    ren .coverage .covvv
    %RUN% -m pytest -c setup.cfg --cov=build\\%BUILD_DIR% build\\%BUILD_DIR%
    ren .covvv .coverage.1
    ren .coverage .coverage.2
    %COV% combine
    %COV% xml
    %RUN% -c "import codecov; codecov.main('--token=d89f9bd9-27a3-4560-8dbb-39ee3ba020a5', '--file=coverage.xml')"
) ELSE (
    powershell -Command "Install-Product node $env:NODE"
    npm install .
    npm install -g mocha babel-cli
    mocha js_src\\test\\*
    babel js_src --out-dir build\\es5
    mocha build\\es5\\test\\*
)
