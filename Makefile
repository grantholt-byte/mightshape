.PHONY: build-openai build-claude build-packages validate-openai validate-claude \
	validate-packages check-cross-platform-drift check-drift platform-evals test \
	benchmark-dry-run benchmark trajectory-benchmark-dry-run trajectory-benchmark \
	release-check clean-dist

build-openai:
	python3 scripts/build_packages.py --platform openai

build-claude:
	python3 scripts/build_packages.py --platform claude

build-packages:
	python3 scripts/build_packages.py --clean --platform all

validate-openai: build-openai
	python3 scripts/validate_packages.py --platform openai

validate-claude: build-claude
	python3 scripts/validate_packages.py --platform claude --require-claude

validate-packages: build-packages
	python3 scripts/validate_packages.py --platform all

check-cross-platform-drift: build-packages
	python3 scripts/check_cross_platform_drift.py

check-drift: check-cross-platform-drift

platform-evals: build-packages
	python3 evals/run_platform_contracts.py

test:
	python3 -m unittest discover -s tests -v
	python3 evals/run_contracts.py
	python3 evals/run_platform_contracts.py

benchmark-dry-run:
	python3 evals/run_ab_benchmark.py --dry-run

benchmark:
	python3 evals/run_ab_benchmark.py --repeats 2 --judge-repetitions 2 --run-model

trajectory-benchmark-dry-run:
	python3 evals/run_trajectory_benchmark.py --dry-run --repeats 2 --judge-repetitions 2

trajectory-benchmark:
	python3 evals/run_trajectory_benchmark.py --run-model --require-model \
		--session-mode persisted --control-mode design-thinking-prompt \
		--repeats 2 --judge-repetitions 2 --judge-model gpt-5.6-terra

release-check:
	python3 scripts/release_check.py

clean-dist:
	python3 scripts/build_packages.py --clean-only
