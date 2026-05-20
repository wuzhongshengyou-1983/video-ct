.PHONY: help install dev dev-api dev-h5 dev-admin dev-consultant build lint clean test \
        seed docker-up docker-down docker-build docker-logs docker-build-h5 docker-build-admin \
        backup restore db-migrate db-init db-seed

help:
	@echo "Video CT · 常用命令"
	@echo "  make install           安装所有前端依赖 + 后端 Python 依赖"
	@echo "  make dev-api           启动后端 (port 8000)"
	@echo "  make dev-h5            启动 H5 (port 5173)"
	@echo "  make dev-admin         启动管理后台 (port 5174)"
	@echo "  make dev-consultant    启动顾问后台 (port 5175)"
	@echo "  make build             构建全部前端"
	@echo "  make lint              全仓 lint"
	@echo "  make test              全仓测试"
	@echo "  make clean             清理构建/缓存"
	@echo ""
	@echo "  make docker-up         启动 Docker Compose (PG/Redis/MinIO)"
	@echo "  make docker-down       停止 Docker Compose"
	@echo "  make docker-build      构建所有 Docker 镜像"
	@echo "  make docker-logs       查看 Docker Compose 日志"
	@echo ""
	@echo "  make db-migrate        运行 Alembic 数据库迁移"
	@echo "  make db-init           初始化数据库 Schema（SQL 文件）"
	@echo "  make db-seed           插入种子数据（产品目录等）"
	@echo "  make backup            备份数据库到 backups/ 目录"
	@echo "  make restore FILE=path 从备份文件恢复数据库"

install:
	pnpm install
	cd services/api && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

dev-api:
	cd services/api && . .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-h5:
	pnpm --filter @video-ct/h5 dev

dev-admin:
	pnpm --filter @video-ct/admin dev

dev-consultant:
	pnpm --filter @video-ct/consultant dev

build:
	pnpm -r build

# ===================== Docker =====================

docker-up:
	docker compose --env-file .env.docker up -d

docker-down:
	docker compose down

docker-build:
	docker build -t video-ct-api:latest -f infra/docker/Dockerfile.api .
	docker build -t video-ct-h5:latest -f infra/docker/Dockerfile.h5 .
	docker build -t video-ct-admin:latest -f infra/docker/Dockerfile.admin .

docker-build-h5:
	docker build -t video-ct-h5:latest -f infra/docker/Dockerfile.h5 .

docker-build-admin:
	docker build -t video-ct-admin:latest -f infra/docker/Dockerfile.admin .

docker-logs:
	docker compose logs -f --tail=100

# ===================== 数据库 =====================

db-migrate:
	cd services/api && . .venv/bin/activate && alembic upgrade head

db-init:
	@echo "初始化数据库 Schema..."
	@PGPASSWORD=$${PGPASSWORD:-video_ct_dev_pwd} psql \
		-h $${PGHOST:-localhost} \
		-p $${PGPORT:-5432} \
		-U $${PGUSER:-video_ct} \
		-d $${PGDATABASE:-video_ct} \
		-f infra/migrations/init_schema.sql

db-seed:
	cd services/api && . .venv/bin/activate && python scripts/seed.py

seed: db-seed

# ===================== 备份恢复 =====================

backup:
	bash scripts/backup-db.sh

restore:
	@if [ -z "$(FILE)" ]; then \
		echo "用法: make restore FILE=backups/video_ct_20260520_120000.dump"; \
		echo ""; \
		ls -lh backups/video_ct_*.dump 2>/dev/null || echo "  (无备份文件)"; \
		exit 1; \
	fi
	bash scripts/restore-db.sh "$(FILE)"

# ===================== Lint / Test / Clean =====================

lint:
	pnpm -r lint
	cd services/api && . .venv/bin/activate && ruff check app/
	cd services/api && . .venv/bin/activate && ruff format --check app/

clean:
	pnpm -r exec rm -rf node_modules dist .turbo
	find . -type d -name __pycache__ -exec rm -rf {} +

test:
	pnpm -r test
	cd services/api && . .venv/bin/activate && pytest
