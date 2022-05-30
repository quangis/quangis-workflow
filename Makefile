# We run the tests with combinations of these variants:
# -   level 1 (only consider External input and output)
#   / level 2 (consider tools but Opaque internals)
#   / level 3 (Transparent internals)
# -   Chronological / Any order
# -   Passthrough / Blocked
# The test for Passthrough/Blocked and Opaque/Transparent operate on dedicated
# database files: PO/PT/BO/BT. Since order is irrelevant at level 1, we get
# 16-4 different evaluation files: EB/EP/OPC/TPC/OPA/TPA/OBA/TBA/OBC/TBC
# cf. https://stackoverflow.com/questions/974077/how-can-i-trap-errors-and-interrupts-in-gnu-make

.NOTPARALLEL:

BUILD=build
TATOOL=python3 utils/ta-tool.py
TDBLOADER=build/apache-jena-4.3.2/bin/tdb1.xloader
# TDBLOADER=build/apache-jena-4.3.2/bin/tdb2.tdbloader
FUSEKI=build/apache-jena-fuseki-4.3.2/fuseki-server
SERVER=http://localhost:3030
TIMEOUT=
WORKFLOWS=$(wildcard workflows/*.ttl)
TASKS=$(wildcard tasks/turtle/*.ttl)

graphs: $(WORKFLOWS:workflows/%.ttl=$(BUILD)/%/graph-TB.dot) \
		$(WORKFLOWS:workflows/%.ttl=$(BUILD)/%/graph-TP.dot)

queries: $(TASKS:tasks/%.ttl=$(BUILD)/%/eval.rq)

evaluations: $(patsubst %,$(BUILD)/eval/%.csv, \
	EP EB OBA OPA TBA TPA   \
) # OBC OPC TBC TPC

# Server

$(BUILD)/tdb-%/marker: $(BUILD)/cct.ttl $(subst VARIANT,%,$(WORKFLOWS:workflows/%.ttl=$(BUILD)/%/graph-VARIANT.ttl))
	mkdir -p $(@D)/db
	$(TDBLOADER) --loc=$(@D)/db $^
	touch $@

$(BUILD)/tdb-%/started: $(BUILD)/tdb-%/marker
	$(FUSEKI) --localhost --loc=$(<:%/marker=%)/db \
		$(if $(TIMEOUT),--timeout=$(TIMEOUT),) \
		$(<:$(BUILD)/tdb-%/marker=/%) & echo $$! > $@
	sleep 10

$(BUILD)/tdb-%/stopped:
	kill -9 $(shell cat $(@:%/stopped=%/started))
	rm $(@:%/stopped=%/started)
	sleep 2


# Running queries

$(BUILD)/eval/%C.csv: $(TASKS)
	@rm -f $@; mkdir -p $(@D)
	V=$(@:$(BUILD)/eval/%C.csv=%); \
	$(MAKE) $(BUILD)/tdb-$$V/started; \
	$(TATOOL) query -e "$(SERVER)/$$V" $^ -o $@;\
	$(MAKE) $(BUILD)/tdb-$$V/stopped

$(BUILD)/eval/%A.csv: $(TASKS)
	@rm -f $@; mkdir -p $(@D)
	V=$(@:$(BUILD)/eval/%A.csv=%); \
	$(MAKE) $(BUILD)/tdb-$$V/started; \
	$(TATOOL) query -e "$(SERVER)/$$V" --order=any $^ -o $@;\
	$(MAKE) $(BUILD)/tdb-$$V/stopped

$(BUILD)/eval/EB.csv: $(TASKS)
	@rm -f $@; mkdir -p $(@D)
	V=OB; \
	$(MAKE) $(BUILD)/tdb-$$V/started; \
	$(TATOOL) query -e "$(SERVER)/$$V" --blackbox $^ -o $@;\
	$(MAKE) $(BUILD)/tdb-$$V/stopped

$(BUILD)/eval/EP.csv: $(TASKS)
	@rm -f $@; mkdir -p $(@D)
	V=OP; \
	$(MAKE) $(BUILD)/tdb-$$V/started; \
	$(TATOOL) query -e "$(SERVER)/$$V" --blackbox $^ -o $@;\
	$(MAKE) $(BUILD)/tdb-$$V/stopped


# Vocabulary

$(BUILD)/cct.ttl: cct.py
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) vocab $@


# Transformation graphs for each workflow

$(BUILD)/%/graph-OP.ttl: workflows/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --passthrough=pass --internal=opaque $< $@

$(BUILD)/%/graph-TP.ttl: workflows/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --passthrough=pass --internal=transparent $< $@

$(BUILD)/%/graph-OB.ttl: workflows/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --passthrough=block --internal=opaque $< $@

$(BUILD)/%/graph-TB.ttl: workflows/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --passthrough=block --internal=transparent $< $@


# Visualisation/diagnostics

$(BUILD)/cct.dot: cct.py
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) vocab --visual $@

$(BUILD)/%/graph-TB.dot: workflows/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --visual --passthrough=block --internal=transparent $< $@

$(BUILD)/%/graph-TP.dot: workflows/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --visual --passthrough=pass --internal=transparent $< $@

$(BUILD)/%/eval.rq: tasks/%.ttl
	@mkdir -p $(@D)
	$(TATOOL) query $^ -o $@


# Other

%.pdf: %.dot
	dot -Tpdf $< > $@

$(BUILD)/results.tex: $(BUILD)/results.csv
	@mkdir -p $(@D)
	< $< csvcut -c Variant,Options,Precision,Recall \
		| csvsort | csv2latex > $@


.PHONY: all graphs queries evaluations
