BUILD_DIR=testbuild
DEBUG_DIR=build
UTIL=python3 utils/util.py
JENA=build/apache-jena-4.3.2/bin
FUSEKI=build/apache-jena-fuseki-4.3.2/fuseki-server
TIMEOUT=60000

all: $(BUILD_DIR)/tdb-insular/nodes.dat $(BUILD_DIR)/tdb-normal/nodes.dat

graphs: $(BUILD_DIR)/cct.ttl $(patsubst scenarios/%.ttl,$(BUILD_DIR)/%.ttl,$(wildcard scenarios/*.ttl))

evaluations: $(BUILD_DIR)/eval.csv

queries: $(patsubst queries/%.json,$(BUILD_DIR)/%.rq,$(wildcard queries/*.json))

# Serving

server-normal: $(BUILD_DIR)/tdb-normal/nodes.dat
	$(FUSEKI) $(if $(TIMEOUT),--timeout=$(TIMEOUT),) --loc="$(<D)" /name

server-insular: $(BUILD_DIR)/tdb-insular/nodes.dat
	$(FUSEKI) $(if $(TIMEOUT),--timeout=$(TIMEOUT),) --loc="$(<D)" /name

$(BUILD_DIR)/tdb-insular/nodes.dat: $(BUILD_DIR)/cct.ttl $(patsubst scenarios/%.ttl,$(BUILD_DIR)/%.insular.ttl,$(wildcard scenarios/*.ttl))
	$(JENA)/tdb1.xloader --loc $(@D) $^

$(BUILD_DIR)/tdb-normal/nodes.dat: $(BUILD_DIR)/cct.ttl $(patsubst scenarios/%.ttl,$(BUILD_DIR)/%.ttl,$(wildcard scenarios/*.ttl))
	$(JENA)/bin/tdb1.xloader --loc $(@D) $^


# Building graphs

$(BUILD_DIR)/cct.ttl: cct.py
	@rm -f $@
	@mkdir -p $(@D)
	$(UTIL) vocab $@

$(BUILD_DIR)/%.insular.ttl: scenarios/%.ttl
	@rm -f $@
	@mkdir -p $(@D)
	$(UTIL) graph --no-passthrough $< $@

$(BUILD_DIR)/%.ttl: scenarios/%.ttl
	@rm -f $@
	@mkdir -p $(@D)
	$(UTIL) graph $< $@


# Queries

$(BUILD_DIR)/%.rq: queries/%.json
	@mkdir -p $(@D)
	python3 -c 'from cct import cct; from transformation_algebra.query import Query; print(Query.from_file(cct, "$<").sparql())' > $@

$(BUILD_DIR)/eval.csv: $(wildcard queries/*_eval.json)
	@rm -f $@
	@mkdir -p $(@D)
	$(UTIL) query $^ -o $@


# Other

$(BUILD_DIR)/results.tex: $(BUILD_DIR)/results.csv
	@mkdir -p $(@D)
	< $< csvcut -c Variant,Options,Precision,Recall \
		| csvsort | csv2latex > $@


.PHONY: all graphs queries evaluations serve-insular serve-normal
