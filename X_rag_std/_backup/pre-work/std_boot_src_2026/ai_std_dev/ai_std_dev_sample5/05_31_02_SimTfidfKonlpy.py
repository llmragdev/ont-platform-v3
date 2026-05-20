from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from konlpy.tag import Okt  # 한국어 형태소 분석기

# 1. 형태소 분석기 초기화
okt = Okt()

def tokenizer(text):
    # 명사만 추출하거나 어간 추출(stemming)을 선택할 수 있습니다.
    # 여기서는 명사만 추출하여 "운영자는" -> "운영자"로 만듭니다.
    return okt.nouns(text)

def improved_old_method(query, document):
    # tokenizer 인자에 위에서 만든 함수를 넣어줍니다.
    vectorizer = TfidfVectorizer(tokenizer=tokenizer)
    
    try:
        tfidf_matrix = vectorizer.fit_transform([query, document])
        return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except:
        return 0.0

# 1. 사내 기술 표준 문서 청킹 (교육용 데이터)
chunks = [
    "인프라 보안 표준: 사내 서버에 접근하기 위해서는 반드시 2단계 인증(2FA)을 거쳐야 하며, 보안팀의 사전 승인이 필수입니다.",
    "소프트웨어 배포 절차: 모든 코드는 메인 브랜치 병합 전 최소 2인 이상의 코드 리뷰를 거친 후 CI/CD 파이프라인을 통해 배포됩니다.",
    "데이터베이스 설계 원칙: 관계형 DB 사용 시 모든 테이블은 제3정규형을 준수해야 하며, 인덱스 생성 전 DBA의 검토가 필요합니다.",
    "로그 관리 규정: 모든 API 호출 로그는 ELK 스택을 통해 90일간 보관되며, 개인정보가 포함된 데이터는 마스킹 처리가 의무화됩니다.",
    "네트워크 구성 표준: 개발 환경과 운영 환경은 가상 네트워크(VPC) 수준에서 완전히 격리되어야 하며 방화벽은 최소 권한 원칙을 따릅니다."
]

# 2. 질문 (사용자가 챗봇에 물어볼 법한 내용)
query = "보안 승인 절차"

print(f"질문: '{query}' (KoNLPy 형태소 분석 방식)\n")
print("-" * 50)

for i, chunk in enumerate(chunks):
    sim = improved_old_method(query, chunk)
    print(f"[청크 {i+1}] 유사도: {sim:.4f} | 내용: {chunk[:40]}...")