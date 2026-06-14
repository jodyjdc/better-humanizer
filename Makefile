.PHONY: test corpus eval all clean

# Run the test suite (standard library, no pytest needed).
test:
	python3 tests/run.py

# Fetch the human reference corpora and (re)calibrate the bands for every register.
corpus:
	python3 scripts/fetch_corpus.py --register spontaneous
	python3 scripts/fetch_corpus.py --register scientific
	python3 scripts/fetch_corpus.py --register literary --max-chars 3000
	python3 scripts/fetch_corpus.py --register business --min-chars 200 --max-chars 2400 --min-sents 3
	python3 scripts/fetch_corpus.py --register journalism --min-chars 800 --max-chars 4500 --min-sents 6
	python3 scripts/fetch_corpus.py --register social-media --min-chars 250 --max-chars 2400 --min-sents 2
	python3 scripts/fetch_corpus.py --register technical-docs --min-chars 300 --max-chars 3000 --min-sents 4
	python3 scripts/build_reference.py --register spontaneous
	python3 scripts/build_reference.py --register scientific
	python3 scripts/build_reference.py --register literary
	python3 scripts/build_reference.py --register business
	python3 scripts/build_reference.py --register journalism
	python3 scripts/build_reference.py --register social-media
	python3 scripts/build_reference.py --register technical-docs

# Run the blind A/B eval for every register.
eval:
	@for r in spontaneous scientific literary business journalism social-media technical-docs; do \
		python3 eval/run_eval.py --register $$r; echo; \
	done

all: test eval

clean:
	rm -rf corpus/*/raw __pycache__ */__pycache__ *.tar.gz
