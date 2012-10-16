default: test

.PHONY: default test doc egg

test:
	nosetests2 --with-coverage --cover-package=lovett
	coverage2 html

doc:
	epydoc --html -v -o docs lovett/

sdist:
	python setup.py sdist
