# 🌤️ n8n 자동 데이터 수집 + 분석 + 시각화 시스템

> n8n으로 5분마다 날씨 데이터를 자동 수집하고, MariaDB에 저장하며, Flask API로 조회하고, Grafana로 실시간 시각화하는 통합 모니터링 시스템

---

## 📋 목차

1. [시스템 아키텍처](#시스템-아키텍처)
2. [프로젝트 폴더 구조](#프로젝트-폴더-구조)
3. [기술 스택](#기술-스택)
4. [실행 방법](#실행-방법)
5. [n8n 워크플로우 설정](#n8n-워크플로우-설정)
6. [Flask API 사용법](#flask-api-사용법)
7. [Grafana 대시보드 설정](#grafana-대시보드-설정)
8. [트러블슈팅](#트러블슈팅)

---

## 🏗️ 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                     │
│                                                              │
│  ┌─────────────┐     ┌──────────────┐     ┌──────────────┐  │
│  │  Open-Meteo  │────▶│     n8n      │────▶│   MariaDB    │  │
│  │  (외부 API)  │     │  :5678       │     │   :3306      │  │
│  └─────────────┘     │              │     │              │  │
│                      │  5분 스케줄   │     │ sensor_data  │  │
│                      │  데이터 파싱  │     │ alert_log    │  │
│                      │  임계값 체크  │     │              │  │
│                      └──────────────┘     └──────┬───────┘  │
│                                                  │           │
│                                    ┌─────────────┼─────┐    │
│                                    │             │     │    │
│                              ┌─────▼──────┐ ┌───▼─────▼┐   │
│                              │  Flask API  │ │ Grafana   │   │
│                              │  :5000      │ │ :3000     │   │
│                              │             │ │           │   │
│                              │ /data       │ │ 실시간    │   │
│                              │ /alerts     │ │ 대시보드  │   │
│                              │ /stats      │ │           │   │
│                              └─────────────┘ └───────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 데이터 흐름

1. **n8n**이 5분마다 Open-Meteo API에서 서울 날씨 데이터(온도, 습도, 풍속) 수집
2. 수집된 데이터를 **MariaDB**의 `sensor_data` 테이블에 저장
3. 온도가 30°C 초과 시 `alert_log` 테이블에 경고 기록
4. **Flask API**를 통해 REST API로 데이터 조회 가능
5. **Grafana**에서 MariaDB 직접 연결하여 실시간 대시보드 표시

---

## 📁 프로젝트 폴더 구조

```
middle_test/
├── .env                          # 환경변수 (DB 비밀번호, 설정값)
├── docker-compose.yml            # Docker 서비스 오케스트레이션
├── README.md                     # 이 파일
│
├── flask-api/                    # Flask REST API 서버
│   ├── Dockerfile                # Flask 앱 빌드 설정
│   ├── requirements.txt          # Python 패키지 목록
│   └── app.py                    # Flask 메인 애플리케이션
│
├── mariadb/                      # MariaDB 설정
│   └── init.sql                  # 테이블 생성 + 초기 데이터
│
├── n8n/                          # n8n 워크플로우
│   └── workflow.json             # 임포트 가능한 워크플로우 파일
│
└── grafana/                      # Grafana 설정
    └── provisioning/
        ├── datasources/
        │   └── datasource.yml    # MariaDB 데이터소스 자동 등록
        └── dashboards/
            ├── dashboard.yml     # 대시보드 프로비저닝 설정
            └── monitoring-dashboard.json  # 대시보드 레이아웃
```

---

## 🛠️ 기술 스택

| 서비스 | 기술 | 포트 | 용도 |
|--------|------|------|------|
| 워크플로우 | n8n | 5678 | 데이터 수집 자동화 |
| 데이터베이스 | MariaDB 10.11 | 3306 | 데이터 저장소 |
| API 서버 | Flask (Python 3.11) | 5000 | REST API |
| 시각화 | Grafana | 3000 | 실시간 대시보드 |
| 컨테이너 | Docker Compose | - | 서비스 관리 |

---

## 🚀 실행 방법

### 사전 요구사항

- Docker 설치 완료
- Docker Compose 설치 완료
- 인터넷 연결 (Open-Meteo API 접근용)

### Step 1: 프로젝트 디렉토리 이동

```bash
cd /home/chan/Desktop/middle_test
```

### Step 2: Docker Compose 실행

```bash
docker compose up -d --build
```

### Step 3: 서비스 상태 확인

```bash
docker compose ps
```

모든 서비스가 `Up (healthy)` 상태인지 확인합니다.

### Step 4: 각 서비스 접속 확인

| 서비스 | URL | 계정 |
|--------|-----|------|
| n8n | http://localhost:5678 | 최초 접속 시 계정 생성 |
| Flask API | http://localhost:5000 | 인증 없음 |
| Grafana | http://localhost:3000 | admin / admin1234 |

### Step 5: 서비스 중지

```bash
docker compose down
```

데이터를 완전히 삭제하려면:
```bash
docker compose down -v
```

---

## ⚙️ n8n 워크플로우 설정

### 워크플로우 전체 흐름

```
[5분마다 실행] → [날씨 API 호출] → [데이터 파싱] → [DB에 데이터 저장]
                                        ↓
                               [온도 30°C 초과 확인]
                                   ↙        ↘
                           [Alert 기록]  [완료 (Alert 없음)]
```

### Step 1: n8n 접속 및 초기 설정

1. http://localhost:5678 접속
2. 최초 접속 시 Owner 계정 생성 (이메일, 비밀번호 입력)

### Step 2: MySQL 자격증명(Credential) 생성

**⚠️ 이 단계가 가장 중요합니다! 워크플로우 임포트 전에 반드시 먼저 수행하세요.**

1. 좌측 메뉴에서 **Credentials** 클릭
2. **Add Credential** 클릭
3. **MySQL** 검색 후 선택
4. 다음 정보 입력:

| 항목 | 값 |
|------|-----|
| Credential Name | `MariaDB Monitoring` |
| Host | `mariadb` |
| Port | `3306` |
| Database | `monitoring_db` |
| User | `monitor` |
| Password | `monitor1234` |

5. **Save** 클릭

### Step 3: 워크플로우 임포트

1. n8n 대시보드에서 **Add Workflow** 클릭
2. 우측 상단 **⋮** (점 3개 메뉴) → **Import from File** 클릭
3. `n8n/workflow.json` 파일 선택
4. 임포트 완료

### Step 4: 자격증명 연결

임포트 후 MySQL 노드에 자격증명을 연결해야 합니다:

1. **"DB에 데이터 저장"** 노드 더블클릭
2. Credential 드롭다운에서 **MariaDB Monitoring** 선택
3. **"Alert 기록"** 노드도 동일하게 연결
4. **Save** 클릭

### Step 5: 워크플로우 활성화

1. 우측 상단 **Active** 토글 ON
2. 워크플로우가 5분마다 자동 실행됩니다

### Step 6: 수동 테스트

- **Test Workflow** 버튼을 클릭하여 즉시 실행 가능
- 각 노드 클릭 시 실행 결과 확인 가능

---

### 각 노드 상세 설명

#### 노드 1: 5분마다 실행 (Schedule Trigger)
- **타입**: Schedule Trigger
- **설정**: 5분 간격
- **역할**: 워크플로우 트리거

#### 노드 2: 날씨 API 호출 (HTTP Request)
- **타입**: HTTP Request
- **URL**: `https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.978&current=temperature_2m,relative_humidity_2m,wind_speed_10m`
- **역할**: Open-Meteo API에서 서울 현재 날씨 데이터 가져오기

#### 노드 3: 데이터 파싱 (Code)
- **타입**: Code (JavaScript)
- **역할**: API 응답 파싱 및 DB 저장 형식으로 변환

```javascript
// Open-Meteo API 응답에서 데이터 파싱
const response = $input.first().json;
const current = response.current;

const temperature = current.temperature_2m;
const humidity = current.relative_humidity_2m;
const windSpeed = current.wind_speed_10m;

// MySQL DATETIME 형식으로 변환
const now = new Date();
const collectedAt = now.getFullYear() + '-' + 
  String(now.getMonth() + 1).padStart(2, '0') + '-' + 
  String(now.getDate()).padStart(2, '0') + ' ' + 
  String(now.getHours()).padStart(2, '0') + ':' + 
  String(now.getMinutes()).padStart(2, '0') + ':' + 
  String(now.getSeconds()).padStart(2, '0');

return [{
  json: {
    temperature: temperature,
    humidity: humidity,
    wind_speed: windSpeed,
    source: 'open-meteo-seoul',
    collected_at: collectedAt
  }
}];
```

#### 노드 4: DB에 데이터 저장 (MySQL)
- **타입**: MySQL
- **동작**: Execute Query

```sql
INSERT INTO sensor_data (temperature, humidity, wind_speed, source, collected_at) 
VALUES ({{ $json.temperature }}, {{ $json.humidity }}, {{ $json.wind_speed }}, '{{ $json.source }}', '{{ $json.collected_at }}')
```

#### 노드 5: 온도 30°C 초과 확인 (IF)
- **타입**: IF
- **조건**: `{{ $json.temperature }}` > 30
- **True 출력**: Alert 기록 노드로 연결
- **False 출력**: 완료 (NoOp) 노드로 연결

#### 노드 6: Alert 기록 (MySQL)
- **타입**: MySQL
- **동작**: Execute Query

```sql
INSERT INTO alert_log (metric_name, metric_value, threshold, message) 
VALUES ('temperature', {{ $json.temperature }}, 30, '온도 임계값 초과: {{ $json.temperature }}°C (기준: 30°C)')
```

### ⚠️ 워크플로우를 UI에서 직접 만들 경우

JSON 임포트가 안 될 경우, 위 노드 설명을 따라 직접 만들 수 있습니다:

1. **Schedule Trigger** 노드 추가 → 5분 간격 설정
2. **HTTP Request** 노드 추가 → URL 입력
3. **Code** 노드 추가 → JavaScript 코드 붙여넣기
4. **MySQL** 노드 추가 → INSERT 쿼리 입력
5. **IF** 노드 추가 → 온도 > 30 조건
6. **MySQL** 노드 추가 → Alert INSERT 쿼리
7. 노드 간 연결선 드래그

---

## 📡 Flask API 사용법

### 엔드포인트 목록

#### `GET /` - API 정보
```bash
curl http://localhost:5000/
```

#### `GET /data` - 센서 데이터 조회
```bash
# 기본 (최신 100건)
curl http://localhost:5000/data

# 건수 제한
curl http://localhost:5000/data?limit=10

# 페이지네이션
curl http://localhost:5000/data?limit=10&offset=20

# 날짜 필터
curl "http://localhost:5000/data?start=2026-04-23 00:00:00&end=2026-04-23 23:59:59"
```

**응답 예시:**
```json
{
  "status": "success",
  "total": 150,
  "count": 10,
  "limit": 10,
  "offset": 0,
  "data": [
    {
      "id": 150,
      "temperature": 25.3,
      "humidity": 62.0,
      "wind_speed": 14.2,
      "source": "open-meteo-seoul",
      "collected_at": "2026-04-23 16:45:00"
    }
  ]
}
```

#### `GET /data/latest` - 최신 데이터 1건
```bash
curl http://localhost:5000/data/latest
```

#### `GET /alerts` - 알림 로그 조회
```bash
curl http://localhost:5000/alerts
curl http://localhost:5000/alerts?limit=5
```

#### `GET /stats` - 통계
```bash
curl http://localhost:5000/stats
```

**응답 예시:**
```json
{
  "status": "success",
  "data": {
    "total_records": 150,
    "avg_temperature": 24.56,
    "max_temperature": 35.2,
    "min_temperature": 18.1,
    "avg_humidity": 58.3,
    "avg_wind_speed": 12.7,
    "alert_count": 12,
    "first_record": "2026-04-23 10:00:00",
    "last_record": "2026-04-23 16:45:00"
  }
}
```

#### `GET /health` - 상태 확인
```bash
curl http://localhost:5000/health
```

---

## 📊 Grafana 대시보드 설정

### 자동 프로비저닝 (이미 설정됨)

Docker Compose 실행 시 다음이 자동으로 설정됩니다:
- ✅ MariaDB 데이터소스 연결
- ✅ 모니터링 대시보드 생성

### 대시보드 접속

1. http://localhost:3000 접속
2. 로그인: `admin` / `admin1234`
3. 좌측 메뉴 → **Dashboards** → **Monitoring** 폴더
4. **🌤️ 날씨 모니터링 대시보드** 클릭

### 대시보드 구성 (9개 패널)

| 패널 | 타입 | 설명 |
|------|------|------|
| 📊 현재 온도 | Stat | 최신 온도 (색상: 파랑→초록→노랑→빨강) |
| 💧 현재 습도 | Stat | 최신 습도 |
| 🌬️ 현재 풍속 | Stat | 최신 풍속 |
| 🚨 총 Alert 건수 | Stat | 전체 알림 건수 |
| 🌡️ 온도 변화 추이 | Time Series | 온도 시계열 그래프 (30°C 임계선 표시) |
| 💧 습도 변화 추이 | Time Series | 습도 시계열 그래프 |
| 🌬️ 풍속 변화 추이 | Time Series | 풍속 막대 그래프 |
| 📊 전체 종합 | Time Series | 온도+습도+풍속 통합 그래프 |
| 🚨 최근 Alert 로그 | Table | 알림 이력 테이블 |

### 수동으로 데이터소스 추가하기 (자동 프로비저닝 실패 시)

1. Grafana 접속 → 좌측 메뉴 → **Connections** → **Data sources**
2. **Add data source** 클릭
3. **MySQL** 선택
4. 설정 입력:

| 항목 | 값 |
|------|-----|
| Host | `mariadb:3306` |
| Database | `monitoring_db` |
| User | `monitor` |
| Password | `monitor1234` |

5. **Save & Test** 클릭

### 수동으로 대시보드 만들기 (자동 프로비저닝 실패 시)

1. **Dashboards** → **New Dashboard** → **Add visualization**
2. 데이터소스: **MariaDB** 선택
3. 쿼리 입력 예시:

**온도 시계열:**
```sql
SELECT 
  collected_at AS time, 
  temperature AS '온도' 
FROM sensor_data 
WHERE $__timeFilter(collected_at) 
ORDER BY collected_at
```

**Alert 로그 테이블:**
```sql
SELECT 
  metric_name AS '측정항목',
  metric_value AS '측정값',
  threshold AS '임계값',
  message AS '메시지',
  alerted_at AS '발생시각'
FROM alert_log 
ORDER BY alerted_at DESC 
LIMIT 50
```

---

## 🔧 트러블슈팅

### 1. Docker 권한 오류

```
permission denied while trying to connect to the Docker daemon socket
```

**해결:**
```bash
sudo usermod -aG docker $USER
# 로그아웃 후 다시 로그인
```

### 2. MariaDB 연결 실패

```
Can't connect to MySQL server on 'mariadb'
```

**원인:** MariaDB가 아직 시작되지 않았을 수 있음

**해결:**
```bash
# MariaDB 상태 확인
docker compose logs mariadb

# 컨테이너 재시작
docker compose restart mariadb
```

### 3. 포트 충돌

```
bind: address already in use
```

**해결:** 사용 중인 포트 확인 후 프로세스 종료
```bash
# 어떤 프로세스가 포트를 사용하는지 확인
sudo lsof -i :3306
sudo lsof -i :5000
sudo lsof -i :3000
sudo lsof -i :5678
```

또는 `.env` 파일과 `docker-compose.yml`에서 포트 번호 변경

### 4. n8n 워크플로우 임포트 실패

**해결:** 위 [n8n 워크플로우 설정](#n8n-워크플로우-설정) 섹션의 "UI에서 직접 만들기" 참고

### 5. Grafana 대시보드가 보이지 않음

```bash
# Grafana 로그 확인
docker compose logs grafana

# 프로비저닝 파일 권한 확인
ls -la grafana/provisioning/
```

**해결:** Grafana 컨테이너 재시작
```bash
docker compose restart grafana
```

### 6. 데이터가 수집되지 않음

1. n8n에서 워크플로우가 **Active** 상태인지 확인
2. n8n 워크플로우 실행 이력 확인 (좌측 메뉴 → Executions)
3. 네트워크 연결 확인 (Open-Meteo API 접근 가능한지)

```bash
# 컨테이너 내부에서 API 테스트
docker exec middle_n8n wget -qO- "https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.978&current=temperature_2m"
```

### 7. 전체 초기화 (완전 재설정)

```bash
docker compose down -v
docker compose up -d --build
```

---

## 📊 MariaDB 테이블 구조

### sensor_data (센서 데이터)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT (PK, AUTO_INCREMENT) | 고유 식별자 |
| temperature | FLOAT | 온도 (°C) |
| humidity | FLOAT | 습도 (%) |
| wind_speed | FLOAT | 풍속 (km/h) |
| source | VARCHAR(100) | 데이터 출처 |
| collected_at | DATETIME | 수집 시각 |

### alert_log (알림 로그)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT (PK, AUTO_INCREMENT) | 고유 식별자 |
| metric_name | VARCHAR(100) | 측정 항목명 |
| metric_value | FLOAT | 측정값 |
| threshold | FLOAT | 임계값 |
| message | TEXT | 알림 메시지 |
| alerted_at | DATETIME | 알림 발생 시각 |

---

## 🔐 기본 계정 정보

| 서비스 | 사용자 | 비밀번호 | 비고 |
|--------|--------|----------|------|
| MariaDB (root) | root | root1234 | 관리용 |
| MariaDB (앱) | monitor | monitor1234 | 앱 전용 |
| Grafana | admin | admin1234 | 웹 UI 접속 |
| n8n | - | - | 최초 접속 시 생성 |

> ⚠️ **프로덕션 환경에서는 `.env` 파일의 비밀번호를 반드시 변경하세요!**

---

## 📜 라이선스

이 프로젝트는 학습 및 테스트 목적으로 작성되었습니다.
