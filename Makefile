PYTHON=`which python`
DESTDIR=/

all:
	@echo "make source - Create source package"
	@echo "make install - Install on local system (only during development)"
	@echo "make deb - Generate a deb package - for local testing"
	@echo "make clean - Get rid of scratch and byte files"

source:
	$(PYTHON) setup.py sdist $(COMPILE)

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

deb:
	debuild -uc -us

clean:
	$(PYTHON) setup.py clean
	dh_clean
	rm -rf build/ MANIFEST
	rm -rf dist/
	rm -rf tox-generated.ini
	rm -rf .tox
	rm -rf *.egg-info
	find . -name '*.pyc' -delete
	find . -name '*.py,cover' -delete

test:
	tox

.PHONY: test clean deb install source all
