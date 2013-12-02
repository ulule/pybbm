pep8:
	flake8 pybbm --ignore=E501,E127,E128,E124

test:
	coverage run --branch --source=pybb manage.py test pybb
	coverage report --omit=pybb/test*,pybb/management/*

release:
	python setup.py sdist register upload -s
