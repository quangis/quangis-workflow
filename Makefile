# We run the tests with combinations of these variants:
# -   level 1 (only consider External input and output)
#   / level 2 (consider tools but Opaque internals)
#   / level 3 (Transparent internals)
# -   Chronological / Any order
# -   Passthrough / Blocked
# The test for Passthrough/Blocked and Opaque/Transparent operate on dedicated
# database files: PO/PT/BO/BT. Since order is irrelevant at level 1, we get
# 16-4 different evaluation files: EB/EP/OPC/TPC/OPA/TPA/OBA/TBA/OBC/TBC

BUILD_DIR=build
DEBUG_DIR=build
TATOOL=python3 utils/ta-tool.py
JENA=build/apache-jena-4.3.2/bin/tdb2.tdbloader
FUSEKI=build/apache-jena-fuseki-4.3.2/fuseki-server
SERVER=http://localhost:3030
TIMEOUT=
WFs=$(wildcard workflows/*.ttl)
QUERIES_EVAL=$(wildcard queries/eval/*.yaml)

# graphs: \
# 	$(BUILD_DIR)/cct.ttl \
# 	$(patsubst scenarios/%.ttl,$(BUILD_DIR)/%/graph0.ttl,$(wildcard scenarios/*.ttl))

# $(SCENARIOS:scenarios/%.ttl=$(BUILD_DIR)/%/graphPO.ttl)

evaluations: $(BUILD_DIR)/eval.csv

queries: $(QUERIES_EVAL:queries/eval/%.yaml=$(BUILD_DIR)/%/eval.rq)

# Serving

.PHONY: tdb-TP
tdb-TP: $(BUILD_DIR)/tdb-TP/marker
	$(FUSEKI) --localhost --loc=$(<D) $(if $(TIMEOUT),--timeout=$(TIMEOUT),) /$@



$(BUILD_DIR)/tdb-TP/marker: $(BUILD_DIR)/cct.ttl $(WFs:workflows/%.ttl=$(BUILD_DIR)/%/graph-TP.ttl)
	mkdir -p $(@D); touch $@
	$(JENA) --loc=$(@D) --loader=phased $^

$(BUILD_DIR)/db-OP.ttl: $(BUILD_DIR)/cct.ttl $(WFs:workflows/%.ttl=$(BUILD_DIR)/%/graph-OP.ttl)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) merge $@ $^

$(BUILD_DIR)/db-OB.ttl: $(BUILD_DIR)/cct.ttl $(WFs:workflows/%.ttl=$(BUILD_DIR)/%/graph-OB.ttl)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) merge $@ $^

$(BUILD_DIR)/db-TP.ttl: $(BUILD_DIR)/cct.ttl $(WFs:workflows/%.ttl=$(BUILD_DIR)/%/graph-TP.ttl)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) merge $@ $^

$(BUILD_DIR)/db-TB.ttl: $(BUILD_DIR)/cct.ttl $(WFs:workflows/%.ttl=$(BUILD_DIR)/%/graph-TB.ttl)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) merge $@ $^

# Run servers at /db-%
db-OP: $(BUILD_DIR)/db-OP.ttl
	$(FUSEKI) --localhost --file="$<" $(if $(TIMEOUT),--timeout=$(TIMEOUT),) /$@

db-OB: $(BUILD_DIR)/db-OB.ttl
	$(FUSEKI) --localhost --file="$<" $(if $(TIMEOUT),--timeout=$(TIMEOUT),) /$@

db-TB: $(BUILD_DIR)/db-TB.ttl
	$(FUSEKI) --localhost --file="$<" $(if $(TIMEOUT),--timeout=$(TIMEOUT),) /$@

db-TP: $(BUILD_DIR)/db-TP.ttl
	$(FUSEKI) --localhost --file="$<" $(if $(TIMEOUT),--timeout=$(TIMEOUT),) /$@

.PHONY: db-OP db-TP db-OB db-TB


# Graphs

$(BUILD_DIR)/cct.dot: cct.py
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) vocab --visual $@

$(BUILD_DIR)/cct.ttl: cct.py
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) vocab $@

$(BUILD_DIR)/%/graph-OP.ttl: workflows/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --passthrough=pass --internal=opaque $< $@

$(BUILD_DIR)/%/graph-TP.ttl: workflows/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --passthrough=pass --internal=transparent $< $@

$(BUILD_DIR)/%/graph-OB.ttl: workflows/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --passthrough=block --internal=opaque $< $@

$(BUILD_DIR)/%/graph-TB.ttl: workflows/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --passthrough=block --internal=transparent $< $@

$(BUILD_DIR)/%/graph.dot: workflows/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --visual --passthrough=block --internal=transparent $< $@

# Queries

$(BUILD_DIR)/%/eval.rq: queries/eval/%.yaml
	@mkdir -p $(@D)
	$(TATOOL) query --blackbox $^ -o $@

$(BUILD_DIR)/eval-EP.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(SERVER)/db-OP" --blackbox $^ -o $@

$(BUILD_DIR)/eval-EB.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(SERVER)/db-OB" --blackbox $^ -o $@

$(BUILD_DIR)/eval-OPC.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(SERVER)/db-OP" $^ -o $@

$(BUILD_DIR)/eval-OPA.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(SERVER)/db-OP" --order=any $^ -o $@

$(BUILD_DIR)/eval-TPC.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(SERVER)/db-TP" $^ -o $@

$(BUILD_DIR)/eval-TPA.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(SERVER)/tdb-TP" --order=any $^ -o $@

$(BUILD_DIR)/eval-OBC.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(SERVER)/db-OB" $^ -o $@

$(BUILD_DIR)/eval-OBA.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(SERVER)/db-OB" --order=any $^ -o $@

$(BUILD_DIR)/eval-TBC.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(SERVER)/db-TB" $^ -o $@

$(BUILD_DIR)/eval-TBA.csv: $(QUERIES_EVAL)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(SERVER)/db-TB" --order=any $^ -o $@


# Other

$(BUILD_DIR)/results.tex: $(BUILD_DIR)/results.csv
	@mkdir -p $(@D)
	< $< csvcut -c Variant,Options,Precision,Recall \
		| csvsort | csv2latex > $@


.PHONY: all graphs queries evaluations
