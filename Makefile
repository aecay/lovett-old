default: test

.PHONY: default test doc sdist

test:
	nosetests --with-coverage --cover-package=lovett --cover-branches
	coverage3 html

doc:
	epydoc --html -v -o docs lovett/

sdist:
	python setup.py sdist
