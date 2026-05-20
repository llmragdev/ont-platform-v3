import httpx
import asyncio

async def seed():
    async with httpx.AsyncClient() as client:
        # 헬스체크
        try:
            resp = await client.get("http://localhost:8000/api/health")
            print(f"Health: {resp.json()}")
        except Exception as e:
            print(f"Server not running? {e}")
            return

        # 추가적인 데이터 시딩 로직 (필요시)
        print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed())
