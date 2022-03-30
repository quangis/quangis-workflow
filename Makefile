BUILD_DIR=testbuild
DEBUG_DIR=build

all: $(BUILD_DIR)/eval.csv

queries: $(patsubst queries/%.json,$(BUILD_DIR)/%.rq,$(wildcard queries/*.json))

.PHONY: queries

# $(BUILD_DIR)/eval_results.csv: $(wildcard $(QUERY_DIR)/eval_*.json)
# 	util/query.py run $^ -o $@

# $(DEBUG_DIR)/%.debug.csv: $(QUERY_DIR)/%.json | $(@D)
# 	util/query.py debug $< $@

$(BUILD_DIR)/%.rq: queries/%.json
	mkdir -p $(@D)
	python3 -c 'from cct import cct; from transformation_algebra.query import Query; print(Query.from_file(cct, "$<").sparql())' > $@

$(BUILD_DIR)/eval.csv: $(wildcard queries/*_eval.json)
	rm -f $@
	mkdir -p $(@D)
	python3 utils/util.py query $^ -o $@

$(BUILD_DIR)/results.tex: $(BUILD_DIR)/results.csv
	mkdir -p $(@D)
	< $< csvcut -c Variant,Options,Precision,Recall \
		| csvsort | csv2latex > $@
