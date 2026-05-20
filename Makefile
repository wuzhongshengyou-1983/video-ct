.PHONY: help install dev dev-api dev-h5 build lint clean test seed db-up db-down docker-up docker-down

help:
	@echo "Video CT · 常用命令"
	@echo "  make install      安装所有前端依赖 + 后端 Python 依赖"
	@echo "  make dev          同时启动后端 + H5（需 4 个终端跑各端）"
	@echo "  make dev-api      启动后端 (port 8000)"
	@echo "  make dev-h5       启动 H5 (port 5173)"
	@echo "  make dev-admin    启动管理后台 (port 5174)"
	@echo "  make dev-consultant 启动顾问后台 (port 5175)"
	@echo "  make build        构建全部前端"
	@echo "  make seed         初始化数据库基础数据"
	@echo "  make lint         全仓 lint"
	@echo "  make clean        清理构建/缓存"
	@echo "  make docker-up    启动 Docker 依赖（PG/Redis/Milvus）"

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

seed:
	cd services/api && . .venv/bin/activate && python scripts/seed.py

lint:
	pnpm -r lint
	cd services/api && . .venv/bin/activate && ruff check app/

clean:
	pnpm -r exec rm -rf node_modules dist .turbo
	find . -type d -name __pycache__ -exec rm -rf {} +

docker-up:
	docker compose up -d

docker-down:
	docker compose down

test:
	pnpm -r test
	cd services/api && . .venv/bin/activate && pytest
