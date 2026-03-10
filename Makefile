.PHONY: install dev test lint typecheck fmt clean run-discover run-enrich run-export \
	system-ci system-validate check-agents check-skills check-commands check-registry check-refs system-status clean-state

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest --cov=scrapper --cov-report=term-missing

lint:
	ruff check src/ tests/

typecheck:
	mypy src/scrapper/

fmt:
	ruff check --fix src/ tests/
	ruff format src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache *.egg-info

run-discover:
	scrapper discover --source fake

run-enrich:
	scrapper enrich --batch-size 5

run-export:
	scrapper export --format xlsx

run-stats:
	scrapper stats

init-db:
	scrapper init-db

# ============================================================
# Multi-Agent System Infrastructure
# ============================================================

SYSTEM_ROOT := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
AGENTS_DIR := $(SYSTEM_ROOT)/.claude/agents
SKILLS_DIR := $(SYSTEM_ROOT)/.claude/skills
COMMANDS_DIR := $(SYSTEM_ROOT)/.claude/commands
STATE_DIR := $(SYSTEM_ROOT)/.claude/state
REGISTRY := $(SYSTEM_ROOT)/.claude/agents/REGISTRY.json
SCHEMAS_DIR := $(SYSTEM_ROOT)/.claude/schemas
QUALITY_SCRIPTS := $(SYSTEM_ROOT)/.claude/quality/scripts

system-ci: ## Run all system checks in sequence
	@echo "=== Multi-Agent System CI ==="
	@echo ""
	@$(MAKE) --no-print-directory check-agents
	@echo ""
	@$(MAKE) --no-print-directory check-skills
	@echo ""
	@$(MAKE) --no-print-directory check-commands
	@echo ""
	@$(MAKE) --no-print-directory check-registry
	@echo ""
	@$(MAKE) --no-print-directory check-refs
	@echo ""
	@echo "=== All checks passed ==="

system-validate: ## Validate state task artifacts against schemas
	@echo "--- Validating state artifacts ---"
	@count=0; fail=0; \
	for f in $(STATE_DIR)/tasks/*.json; do \
		[ -f "$$f" ] || continue; \
		task_id=$$(basename "$$f" .json); \
		count=$$((count + 1)); \
		if jq empty "$$f" 2>/dev/null; then \
			echo "  PASS  $$task_id"; \
		else \
			echo "  FAIL  $$task_id"; \
			fail=$$((fail + 1)); \
		fi; \
	done; \
	echo ""; \
	echo "Results: $$count passed, $$fail failed"; \
	[ $$fail -eq 0 ]

check-agents: ## Validate all agent .md files have required frontmatter
	@bash $(QUALITY_SCRIPTS)/check-agents.sh

check-skills: ## Validate all skill SKILL.md files
	@bash $(QUALITY_SCRIPTS)/check-skills.sh

check-commands: ## Validate all command .md files
	@bash $(QUALITY_SCRIPTS)/check-commands.sh

check-registry: ## Verify 1:1 match between REGISTRY.json and .claude/agents/*.md
	@echo "--- Checking registry sync ---"
	@registry_names=$$(jq -r '.agents[].name' $(REGISTRY) | sort); \
	file_names=$$(ls $(AGENTS_DIR)/*.md 2>/dev/null | xargs -I{} basename {} .md | sort); \
	registry_only=$$(comm -23 <(echo "$$registry_names") <(echo "$$file_names")); \
	files_only=$$(comm -13 <(echo "$$registry_names") <(echo "$$file_names")); \
	fail=0; \
	if [ -n "$$registry_only" ]; then \
		echo "  FAIL  In registry but no .md file:"; \
		echo "$$registry_only" | sed 's/^/         /'; \
		fail=1; \
	fi; \
	if [ -n "$$files_only" ]; then \
		echo "  FAIL  Has .md file but not in registry:"; \
		echo "$$files_only" | sed 's/^/         /'; \
		fail=1; \
	fi; \
	if [ $$fail -eq 0 ]; then \
		echo "  PASS  Registry and agent files are in sync ($$(echo "$$registry_names" | wc -l | tr -d ' ') agents)"; \
	else \
		exit 1; \
	fi

check-refs: ## Check for broken agent references in commands and agent files
	@bash $(QUALITY_SCRIPTS)/check-refs.sh

system-status: ## Show system counts (agents, skills, commands, state)
	@echo "=== Multi-Agent System Status ==="
	@echo ""
	@echo "Agents:    $$(ls $(AGENTS_DIR)/*.md 2>/dev/null | wc -l | tr -d ' ')"
	@echo "Registry:  $$(jq '.agents | length' $(REGISTRY) 2>/dev/null || echo 0)"
	@echo "Skills:    $$(find $(SKILLS_DIR) -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ')"
	@echo "Commands:  $$(ls $(COMMANDS_DIR)/*.md 2>/dev/null | wc -l | tr -d ' ')"
	@echo "Schemas:   $$(ls $(SCHEMAS_DIR)/*.schema.json 2>/dev/null | wc -l | tr -d ' ')"
	@echo ""
	@echo "State:"
	@for dir in tasks handoffs decisions findings; do \
		count=$$(ls $(STATE_DIR)/$$dir/*.json 2>/dev/null | wc -l | tr -d ' '); \
		echo "  $$dir: $$count"; \
	done

clean-state: ## Remove closed/completed state files (with confirmation)
	@echo "Files that would be removed:"
	@found=0; \
	for dir in tasks handoffs; do \
		for f in $(STATE_DIR)/$$dir/*.json; do \
			[ -f "$$f" ] || continue; \
			status=$$(jq -r '.status // ""' "$$f" 2>/dev/null); \
			if [ "$$status" = "closed" ] || [ "$$status" = "accepted" ] || [ "$$status" = "completed" ]; then \
				echo "  $$f (status: $$status)"; \
				found=$$((found + 1)); \
			fi; \
		done; \
	done; \
	if [ $$found -eq 0 ]; then \
		echo "  (none)"; \
		exit 0; \
	fi; \
	echo ""; \
	read -p "Remove $$found files? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		for dir in tasks handoffs; do \
			for f in $(STATE_DIR)/$$dir/*.json; do \
				[ -f "$$f" ] || continue; \
				status=$$(jq -r '.status // ""' "$$f" 2>/dev/null); \
				if [ "$$status" = "closed" ] || [ "$$status" = "accepted" ] || [ "$$status" = "completed" ]; then \
					rm "$$f"; \
					echo "  Removed: $$f"; \
				fi; \
			done; \
		done; \
	else \
		echo "Cancelled."; \
	fi
