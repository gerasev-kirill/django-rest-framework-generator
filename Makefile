install_virtualenv:
	rm -fr .virtualenv/p2 || true
	virtualenv  --system-site-packages .virtualenv/p2
	chmod +x .virtualenv/p2/bin/activate
	ln -s .virtualenv/p2/bin/activate ap2 || true
	bash -c "source ap2; pip2 install -r ./requirements.django.txt"

run_tests:
	bash -c "source ap2; python2 ./runtests.py"

install_virtualenv3:
	rm -fr .virtualenv/p3 || true
	virtualenv .virtualenv/p3
	chmod +x .virtualenv/p3/bin/activate
	ln -s .virtualenv/p3/bin/activate ap3 || true
	bash -c "source ap3; pip3 install -r ./requirements.django3.txt"

run_tests3:
	bash -c "source ap3; python3 ./runtests.py"
