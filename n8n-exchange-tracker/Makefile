# ─────────────────────────────────────────
#  n8n Stack - 관리 명령어
#  사용법: make <명령어>
# ─────────────────────────────────────────

.PHONY: up down restart logs ps clean pull help

# 전체 스택 시작
up:
	docker compose up -d
	@echo ""
	@echo "✅ 스택이 시작되었습니다"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  대시보드   → http://localhost"
	@echo "  n8n        → http://localhost:5678"
	@echo "  Grafana    → http://localhost:3000"
	@echo "  Adminer    → http://localhost:8080"
	@echo "  Prometheus → http://localhost:9090"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 전체 스택 중지
down:
	docker compose down

# 재시작
restart:
	docker compose down && docker compose up -d

# 전체 로그 (실시간)
logs:
	docker compose logs -f

# n8n 로그만
logs-n8n:
	docker compose logs -f n8n n8n-worker

# MySQL 로그만
logs-mysql:
	docker compose logs -f mysql

# 컨테이너 상태 확인
ps:
	docker compose ps

# 이미지 최신 버전으로 업데이트
pull:
	docker compose pull
	docker compose up -d

# 데이터 보존하고 컨테이너만 삭제
clean:
	docker compose down --remove-orphans

# 데이터까지 완전 삭제 (주의!)
clean-all:
	@echo "⚠️  모든 데이터가 삭제됩니다. 계속하시겠습니까? (Ctrl+C 취소)"
	@read -p "Enter 키를 눌러 계속: "
	docker compose down -v --remove-orphans

# MySQL 접속
mysql:
	docker exec -it n8n-mysql mysql -uroot -p7345

# Redis 접속
redis:
	docker exec -it n8n-redis redis-cli

# 각 서비스 개별 재시작
restart-n8n:
	docker compose restart n8n n8n-worker

restart-mysql:
	docker compose restart mysql

restart-grafana:
	docker compose restart grafana

# 도움말
help:
	@echo ""
	@echo "사용 가능한 명령어:"
	@echo "  make up           - 전체 스택 시작"
	@echo "  make down         - 전체 스택 중지"
	@echo "  make restart      - 전체 재시작"
	@echo "  make ps           - 컨테이너 상태 확인"
	@echo "  make logs         - 전체 로그 (실시간)"
	@echo "  make logs-n8n     - n8n 로그만"
	@echo "  make logs-mysql   - MySQL 로그만"
	@echo "  make pull         - 이미지 업데이트"
	@echo "  make mysql        - MySQL CLI 접속"
	@echo "  make redis        - Redis CLI 접속"
	@echo "  make clean        - 컨테이너 삭제 (데이터 유지)"
	@echo "  make clean-all    - 전체 삭제 (데이터 포함)"
	@echo ""
