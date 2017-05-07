pep8:
	flake8 pybbm --ignore=E501,E127,E128,E124

test:
	py.test tests/ -s

release:
	python setup.py sdist register upload -s
