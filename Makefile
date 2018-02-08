PYTHON=`which python`
DESTDIR=/
PROJECT=python-mdnsbridge

TEST_DEPS=\
	mock \
	systemd

VENV=virtpython
VENV_ACTIVATE=$(VENV)/bin/activate
VENV_MODULE_DIR=$(VENV)/lib/python2.7/site-packages
VENV_TEST_DEPS=$(addprefix $(VENV_MODULE_DIR)/,$(TEST_DEPS))

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
	find . -name '*.pyc' -delete
	find . -name '*.py,cover' -delete
	rm -rf $(VENV)

$(VENV):
	virtualenv --system-site-packages $@

$(VENV_TEST_DEPS): $(VENV)
	. $(VENV_ACTIVATE); pip install $(@F)

test: $(VENV_TEST_DEPS)
	. $(VENV_ACTIVATE); nose2 --with-coverage --coverage=mdnsbridge --coverage-report=annotate --coverage-report=term

.PHONY: test clean deb install source all
