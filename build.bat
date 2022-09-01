:: upload the package to pypi
:: https://packaging.python.org/en/latest/tutorials/packaging-projects/
python -m pip install --upgrade build
python -m build
python -m twine upload --repository testpypi dist/*

:: test the package
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps lost-cat

:: upload to pypi
:: python -m twine upload --repository pypi dist/*
