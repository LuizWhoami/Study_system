PYTHON = venv/bin/python
MANAGE = $(PYTHON) manage.py
DATE   = $(shell date +%Y%m%d-%H%M%S)

.PHONY: help run migrate makemigrations shell test check collect backup-db clean-backups

help:
	@echo "Comandos:"
	@echo "  make run             - Servidor em 0.0.0.0:8000"
	@echo "  make migrate         - Aplica migrações"
	@echo "  make makemigrations  - Gera migrações"
	@echo "  make shell           - Shell do Django"
	@echo "  make test            - Roda testes"
	@echo "  make check           - django check"
	@echo "  make collect         - collectstatic"
	@echo "  make backup-db       - Copia db.sqlite3"
	@echo "  make clean-backups   - Remove *.bak-* etc"

run:
	$(MANAGE) runserver 0.0.0.0:8000

migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations

shell:
	$(MANAGE) shell

test:
	$(MANAGE) test

check:
	$(MANAGE) check

collect:
	$(MANAGE) collectstatic --noinput

backup-db:
	@cp db.sqlite3 db.bak-$(DATE)
	@echo "Backup criado: db.bak-$(DATE)"

clean-backups:
	@find . -type f \\( -name "*.bak-*" -o -name "*.removed-*" -o -name "*.pre-*" \\) \\
	    -not -path "./venv/*" -not -path "./.git/*" -delete -print
