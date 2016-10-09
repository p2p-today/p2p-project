if [ $py_ver ]; then
    python -m coverage combine;
    python -m coverage xml;
    codecov --token=d89f9bd9-27a3-4560-8dbb-39ee3ba020a5 --file=coverage.xml
fi