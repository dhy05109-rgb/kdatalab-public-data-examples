.PHONY: check compile python js shell demo clean

PYTHON ?= python3
NODE ?= node

check: compile js shell demo
	@echo "All checks passed."

compile:
	@echo "== Python: compile =="
	@$(PYTHON) -m py_compile python/*.py
	@echo "OK"

js:
	@echo "== JavaScript: syntax =="
	@for file in javascript/*.mjs; do $(NODE) --check "$$file" || exit 1; done
	@echo "OK"

shell:
	@echo "== Shell: syntax =="
	@bash -n curl/quickstart.sh
	@echo "OK"

demo:
	@echo "== Python: --demo and --help =="
	@for file in python/*.py; do \
		case "$$file" in *kdatalab_client.py) continue;; esac; \
		$(PYTHON) "$$file" --help >/dev/null || exit 1; \
		$(PYTHON) "$$file" --demo >/dev/null || exit 1; \
	done
	@echo "OK"
	@echo "== JavaScript: --demo =="
	@for file in javascript/*.mjs; do \
		case "$$file" in *client.mjs) continue;; esac; \
		$(NODE) "$$file" --demo >/dev/null || exit 1; \
	done
	@echo "OK"

clean:
	rm -rf python/__pycache__ out
