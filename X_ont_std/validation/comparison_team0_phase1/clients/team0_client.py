import asyncio
import httpx
from typing import Dict, List

class Team0Client:
    def __init__(self, base_url: str = "http://localhost:8002", tenant_id: str = "company_abc", org_id: str = "0200"):
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self.org_id = org_id
        self.headers = {
            "X-Tenant-ID": tenant_id,
            "X-Org-ID": org_id,
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient()

    async def health_check(self) -> bool:
        """Team0 RAG 서버의 헬스 상태를 점검합니다."""
        url = f"{self.base_url}/api/v1/health"
        try:
            # 헬스체크는 헤더 없이도 동작할 수 있으나 명확성을 위해 포함
            resp = await self.client.get(url, headers=self.headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                # status가 ok이거나 전체 응답 확인
                return data.get("status") in ["ok", "success"]
            return False
        except Exception as e:
            print(f"⚠️ Health check failed at {url}: {e}")
            return False

    async def search(self, query: str, top_k: int = 5) -> Dict:
        """단일 검색 쿼리를 Team0 RAG 서버에 전송합니다."""
        url = f"{self.base_url}/api/v1/rag/search"
        payload = {
            "query": query,
            "top_k": top_k,
            "debug_mode": True
        }
        
        for attempt in range(3):
            try:
                resp = await self.client.post(url, headers=self.headers, json=payload, timeout=30.0)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                print(f"⚠️ Search attempt {attempt + 1}/3 failed for query '{query}': {e}")
                if attempt == 2:
                    raise e
                await asyncio.sleep(1.5)

    async def batch_search(self, queries: List[str], top_k: int = 5) -> List[Dict]:
        """여러 쿼리를 동시에 실행하여 결과를 모아 반환합니다."""
        tasks = [self.search(q, top_k) for q in queries]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def close(self):
        """HTTP 클라이언트를 종료합니다."""
        await self.client.aclose()

if __name__ == "__main__":
    from pathlib import Path
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from config import TEAM0_API_BASE, TEAM0_TENANT_ID, TEAM0_ORG_ID
    
    async def main():
        client = Team0Client(TEAM0_API_BASE, TEAM0_TENANT_ID, TEAM0_ORG_ID)
        health = await client.health_check()
        print(f"🏥 Team0 Connection Status: {'CONNECTED' if health else 'DISCONNECTED'}")
        
        if health:
            print("🔍 Testing search...")
            res = await client.search("온톨로지란 무엇인가?", top_k=3)
            print("Response Status:", res.get("status"))
            if res.get("data"):
                print("Answer Length:", len(res["data"].get("answer", "")))
        await client.close()
        
    asyncio.run(main())
