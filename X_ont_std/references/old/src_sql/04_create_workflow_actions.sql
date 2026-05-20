-- [04_create_workflow_actions.sql]
-- 액션 요청 기록 구현
USE DATABASE ONTOLOGY_EDU;
USE SCHEMA APP;

-- 액션 요청 테이블
CREATE OR REPLACE TABLE ACTION_REQUESTS (
    ACTION_ID STRING DEFAULT UUID_STRING(),
    OBJECT_TYPE STRING,
    OBJECT_ID STRING,
    ACTION_TYPE STRING,
    REQUESTED_BY STRING,
    REQUESTED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PAYLOAD VARIANT,
    STATUS STRING DEFAULT 'Requested'
);

-- 주문 승인 액션 요청 기록 프로시저
CREATE OR REPLACE PROCEDURE REQUEST_APPROVE_ORDER(ORDER_ID STRING, REQUESTED_BY STRING, COMMENT STRING)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    INSERT INTO ACTION_REQUESTS (
        OBJECT_TYPE,
        OBJECT_ID,
        ACTION_TYPE,
        REQUESTED_BY,
        PAYLOAD
    )
    SELECT
        'Order',
        OBJECT_ID,
        'ApproveOrder',
        :REQUESTED_BY,
        OBJECT_CONSTRUCT(
            'previous_status', STATUS,
            'order_amount', ORDER_AMOUNT,
            'comment', :COMMENT
        )
    FROM ONTOLOGY.ORDER_OBJECT
    WHERE OBJECT_ID = :ORDER_ID;

    RETURN 'ApproveOrder request has been recorded for order ' || :ORDER_ID || '.';
END;
$$;
