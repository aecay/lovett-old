default: test

.PHONY: default test

test:
	nosetests2 --with-coverage --cover-package=lovett
	coverage html
