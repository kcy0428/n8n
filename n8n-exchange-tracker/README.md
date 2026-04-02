# 환율 자동화 프로젝트

n8n + MySQL + Grafana를 Docker로 컨테이너화하여 USD→KRW 환율을 자동 수집하고, 매일 아침 이메일로 시간별 리포트를 발송하는 자동화 시스템입니다.

---

## 목차

- [프로젝트 개요](#프로젝트-개요)
- [전체 시스템 흐름](#전체-시스템-흐름)
- [워크플로우 1 — 환율 수집](#워크플로우-1--환율-수집-5분마다)
- [워크플로우 2 — 이메일 발송](#워크플로우-2--이메일-발송-매일-9시)
- [데이터 저장 구조](#데이터-저장-구조)
- [모니터링 흐름](#모니터링-흐름)
- [기능 요약](#기능-요약)
- [접속 정보](#접속-정보)
- [관리 명령어](#관리-명령어)

---

## 프로젝트 개요

```mermaid
mindmap
  root((환율 자동화))
    수집
      5분마다 자동 실행
      open.er-api.com API
      USD to KRW 환율
      MySQL에 저장
    알림
      매일 오전 9시
      시간별 평균 환율
      최고 최저 환율
      Gmail 이메일 발송
    모니터링
      Grafana 대시보드
      실시간 환율 그래프
      수집 현황 확인
      MySQL 데이터 시각화
    인프라
      Docker Compose
      12개 컨테이너
      MySQL 백엔드
      Redis 작업 큐
```

---

## 전체 시스템 흐름

```mermaid
flowchart TD
    API["🌐 환율 API\nopen.er-api.com"]

    subgraph WF1["워크플로우 1 (5분마다)"]
        T1["⏰ Schedule Trigger\n매 5분"]
        H1["🔗 HTTP Request\nUSD→KRW 환율 조회"]
        M1["🐬 MySQL INSERT\n환율 저장"]
    end

    subgraph WF2["워크플로우 2 (매일 9시)"]
        T2["⏰ Schedule Trigger\n오전 9시"]
        M2["🐬 MySQL SELECT\n시간별 집계 쿼리"]
        C1["⚙️ Code Node\nHTML 이메일 생성"]
        E1["📧 Send Email\nGmail SMTP 발송"]
    end

    subgraph Storage["데이터 저장"]
        DB[("MySQL\nexchange_rate 테이블")]
    end

    subgraph Monitoring["모니터링"]
        GRAF["📊 Grafana\n환율 대시보드"]
    end

    GMAIL["📬 Gmail\nkochanyeong123@gmail.com"]

    T1 --> H1 --> API
    API --> H1
    H1 --> M1 --> DB

    T2 --> M2 --> DB
    DB --> M2
    M2 --> C1 --> E1 --> GMAIL

    DB --> GRAF
```

---

## 워크플로우 1 — 환율 수집 (5분마다)

```mermaid
sequenceDiagram
    participant SCH as Schedule Trigger
    participant API as open.er-api.com
    participant N8N as n8n Worker
    participant DB as MySQL

    loop 매 5분마다
        SCH->>N8N: 워크플로우 시작
        N8N->>API: GET /v6/latest/USD
        API-->>N8N: {"rates": {"KRW": 1510.45}}
        N8N->>DB: INSERT INTO exchange_rate (rate) VALUES (1510.45)
        DB-->>N8N: 저장 완료
    end
```

---

## 워크플로우 2 — 이메일 발송 (매일 9시)

```mermaid
sequenceDiagram
    participant SCH as Schedule Trigger
    participant DB as MySQL
    participant CODE as Code Node
    participant SMTP as Gmail SMTP
    participant MAIL as 받은편지함

    SCH->>DB: 오늘 시간별 환율 집계 요청
    Note over DB: SELECT hour, AVG(rate), MAX(rate),\nMIN(rate) GROUP BY HOUR
    DB-->>CODE: 시간별 데이터 반환 (여러 행)
    CODE->>CODE: HTML 이메일 템플릿 생성\n(평균·최고·최저·시간별 테이블)
    CODE->>SMTP: HTML 이메일 전송
    SMTP-->>MAIL: 📈 시간별 환율 리포트 도착
```

---

## 데이터 저장 구조

```mermaid
erDiagram
    exchange_rate {
        INT id PK "AUTO_INCREMENT"
        DECIMAL rate "환율 (KRW)"
        VARCHAR base "기준 통화 (USD)"
        VARCHAR target "대상 통화 (KRW)"
        DATETIME collected_at "수집 시각"
    }
```

**수집 주기**: 5분마다
**보존 기간**: 무제한 (디스크 용량 한도)
**집계 방식**: 시간별 AVG / MAX / MIN

---

## 모니터링 흐름

```mermaid
flowchart LR
    subgraph Collect["수집"]
        N8N["n8n\n워크플로우 실행"]
        MySQL["MySQL\n환율 데이터"]
    end

    subgraph Export["메트릭 수집"]
        NE["Node Exporter\n시스템 리소스"]
        ME["MySQL Exporter\nDB 메트릭"]
        RE["Redis Exporter\n큐 메트릭"]
        CA["cAdvisor\n컨테이너 리소스"]
        N8NM["n8n /metrics\n워크플로우 실행수"]
    end

    subgraph Dashboard["시각화"]
        PROM["Prometheus\n메트릭 저장"]
        GRAF["Grafana\n대시보드"]
    end

    N8N --> N8NM --> PROM
    MySQL --> ME --> PROM
    NE --> PROM
    RE --> PROM
    CA --> PROM
    PROM --> GRAF

    subgraph GrafanaDash["Grafana 대시보드 목록"]
        D1["환율 모니터링\nUSD→KRW 그래프"]
        D2["Node Exporter Full\n시스템 리소스"]
        D3["MySQL Overview\nDB 상태"]
        D4["Docker Containers\n컨테이너 현황"]
        D5["Redis Dashboard\n큐 상태"]
    end

    GRAF --> D1
    GRAF --> D2
    GRAF --> D3
    GRAF --> D4
    GRAF --> D5
```

---

## 기능 요약

```mermaid
timeline
    title 하루 동안의 자동화 흐름
    00시 ~ 24시 : 매 5분마다 환율 수집
                : open.er-api.com API 호출
                : MySQL exchange_rate 테이블 저장
    오전 09시    : 전날 ~ 당일 시간별 환율 집계
                : HTML 이메일 리포트 생성
                : Gmail로 자동 발송
    상시         : Grafana 대시보드 실시간 업데이트
                : Prometheus 메트릭 수집
```

---

## 이메일 리포트 구성

```mermaid
graph TD
    MAIL["📧 시간별 환율 리포트 이메일"]

    MAIL --> S1["📊 오늘 평균 환율"]
    MAIL --> S2["📈 오늘 최고 환율"]
    MAIL --> S3["📉 오늘 최저 환율"]
    MAIL --> T1["🕐 시간별 테이블\n시간 / 평균 / 최고 / 최저 / 수집횟수"]

    S1 & S2 & S3 --> SRC["MySQL\n시간별 집계 데이터"]
    T1 --> SRC
```

---

## 접속 정보

| 서비스 | URL | 계정 | 비밀번호 |
|---|---|---|---|
| 🌐 랜딩 대시보드 | http://localhost:8888 | — | — |
| ⚡ n8n | http://localhost:5678 | — | — |
| 📊 Grafana | http://localhost:3001 | `admin` | `7345` |
| 🗄️ Adminer | http://localhost:8080 | `root` | `7345` |
| 🔥 Prometheus | http://localhost:9090 | — | — |
| 🐬 MySQL | `localhost:3307` | `root` | `7345` |

---

## 관리 명령어

```bash
make up          # 전체 스택 시작
make down        # 전체 스택 중지
make ps          # 컨테이너 상태 확인
make logs        # 전체 로그 (실시간)
make logs-n8n    # n8n 로그만
make logs-mysql  # MySQL 로그만
make mysql       # MySQL CLI 접속
make clean       # 컨테이너 삭제 (데이터 유지)
make clean-all   # 전체 삭제 (데이터 포함, 주의!)
```
