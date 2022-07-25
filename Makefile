# We run the tests with combinations of these variants:
# -   level 1 (only consider External input and output)
#   / level 2 (consider tools but Opaque internals)
#   / level 3 (Transparent internals)
# -   Chronological / Any order
# -   Passthrough / Blocked
# The test for Passthrough/Blocked and Opaque/Transparent operate on dedicated
# database files: PO/PT/BO/BT. Since order is irrelevant at level 1, we get
# 16-4 different evaluation files: EB/EP/OPC/TPC/OPA/TPA/OBA/TBA/OBC/TBC

.NOTPARALLEL:

BUILD=build
TATOOL=contra.py
JENAVERSION=4.5.0
TDBLOADER=build/apache-jena-$(JENAVERSION)/bin/tdb1.xloader
# TDBLOADER=build/apache-jena-4.3.2/bin/tdb2.tdbloader
FUSEKI=build/apache-jena-fuseki-$(JENAVERSION)/fuseki-server
SERVER=http://localhost:3030
TIMEOUT=
WORKFLOWS=$(wildcard workflows/*.ttl)
TASKS=$(wildcard tasks/*.ttl)
TOOLS=tools/tools.ttl
LANG=cct.py

# Workflow graphs and the database should not be removed as intermediate files
.SECONDARY: $(foreach VARIANT,OB OP TB TP,\
	$(BUILD)/tdb-$(VARIANT)/mark \
	$(WORKFLOWS:workflows/%.ttl=$(BUILD)/%/graph-$(VARIANT).ttl)\
)

graphs: $(WORKFLOWS:workflows/%.ttl=$(BUILD)/%/graph.dot)

queries: $(TASKS:tasks/%.ttl=$(BUILD)/%/eval.rq)

eval: eval-ordered eval-unordered
eval-ordered: $(patsubst %,$(BUILD)/eval/%.csv, OBC OPC TBC TPC)
eval-unordered: $(patsubst %,$(BUILD)/eval/%.csv, EP EB OBA OPA TBA TPA)


# Apache Jena

$(TDBLOADER):
	mkdir -p build/; cd build; \
		wget https://archive.apache.org/dist/jena/binaries/apache-jena-$(JENAVERSION).tar.gz; \
		tar -xvf apache-jena-$(JENAVERSION).tar.gz

$(FUSEKI):
	mkdir -p build/; cd build; \
		wget https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-$(JENAVERSION).tar.gz; \
		tar -xvf apache-jena-fuseki-$(JENAVERSION).tar.gz

# Server

$(BUILD)/tdb-%/mark: $(TDBLOADER) $(BUILD)/cct.ttl \
		$(subst VARIANT,%,$(WORKFLOWS:workflows/%.ttl=$(BUILD)/%/graph-VARIANT.ttl))
	mkdir -p $(@D); rm -rf $(@D)/*
	$(TDBLOADER) --loc=$(@D) $(filter %.ttl,$^)
	touch $@


# Running queries

$(BUILD)/eval/%C.csv: $(BUILD)/tdb-%/mark $(FUSEKI) $(TASKS) $(LANG)
	@rm -f $@; mkdir -p $(@D)
	TDB=$(<:$(BUILD)/tdb-%/mark=%); \
	$(FUSEKI) --localhost --loc=$(<:%/mark=%) /$$TDB & PID=$$!; sleep 4; \
	$(TATOOL) query --language=$(LANG) --endpoint "$(SERVER)/$$TDB" --chronological $(filter %.ttl,$^) -o $@;\
	kill -9 $$PID

$(BUILD)/eval/%A.csv: $(BUILD)/tdb-%/mark $(FUSEKI) $(TASKS) $(LANG)
	@rm -f $@; mkdir -p $(@D)
	TDB=$(<:$(BUILD)/tdb-%/mark=%); \
	$(FUSEKI) --localhost --loc=$(<:%/mark=%) /$$TDB & PID=$$!; sleep 4; \
	$(TATOOL) query --language=$(LANG) --endpoint "$(SERVER)/$$TDB" $(filter %.ttl,$^) -o $@;\
	kill -9 $$PID

$(BUILD)/eval/EB.csv: $(BUILD)/tdb-OB/mark $(FUSEKI) $(TASKS) $(LANG)
	@rm -f $@; mkdir -p $(@D)
	TDB=$(<:$(BUILD)/tdb-%/mark=%); \
	$(FUSEKI) --localhost --loc=$(<:%/mark=%) /$$TDB & PID=$$!; sleep 4; \
	$(TATOOL) query --language=$(LANG) --endpoint "$(SERVER)/$$TDB" --blackbox $(filter %.ttl,$^) -o $@;\
	kill -9 $$PID

$(BUILD)/eval/EP.csv: $(BUILD)/tdb-OP/mark $(FUSEKI) $(TASKS) $(LANG)
	@rm -f $@; mkdir -p $(@D)
	TDB=$(<:$(BUILD)/tdb-%/mark=%); \
	$(FUSEKI) --localhost --loc=$(<:%/mark=%) /$$TDB & PID=$$!; sleep 4; \
	$(TATOOL) query --language=$(LANG) --endpoint "$(SERVER)/$$TDB" --blackbox $(filter %.ttl,$^) -o $@;\
	kill -9 $$PID


# Vocabulary

$(BUILD)/cct.ttl: $(LANG)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) vocab --language=$(LANG) $@

$(BUILD)/cct.json: $(LANG)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) vocab --language=$(LANG) --to=json-ld $@

# Transformation graphs for each workflow

$(BUILD)/%/graph-TP.ttl: workflows/%.ttl $(TOOLS) $(LANG)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --language=$(LANG) --tools=$(TOOLS) $< $@

$(BUILD)/%/graph-OP.ttl: workflows/%.ttl $(TOOLS) $(LANG)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --language=$(LANG) --tools=$(TOOLS) --opaque $< $@

$(BUILD)/%/graph-TB.ttl: workflows/%.ttl $(TOOLS) $(LANG)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --language=$(LANG) --tools=$(TOOLS) --blocked $< $@

$(BUILD)/%/graph-OB.ttl: workflows/%.ttl $(TOOLS) $(LANG)
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --language=$(LANG) --tools=$(TOOLS) --blocked --opaque $< $@

$(BUILD)/everything.ttl: $(BUILD)/cct.ttl $(WORKFLOWS:workflows/%.ttl=$(BUILD)/%/graph-TP.ttl)
	$(TATOOL) merge $@ $^

# Visualisation/diagnostics

$(BUILD)/cct.dot: cct.py
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) vocab --language=$(LANG) --to=dot $@

$(BUILD)/%/graph.dot: workflows/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) graph --language=$(LANG) --tools=$(TOOLS) --to=dot $< $@

$(BUILD)/%/eval.rq: tasks/%.ttl
	@rm -f $@; mkdir -p $(@D)
	$(TATOOL) query --language=$(LANG) --to=sparql $^ -o $@


# Other

%.pdf: %.dot
	dot -Tpdf $< > $@

$(BUILD)/results.tex: $(BUILD)/results.csv
	@mkdir -p $(@D)
	< $< csvcut -c Variant,Options,Precision,Recall \
		| csvsort | csv2latex > $@


.PHONY: all graphs queries eval eval-ordered eval-unordered
