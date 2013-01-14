pep8:
	flake8 pybbm --ignore=E501,E127,E128,E124

test:
	coverage run --branch --source=pybb manage.py test -s -x --with-progressive pybb
	coverage report --omit=pybb/test*,pybb/management/*

coverage:
	python manage.py test -s -x --with-progressive pybb --with-coverage --cover-html --cover-html-dir=./coverage --cover-package=pybb

release:
	python setup.py sdist register upload -s

