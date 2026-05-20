import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from konlpy.tag import Okt  # 한국어 형태소 분석기

# 1. 형태소 분석기 초기화 (JVM 환경 변수 JAVA_HOME 참조)
okt = Okt()

def tokenizer(text):
    # 명사만 추출하여 조사("는", "의")의 영향을 배제하고 핵심 의미만 비교
    return okt.nouns(text)

def improved_old_method(query, document):
    # 유연한 비교를 위해 형태소 분석 기반의 tokenizer 적용
    # UserWarning 방지를 위해 token_pattern=None 설정
    vectorizer = TfidfVectorizer(tokenizer=tokenizer, token_pattern=None)
    
    try:
        tfidf_matrix = vectorizer.fit_transform([query, document])
        return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except:
        return 0.0

# 2. [사내 강의용 핵심 로직] 외부 MD 파일 로드 및 전처리
file_name = "사내기술표준문서.md"
chunks = []

if os.path.exists(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 텍스트가 비어있거나, 마크다운 기호(#, ---, *)로 시작하는 행 제외
            if line and not line.startswith(('#', '---', '*')):
                chunks.append(line)
else:
    print(f"Error: {file_name} 파일을 찾을 수 없습니다.")
    chunks = ["파일 로드 실패"]

# 3. 질문 및 테스트 실행
query = "보안 승인 절차"

print(f"질문: '{query}' (KoNLPy 형태소 분석 방식)\n")
print("-" * 60)

for i, chunk in enumerate(chunks):
    sim = improved_old_method(query, chunk)
    # 가독성을 위해 상위 10개 문장만 출력하거나 필터링 가능
    print(f"[청크 {i+1}] 유사도: {sim:.4f} | 내용: {chunk[:45]}...")