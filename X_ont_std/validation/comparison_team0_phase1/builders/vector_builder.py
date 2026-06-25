import json
import asyncio
import httpx
from pathlib import Path
import sys

class VectorBuilder:
    def __init__(self, embedding_url: str, tenant_id: str):
        self.embedding_url = embedding_url
        self.tenant_id = tenant_id

    async def _call_embedding_api(self, client: httpx.AsyncClient, text: str) -> list:
        """LLM Gateway 임베딩 API를 호출합니다."""
        for attempt in range(3):
            try:
                resp = await client.post(
                    self.embedding_url,
                    json={"text": text, "tenant_id": self.tenant_id},
                    timeout=30.0
                )
                resp.raise_for_status()
                return resp.json()["embedding"]
            except Exception as e:
                print(f"⚠️ Embedding retry {attempt + 1}/3 for: {text[:20]}... Error: {e}")
                if attempt == 2:
                    raise e
                await asyncio.sleep(1.0)

    async def vectorize_all_chunks(self, chunks: list) -> list:
        """모든 청크에 대해 임베딩 벡터를 구합니다."""
        async with httpx.AsyncClient() as client:
            batch_size = 20  # 병렬 처리 크기
            vectorized_chunks = []
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                print(f"⚡ Vectorizing chunks {i + 1} to {min(i + batch_size, len(chunks))} of {len(chunks)}...")
                
                async def process_chunk(chunk):
                    try:
                        emb = await self._call_embedding_api(client, chunk["text"])
                        return {
                            "id": chunk["id"],
                            "doc_id": chunk["doc_id"],
                            "text": chunk["text"],
                            "start_char": chunk["start_char"],
                            "end_char": chunk["end_char"],
                            "embedding": emb,
                            "metadata": chunk["metadata"]
                        }
                    except Exception as e:
                        print(f"❌ Failed to embed chunk {chunk['id']}: {e}")
                        # 에러 발생 시 임시로 3072차원 0 벡터를 넣어 중단 방지
                        return {
                            "id": chunk["id"],
                            "doc_id": chunk["doc_id"],
                            "text": chunk["text"],
                            "start_char": chunk["start_char"],
                            "end_char": chunk["end_char"],
                            "embedding": [0.0] * 3072,
                            "metadata": chunk["metadata"]
                        }
                        
                batch_tasks = [process_chunk(c) for c in batch]
                batch_results = await asyncio.gather(*batch_tasks)
                vectorized_chunks.extend(batch_results)
                
            return vectorized_chunks

async def main():
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from config import GEMINI_EMBEDDING_API, TEAM0_TENANT_ID, RESULTS_DIR
    
    chunks_file = RESULTS_DIR / "chunks.json"
    if not chunks_file.exists():
        print(f"❌ Cannot find {chunks_file}. Run chunk_extractor.py first.")
        sys.exit(1)
        
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    print(f"🚀 Vectorizing {len(chunks)} chunks using {GEMINI_EMBEDDING_API}...")
    builder = VectorBuilder(GEMINI_EMBEDDING_API, TEAM0_TENANT_ID)
    
    # 임베딩 요청 실행
    vectorized = await builder.vectorize_all_chunks(chunks)
    
    output_file = RESULTS_DIR / "vectors.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(vectorized, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Successfully vectorized and saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
