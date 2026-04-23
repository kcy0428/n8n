"""
Flask API Server - 모니터링 데이터 조회 API
==============================================
- /data       : 센서 데이터 조회
- /alerts     : 알림 로그 조회
- /stats      : 통계 데이터 조회
- /health     : 서버 상태 확인
"""

from flask import Flask, jsonify, request
from datetime import datetime
from decimal import Decimal
import pymysql
import os
import time
import logging

# ============================================
# Flask 앱 설정
# ============================================
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 한글 지원

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================
# 데이터베이스 연결
# ============================================
def get_db():
    """MariaDB 연결을 반환합니다."""
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'mariadb'),
        user=os.getenv('DB_USER', 'monitor'),
        password=os.getenv('DB_PASSWORD', 'monitor1234'),
        database=os.getenv('DB_NAME', 'monitoring_db'),
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )


def wait_for_db(max_retries=30, delay=2):
    """데이터베이스가 준비될 때까지 대기합니다."""
    for i in range(max_retries):
        try:
            conn = get_db()
            conn.close()
            logger.info("✅ 데이터베이스 연결 성공!")
            return True
        except Exception as e:
            logger.warning(f"⏳ 데이터베이스 대기 중... ({i+1}/{max_retries}) - {e}")
            time.sleep(delay)
    raise Exception("❌ 데이터베이스 연결 실패!")


def serialize_row(row):
    """행 데이터의 datetime, Decimal 객체를 JSON 직렬화 가능한 형태로 변환합니다."""
    result = {}
    for key, value in row.items():
        if isinstance(value, datetime):
            result[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, Decimal):
            result[key] = float(value)
        else:
            result[key] = value
    return result


# ============================================
# API 엔드포인트
# ============================================

@app.route('/')
def index():
    """API 루트 - 사용 가능한 엔드포인트 목록을 반환합니다."""
    return jsonify({
        "service": "Monitoring Data API",
        "version": "1.0.0",
        "endpoints": {
            "GET /data": "센서 데이터 조회 (쿼리 파라미터: limit, offset)",
            "GET /data/latest": "최신 센서 데이터 1건 조회",
            "GET /alerts": "알림 로그 조회 (쿼리 파라미터: limit)",
            "GET /stats": "통계 데이터 조회",
            "GET /health": "서버 상태 확인"
        }
    })


@app.route('/data', methods=['GET'])
def get_data():
    """
    센서 데이터를 조회합니다.
    
    Query Parameters:
        - limit (int): 조회할 최대 건수 (기본값: 100)
        - offset (int): 시작 위치 (기본값: 0)
        - start (str): 시작 시각 (예: 2026-04-23 00:00:00)
        - end (str): 종료 시각 (예: 2026-04-23 23:59:59)
    """
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    start = request.args.get('start', None)
    end = request.args.get('end', None)

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM sensor_data"
            params = []

            # 날짜 필터링
            conditions = []
            if start:
                conditions.append("collected_at >= %s")
                params.append(start)
            if end:
                conditions.append("collected_at <= %s")
                params.append(end)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY collected_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            data = cursor.fetchall()
            data = [serialize_row(row) for row in data]

            # 전체 건수 조회
            count_query = "SELECT COUNT(*) as total FROM sensor_data"
            if conditions:
                count_query += " WHERE " + " AND ".join(conditions)
            cursor.execute(count_query, params[:-2] if conditions else [])
            total = cursor.fetchone()['total']

        return jsonify({
            "status": "success",
            "total": total,
            "count": len(data),
            "limit": limit,
            "offset": offset,
            "data": data
        })
    except Exception as e:
        logger.error(f"데이터 조회 오류: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()


@app.route('/data/latest', methods=['GET'])
def get_latest_data():
    """최신 센서 데이터 1건을 조회합니다."""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM sensor_data ORDER BY collected_at DESC LIMIT 1")
            data = cursor.fetchone()
            if data:
                data = serialize_row(data)
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        logger.error(f"최신 데이터 조회 오류: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()


@app.route('/alerts', methods=['GET'])
def get_alerts():
    """
    알림 로그를 조회합니다.
    
    Query Parameters:
        - limit (int): 조회할 최대 건수 (기본값: 100)
    """
    limit = request.args.get('limit', 100, type=int)
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM alert_log ORDER BY alerted_at DESC LIMIT %s",
                (limit,)
            )
            data = cursor.fetchall()
            data = [serialize_row(row) for row in data]

            cursor.execute("SELECT COUNT(*) as total FROM alert_log")
            total = cursor.fetchone()['total']

        return jsonify({
            "status": "success",
            "total": total,
            "count": len(data),
            "data": data
        })
    except Exception as e:
        logger.error(f"알림 조회 오류: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()


@app.route('/stats', methods=['GET'])
def get_stats():
    """데이터 통계를 조회합니다."""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    ROUND(AVG(temperature), 2) as avg_temperature,
                    ROUND(MAX(temperature), 2) as max_temperature,
                    ROUND(MIN(temperature), 2) as min_temperature,
                    ROUND(AVG(humidity), 2) as avg_humidity,
                    ROUND(MAX(humidity), 2) as max_humidity,
                    ROUND(MIN(humidity), 2) as min_humidity,
                    ROUND(AVG(wind_speed), 2) as avg_wind_speed,
                    MIN(collected_at) as first_record,
                    MAX(collected_at) as last_record
                FROM sensor_data
            """)
            stats = cursor.fetchone()
            stats = serialize_row(stats)

            cursor.execute("SELECT COUNT(*) as alert_count FROM alert_log")
            alerts = cursor.fetchone()
            stats['alert_count'] = alerts['alert_count']

        return jsonify({"status": "success", "data": stats})
    except Exception as e:
        logger.error(f"통계 조회 오류: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()


@app.route('/health', methods=['GET'])
def health():
    """서버 및 데이터베이스 상태를 확인합니다."""
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        conn.close()
        return jsonify({
            "status": "ok",
            "database": "connected",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "database": "disconnected",
            "message": str(e)
        }), 500


# ============================================
# 앱 시작
# ============================================
if __name__ == '__main__':
    logger.info("🚀 Flask API 서버 시작 중...")
    wait_for_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
