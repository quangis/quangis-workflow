# We run the tests with combinations of these variants:
# -   level 1 (only consider External input and output)
#   / level 2 (consider tools but Opaque internals)
#   / level 3 (Transparent internals)
# -   Chronological / Any order
# -   Passthrough / Blocked
# The test for Passthrough/Blocked and Opaque/Transparent operate on dedicated
# database files: PO/PT/BO/BT. Since order is irrelevant at level 1, we get
# 16-4 different evaluation files: EP/OPC/TPC/OPA/TPA/EB/OBA/TBA/OBC/TBC

BUILD_DIR=testbuild
DEBUG_DIR=build
UTIL=python3 utils/util.py
FUSEKI=build/apache-jena-fuseki-4.3.2/fuseki-server
SERVER=http://localhost:3030
TIMEOUT=60000
SCENARIOS=$(wildcard scenarios/*.ttl)
QUERIES_EVAL=$(wildcard queries/*eval.json)

# graphs: \
# 	$(BUILD_DIR)/cct.ttl \
# 	$(patsubst scenarios/%.ttl,$(BUILD_DIR)/%/graph0.ttl,$(wildcard scenarios/*.ttl))

# $(SCENARIOS:scenarios/%.ttl=$(BUILD_DIR)/%/graphPO.ttl)

evaluations: $(BUILD_DIR)/eval.csv

queries: $(QUERIES_EVAL:queries/%.json=$(BUILD_DIR)/%.rq)

# Serving

$(BUILD_DIR)/db-OP.ttl: $(BUILD_DIR)/cct.ttl $(SCENARIOS:scenarios/%.ttl=$(BUILD_DIR)/%/graph-OP.ttl)
	$(UTIL) merge $@ $^

$(BUILD_DIR)/db-OB.ttl: $(BUILD_DIR)/cct.ttl $(SCENARIOS:scenarios/%.ttl=$(BUILD_DIR)/%/graph-OB.ttl)
	$(UTIL) merge $@ $^

$(BUILD_DIR)/db-TP.ttl: $(BUILD_DIR)/cct.ttl $(SCENARIOS:scenarios/%.ttl=$(BUILD_DIR)/%/graph-TP.ttl)
	$(UTIL) merge $@ $^

$(BUILD_DIR)/db-TB.ttl: $(BUILD_DIR)/cct.ttl $(SCENARIOS:scenarios/%.ttl=$(BUILD_DIR)/%/graph-TB.ttl)
	$(UTIL) merge $@ $^

# Run servers at /db-%
db-%: $(BUILD_DIR)/db-%.ttl
	$(FUSEKI) --localhost --file="$<" $(if $(TIMEOUT),--timeout=$(TIMEOUT),) /$@

.PHONY: db-OP db-TP db-OB db-TB


# Graphs

$(BUILD_DIR)/cct.dot: cct.py
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) vocab --visual $@

$(BUILD_DIR)/cct.ttl: cct.py
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) vocab $@

$(BUILD_DIR)/%/graph-OP.ttl: scenarios/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) graph --passthrough=pass --internals=opaque $< $@

$(BUILD_DIR)/%/graph-TP.ttl: scenarios/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) graph --passthrough=pass --internals=transparent $< $@

$(BUILD_DIR)/%/graph-OB.ttl: scenarios/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) graph --passthrough=block --internals=opaque $< $@

$(BUILD_DIR)/%/graph-TB.ttl: scenarios/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) graph --passthrough=block --internals=transparent $< $@

$(BUILD_DIR)/%/graph.dot: scenarios/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) graph --visual $< $@

# Queries

$(BUILD_DIR)/%/query.rq: queries/%.json
	@mkdir -p $(@D)
	python3 -c 'from cct import cct; from transformation_algebra.query import Query; print(Query.from_file(cct, "$<").sparql())' > $@

$(BUILD_DIR)/eval-EP.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) query -e "$(SERVER)/db-OP" --blackbox $^ -o $@

$(BUILD_DIR)/eval-EB.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) query -e "$(SERVER)/db-OB" --blackbox $^ -o $@

$(BUILD_DIR)/eval-OPC.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) query -e "$(SERVER)/db-OP" $^ -o $@

$(BUILD_DIR)/eval-OPA.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) query -e "$(SERVER)/db-OP" --order=any $^ -o $@

$(BUILD_DIR)/eval-TPC.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) query -e "$(SERVER)/db-TP" $^ -o $@

$(BUILD_DIR)/eval-TPA.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) query -e "$(SERVER)/db-TP" --order=any $^ -o $@

$(BUILD_DIR)/eval-OBC.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) query -e "$(SERVER)/db-OB" $^ -o $@

$(BUILD_DIR)/eval-OBA.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) query -e "$(SERVER)/db-OB" --order=any $^ -o $@

$(BUILD_DIR)/eval-TBC.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) query -e "$(SERVER)/db-TB" $^ -o $@

$(BUILD_DIR)/eval-TBA.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(UTIL) query -e "$(SERVER)/db-TB" --order=any $^ -o $@


# Other

$(BUILD_DIR)/results.tex: $(BUILD_DIR)/results.csv
	@mkdir -p $(@D)
	< $< csvcut -c Variant,Options,Precision,Recall \
		| csvsort | csv2latex > $@


.PHONY: all graphs queries evaluations
