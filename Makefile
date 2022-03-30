BUILD_DIR=testbuild
DEBUG_DIR=build
UTIL=python3 utils/util.py
FUSEKI=build/apache-jena-fuseki-4.3.2/fuseki-server
TIMEOUT=60000

graphs: \
	$(BUILD_DIR)/cct.ttl \
	$(patsubst scenarios/%.ttl,$(BUILD_DIR)/%/graph0.ttl,$(wildcard scenarios/*.ttl))

evaluations: $(BUILD_DIR)/eval.csv

queries: $(patsubst queries/%.json,$(BUILD_DIR)/%.rq,$(wildcard queries/*.json))

# Serving

$(BUILD_DIR)/db0.ttl: $(BUILD_DIR)/cct.ttl $(patsubst scenarios/%.ttl,$(BUILD_DIR)/%/graph0.ttl,$(wildcard scenarios/*.ttl))
	$(UTIL) merge $@ $^

$(BUILD_DIR)/db1.ttl: $(BUILD_DIR)/cct.ttl $(patsubst scenarios/%.ttl,$(BUILD_DIR)/%/graph1.ttl,$(wildcard scenarios/*.ttl))
	$(UTIL) merge $@ $^

server-insular: $(BUILD_DIR)/db0.ttl
	$(FUSEKI) --localhost --file="$<" \
		$(if $(TIMEOUT),--timeout=$(TIMEOUT),) \
		/name

server-normal: $(BUILD_DIR)/db1.ttl
	$(FUSEKI) --localhost --file="$<" \
		$(if $(TIMEOUT),--timeout=$(TIMEOUT),) \
		/name


# Graphs

$(BUILD_DIR)/cct.dot: cct.py
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) vocab --visual $@

$(BUILD_DIR)/cct.ttl: cct.py
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) vocab $@

$(BUILD_DIR)/%/graph0.ttl: scenarios/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) graph --no-passthrough $< $@

$(BUILD_DIR)/%/graph1.ttl: scenarios/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) graph $< $@

$(BUILD_DIR)/%/graph0.dot: scenarios/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) graph --no-passthrough --visual $< $@

$(BUILD_DIR)/%/graph1.dot: scenarios/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) graph --visual $< $@

# Queries

$(BUILD_DIR)/%/query.rq: queries/%.json
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


.PHONY: all graphs queries evaluations server-insular server-normal
