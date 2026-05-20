# sit_scenario_data.py

# [1단계] 공통 업로드 대상 파일 목록
COMMON_UPLOAD_TASKS = [
    {
        "desc": "V5001 기본 논문 적재",
        "local_dir": r"F:\ai_std_dev\data\Test_file\02_온톨로지논문\1001_2002",
        "mid": "1001", "sub": "2002"
    },
    {
        "desc": "V5001 특정 파일 추가",
        "local_dir": r"F:\ai_std_dev\data\Test_file\02_온톨로지논문\1001_2003",
        "file_name": "국방 - [01] 온톨로지와지식그래프를활용한국방지휘통제데이터통합방법연구-2025.pdf",
        "mid": "1001", "sub": "2003"
    },
    {
        "desc": "V5002 특정 파일 격리 적재",
        "local_dir": r"F:\ai_std_dev\data\Test_file\02_온톨로지논문\1001_2003",
        "file_name": "국방 - [02] 해외 온톨로지 현황과 한국군 온톨로지 개발방안_202306.pdf",
        "mid": "1001", "sub": "2004"
    }
]

# [2단계] 공통 벡터 DB 동기화 목록
COMMON_VECTORIZE_TASKS = [
    {"desc": "V5001 동기화 (1001/2002)", "mid": "1001", "sub": "2002", "target_v_id": "5001"},
    {"desc": "V5001 동기화 (1001/2003)", "mid": "1001", "sub": "2003", "target_v_id": "5001"},
    {"desc": "V5002 동기화 (1001/2004)", "mid": "1001", "sub": "2004", "target_v_id": "5002"}
]

# (기존에 작성하신 COMMON_QUESTIONS 는 이 아래에 그대로 두시면 됩니다)
COMMON_QUESTIONS = [
    {"no": 1, "q": "국방 지휘통제 데이터 통합을 위한 온톨로지 연구의 핵심 내용은?", "v_id": "5001"},
    {"no": 2, "q": "방금 질문한 연구의 기대효과를 요약해줘.", "v_id": "5001"},
    {"no": 3, "q": "해외 군사 온톨로지 개발 현황에 대해 설명해줘.", "v_id": "5002"},
]
