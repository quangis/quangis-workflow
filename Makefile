VIRTUAL_ENV?= ./venv
VENV:= . ${VIRTUAL_ENV}/bin/activate &&

${VIRTUAL_ENV}: requirements.txt
	test -d "${VIRTUAL_ENV}" || virtualenv "${VIRTUAL_ENV}"
	${VENV} pip install -Ur requirements.txt

solutions: ${VIRTUAL_ENV}
	-mkdir -p build/
	${VENV} quangis synthesis -d build/ -x --tools data/all.ttl --config data/ioconfig.ttl

abstract-workflows: ${VIRTUAL_ENV}
	-mkdir -p build/
	${VENV} quangis convert-abstract -d build/ -x --tools data/all.ttl workflows-concrete/*.ttl

build/repo.ttl: ${VIRTUAL_ENV}
	-mkdir -p build/
	${VENV} quangis update-tools -o build/repo.ttl -x --tools data/all.ttl workflows-concrete/*.ttl

.PHONY: solutions abstract-workflows
