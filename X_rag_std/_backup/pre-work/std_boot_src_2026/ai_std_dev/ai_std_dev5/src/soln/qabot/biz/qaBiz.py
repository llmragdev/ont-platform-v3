import os
from soln.qabot.schemas.qaSch import QaRequest, QaResponse, IngestResponse
from soln.qabot.repository.qaRpo import QaRepository
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

class QaBizService:
    def __init__(self):
        self.repo = QaRepository()
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash-lite"),
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0
        )

    async def ingest_assets(self) -> IngestResponse:
        base_dir = self.repo.st.source_doc_dir
        file_names = ["2025년 AI바우처 사업설명회 발표자료.pdf"]
        full_paths = [os.path.join(base_dir, f) for f in file_names]
        success = await self.repo.save_knowledge_assets(full_paths)
        return IngestResponse(status="success" if success else "fail", message="지식 자산화 완료")

    async def ask_with_rag(self, req: QaRequest) -> QaResponse:
        # 1. RPO 데이터 검색 (k=10 확보로 누락 방지)
        scored_results = await self.repo.get_scored_docs(req.question, k=10)
        sorted_results = sorted(scored_results, key=lambda x: x[1]) 
        
        context_parts = []
        ui_sources = []
        
        # [디버깅] 상세 로그 출력 (내용 전체 확인용)
        print("\n" + "="*30 + " [BIZ: 상세 분석 로그] " + "="*30)
        for i, (doc, score) in enumerate(sorted_results):
            similarity = round(1 - score, 4)
            page = doc.metadata.get('page', 0) + 1
            print(f"[{i+1}순위] 유사도: {similarity} | P.{page} | 내용: {doc.page_content.strip()[:60]}...")
            
            context_parts.append(f"[Ref {i+1}/P.{page}] {doc.page_content}")
            ui_sources.append(f"P.{page} (Score: {similarity})")

        # 2. [핵심] 간결하고 명확한 비즈니스 답변을 위한 프롬프트
        prompt = ChatPromptTemplate.from_template("""
        당신은 사내 지식 가이드 AI입니다. 
        [Context]를 바탕으로 사용자의 질문에 핵심 위주로 명확하게 답하세요.
        
        [지침]
        1. 질문에 대한 직접적인 정답을 가장 먼저 제시하고, 상세 설명은 불필요하게 늘리지 마세요.
        2. 본문에는 '(근거 X)'나 '[Ref X]'와 같은 주석 표시를 절대 하지 마세요. 순수 텍스트만 출력하세요.
        3. 항목별 나열(Bullet point)을 사용하여 가독성을 높이세요.
        
        [Context]
        {context}
        
        [Question]
        {question}
        """)
        
        chain = prompt | self.llm
        result = await chain.ainvoke({"context": "\n\n".join(context_parts), "question": req.question})
        
        return QaResponse(
            answer=result.content.strip(),
            source_documents=ui_sources
        )