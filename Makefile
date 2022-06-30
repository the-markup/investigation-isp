.PHONY: venv reproduce

venv:
	python -m venv venv
	. venv/bin/activate
	pip install -r requirements.txt

reproduce:
	nbexec notebooks