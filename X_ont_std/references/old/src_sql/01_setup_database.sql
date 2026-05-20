-- [01_setup_database.sql]
-- 데이터베이스 및 스키마 생성
CREATE OR REPLACE DATABASE ONTOLOGY_EDU;
USE DATABASE ONTOLOGY_EDU;

CREATE OR REPLACE SCHEMA RAW;       -- 원천 데이터 적재 영역
CREATE OR REPLACE SCHEMA ONTOLOGY;  -- 온톨로지 객체/관계 정의 영역
CREATE OR REPLACE SCHEMA APP;       -- 애플리케이션 액션/로직 영역
