-- ============================================
-- 데이터베이스 생성 (docker-compose에서 자동 생성되지만 명시적 선언)
-- ============================================
CREATE DATABASE IF NOT EXISTS monitoring_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE monitoring_db;

-- ============================================
-- 센서 데이터 테이블
-- n8n이 수집한 날씨 데이터 저장
-- ============================================
CREATE TABLE IF NOT EXISTS sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    temperature FLOAT NOT NULL COMMENT '온도 (°C)',
    humidity FLOAT NOT NULL COMMENT '습도 (%)',
    wind_speed FLOAT NOT NULL COMMENT '풍속 (km/h)',
    source VARCHAR(100) DEFAULT 'open-meteo' COMMENT '데이터 출처',
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '수집 시각'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 알림 로그 테이블
-- 임계값 초과 시 기록 (예: 온도 > 30°C)
-- ============================================
CREATE TABLE IF NOT EXISTS alert_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL COMMENT '측정 항목명',
    metric_value FLOAT NOT NULL COMMENT '측정값',
    threshold FLOAT NOT NULL COMMENT '임계값',
    message TEXT COMMENT '알림 메시지',
    alerted_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '알림 발생 시각'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 인덱스 생성 (조회 성능 최적화)
-- ============================================
CREATE INDEX idx_sensor_collected_at ON sensor_data(collected_at);
CREATE INDEX idx_alert_alerted_at ON alert_log(alerted_at);
CREATE INDEX idx_sensor_temperature ON sensor_data(temperature);

-- ============================================
-- monitor 사용자에게 권한 부여
-- ============================================
GRANT ALL PRIVILEGES ON monitoring_db.* TO 'monitor'@'%';
FLUSH PRIVILEGES;

-- ============================================
-- 초기 테스트 데이터 삽입 (선택사항)
-- ============================================
INSERT INTO sensor_data (temperature, humidity, wind_speed, source, collected_at) VALUES
(22.5, 65.0, 12.3, 'open-meteo-seoul', NOW() - INTERVAL 30 MINUTE),
(23.1, 63.5, 11.8, 'open-meteo-seoul', NOW() - INTERVAL 25 MINUTE),
(24.8, 60.2, 13.1, 'open-meteo-seoul', NOW() - INTERVAL 20 MINUTE),
(26.3, 58.7, 14.5, 'open-meteo-seoul', NOW() - INTERVAL 15 MINUTE),
(28.0, 55.0, 15.2, 'open-meteo-seoul', NOW() - INTERVAL 10 MINUTE),
(31.2, 52.3, 16.8, 'open-meteo-seoul', NOW() - INTERVAL 5 MINUTE),
(29.5, 54.1, 15.0, 'open-meteo-seoul', NOW());

-- 임계값 초과 데이터에 대한 alert 기록
INSERT INTO alert_log (metric_name, metric_value, threshold, message, alerted_at) VALUES
('temperature', 31.2, 30.0, '온도 임계값 초과: 31.2°C (기준: 30°C)', NOW() - INTERVAL 5 MINUTE);
