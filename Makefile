pep8:
	flake8 pybbm --ignore=E501,E127,E128,E124

test:
	DJANGO_SETTINGS_MODULE=tests.settings python manage.py test --verbosity 2

release:
	python setup.py sdist register upload -s
