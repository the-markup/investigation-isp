.PHONY: venv reproduce

venv:
	python -m venv venv
	. venv/bin/activate
	pip install -r requirements.txt

run:
	nbexec notebooks

download:
    sh download_data.sh