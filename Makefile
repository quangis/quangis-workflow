VIRTUAL_ENV?= ./venv
VENV:= . ${VIRTUAL_ENV}/bin/activate &&
PY:= $(shell find quangis -name '*.py')

${VIRTUAL_ENV}: requirements.txt
	test -d "${VIRTUAL_ENV}" || python -m venv "${VIRTUAL_ENV}"
	${VENV} pip install -Ur requirements.txt
	${VENV} pip install -e .

solutions: ${VIRTUAL_ENV} ${PY}
	-mkdir -p build/
	${VENV} quangis synthesis -d build/ -x --tools data/all.ttl --config data/ioconfig.ttl

abstract-workflows: ${VIRTUAL_ENV} ${PY} build/repo.ttl
	-mkdir -p build/
	rm -f build/wf*.ttl
	${VENV} quangis convert-abstract -d build/ -x --tools build/repo.ttl workflows-concrete/*.ttl

build/repo.ttl: ${VIRTUAL_ENV} ${PY}
	-mkdir -p build/
	${VENV} quangis update-tools -o build/repo.ttl --tools data/all.ttl workflows-concrete/*.ttl

.PHONY: solutions abstract-workflows
