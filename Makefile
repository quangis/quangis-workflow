VIRTUAL_ENV?=./venv
DEST?=build
CONFIG?=data/ioconfig.ttl
TOOLS?=build/repo.ttl
MARKLOGIC?=marklogic@https://127.0.0.1:8000
CRED?=user:password

VENV=${VIRTUAL_ENV}/bin/activate
PY=$(shell find quangis/ -name '*.py')

MANUAL_WORKFLOWS:=$(shell find workflows/ -name '*.ttl')
TASKS:=$(shell find tasks/ -name '*.ttl')
CONCRETE_WORKFLOWS:=$(shell find workflows-concrete/ -name '*.ttl')

${VIRTUAL_ENV}: requirements.txt
	test -d "${VIRTUAL_ENV}" || python -m venv "${VIRTUAL_ENV}"
	. ${VENV} && pip install -Ur requirements.txt
	. ${VENV} && pip install -e .

# Generate workflows
solutions: ${TOOLS} ${PY} ${VENV} ${TOOLS} ${CONFIG}
	-mkdir -p "${DEST}"
	. ${VENV} && quangis synthesis \
		-d "${DEST}" \
		--tools "${TOOLS}" -x \
		--config "${CONFIG}"
.PHONY: solutions

# Convert concrete workflows into abstract ones
ABSTRACT_WORKFLOWS:=$(patsubst workflows-concrete/%.ttl,${DEST}/workflows-abstract/%.ttl,${CONCRETE_WORKFLOWS})
${DEST}/workflows-abstract/%.ttl: workflows-concrete/%.ttl ${VENV} ${PY} ${TOOLS}
	-mkdir -p "${@D}"
	-rm -f "$@"
	. ${VENV} && quangis convert-abstract \
		-d "${DEST}" \
		--tools "${TOOLS}" -x \
		"$<"
abstract-workflows: ${ABSTRACT_WORKFLOWS}
.PHONY: abstract-workflows

# Tool repository built upon existing tool repository, expanded with tools 
# extracted from concrete workflows
${DEST}/repo.ttl: data/all.ttl ${CONCRETE_WORKFLOWS} ${VENV} ${PY}
	-mkdir -p ${DEST}
	. ${VENV} && quangis update-tools \
		-o "$@" \
		--tools "$<" -x \
		${CONCRETE_WORKFLOWS}

# Vocabulary for the CCT algebra
${DEST}/cct.ttl: quangis/cctrans.py ${VENV}
	-mkdir -p "${@D}"
	. ${VENV} && transforge vocab "$<" -o "$@" -t ttl

# All manual workflows, decorated with transformation graphs
build/graph.trig: ${TOOLS} ${MANUAL_WORKFLOWS}
	-mkdir -p "${@D}"
	. ${VENV} && transforge graph cct -T "${TOOLS}" --skip-error \
		${MANUAL_WORKFLOWS} -o "$@" -t trig

# Skeleton tasks are tasks where basic types are replaced with the 
# highest-level basic type (underneath `Top`)
SKELETON_TASKS:=$(patsubst tasks/%.ttl,${DEST}/task-skeletons/%.ttl,${TASKS})

${DEST}/task-skeletons/%.ttl: tasks/%.ttl scripts/preprocess.py
	-mkdir -p "${@D}"
	. ${VENV} && python3 scripts/preprocess.py "$<" > "$@"

skeletons: ${SKELETON_TASKS}
.PHONY: skeletons


# Queries #

${DEST}/results/skeletal.csv: ${VENV} ${SKELETON_TASKS}
	-mkdir -p "${@D}"
	. ${VENV} && transforge query cct -s "${MARKLOGIC}" -u "${CRED}" ${SKELETON_TASKS} --summary "$@"
results: ${DEST}/results/skeletal.csv
.PHONY: results
