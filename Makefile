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
JENA=build/apache-jena-4.3.2/bin/tdb2.tdbloader
FUSEKI=build/apache-jena-fuseki-4.3.2/fuseki-server
SERVER=http://localhost:3030
TIMEOUT=
WFs=$(wildcard workflows/*.ttl)
TASKS=$(wildcard tasks/*.yaml)

graphs: $(TASKS:workflows/%.ttl=$(BUILD)/%/graph.pdf)

evaluations: $(patsubst %,$(BUILD)/eval/%.csv, \
	EP EB OPC OPA TPC TPA OBC OBA TBC TBA \
)

queries: $(TASKS:tasks/%.yaml=$(BUILD)/%/eval.rq)

# Server

$(BUILD)/tdb-%/marker: $(BUILD)/cct.ttl $(subst VARIANT,%,$(WFs:workflows/%.ttl=$(BUILD)/%/graph-VARIANT.ttl))
	mkdir -p $(@D); touch $@
	$(JENA) --loc=$(@D) --loader=phased $^

$(BUILD)/tdb-%/started: $(BUILD)/tdb-%/marker
	$(FUSEKI) --localhost --loc=$(<:%/marker=%) \
		$(if $(TIMEOUT),--timeout=$(TIMEOUT),) \
		$(<:$(BUILD)/tdb-%/marker=/%) & echo $$! > $@
	sleep 10

$(BUILD)/tdb-%/stopped:
	kill -9 $(shell cat $(@:%/stopped=%/started))
	rm $(@:%/stopped=%/started)


# Running queries

$(BUILD)/eval/%C.csv: $(BUILD)/tdb-%/started $(TASKS)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(<:$(BUILD)/tdb-%/started=$(SERVER)/%)" $(filter-out %/started,$^) -o $@; $(MAKE) $(<:%/started=%/stopped)

$(BUILD)/eval/%A.csv: $(BUILD)/tdb-%/started $(TASKS)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(<:$(BUILD)/tdb-%/started=$(SERVER)/%)" --order=any $(filter-out %/started,$^) -o $@; $(MAKE) $(<:%/started=%/stopped)

$(BUILD)/eval/EB.csv: $(BUILD)/tdb-OB/started $(TASKS)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(<:$(BUILD)/tdb-%/started=$(SERVER)/%)" --blackbox $(filter-out %/started,$^) -o $@; $(MAKE) $(<:%/started=%/stopped)

$(BUILD)/eval/EP.csv: $(BUILD)/tdb-OP/started $(TASKS)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query -e "$(<:$(BUILD)/tdb-%/started=$(SERVER)/%)" --blackbox $(filter-out %/started,$^) -o $@; $(MAKE) $(<:%/started=%/stopped)


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

$(BUILD)/%/graph.dot: workflows/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --visual --passthrough=block --internal=transparent $< $@

$(BUILD)/%/eval.rq: tasks/%.yaml
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
