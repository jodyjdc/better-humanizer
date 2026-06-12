.PHONY: test corpus eval all clean

# Run the test suite (standard library, no pytest needed).
test:
	python3 tests/run.py

# Fetch the human reference corpora and (re)calibrate the bands for every register.
corpus:
	python3 scripts/fetch_corpus.py --register spontaneous
	python3 scripts/fetch_corpus.py --register scientific
	python3 scripts/fetch_corpus.py --register literary --max-chars 3000
	python3 scripts/build_reference.py --register spontaneous
	python3 scripts/build_reference.py --register scientific
	python3 scripts/build_reference.py --register literary

# Run the blind A/B eval for every register.
eval:
	@for r in spontaneous scientific literary; do \
		python3 eval/run_eval.py --register $$r; echo; \
	done

all: test eval

clean:
	rm -rf corpus/*/raw __pycache__ */__pycache__ *.tar.gz
