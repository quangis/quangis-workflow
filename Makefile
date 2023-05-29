VIRTUAL_ENV?= ./venv
DEST?= build/
CONFIG?=data/ioconfig.ttl
TOOLS?=build/repo.ttl

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
ABSTRACT_WORKFLOWS:=$(patsubst ${CONCRETE_WORKFLOWS},workflows-concrete/%.ttl,${DEST}/workflows-abstract/%.ttl)
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
	. ${VENV} && transforge vocab "$<" -o "$@" -t ttl

# All manual workflows, decorated with transformation graphs
build/graph.trig: ${TOOLS} ${MANUAL_WORKFLOWS}
	transforge graph cct -T "${TOOLS}" --skip-error \
		${MANUAL_WORKFLOWS} -o "$@" -t trig

# Skeleton tasks are tasks where basic types are replaced with the 
# highest-level basic type (apart from Top)
SKELETON_TASKS:=$(patsubst ${TASKS},tasks/%.ttl,${DEST}/skeletons/%.ttl)
${DEST}/task-skeletons/%.ttl: tasks/%.ttl
	${VENV} python3 pp/preprocess.py "$<" > "$@"
skeletons: ${SKELETON_TASKS}
.PHONY: skeletons
