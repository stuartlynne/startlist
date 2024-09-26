
# vim: noexpandtab tabstop=8 shiftwidth=8


DATES = $(wildcard *.date)
HTML = $(DATES:.date=.html)

%.html: %.date
	startlists --date $(<:.date=) 


all:
	@echo "make sdist | install | uninstall | bdist"

test: $(HTML)

clean:
	rm -f */*pyc
	rm -rf build dist *.egg-info

.PHONY: sdist install bdist


bdist:
	python3 setup.py $@
sdist:
	python3 setup.py $@
install:
	python3 setup.py $@
install-support:
	set -x; cp -vr bin/* /usr/local/bin

uninstall:
	pip3 uninstall qlmux
