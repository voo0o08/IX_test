'''
예시 가정) USER_MAX = 1000, BATCH_SIZE = 100
- MongoDB에서 데이터는 USER_MAX만큼 1번 불러온다
- 불러온 Document를 BATCH_SIZE만큼 분리한다 예시에서는 10개의 BATCH가 생김
- CASE1) 10개의 BATCH들을 한번에 비동기, PostgreSQL조회는 비동기
- CASE2) 10개의 BATCH는 동기, PostgreSQL조회는 비동기
'''
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import asyncpg
from datetime import datetime, timezone
import time
print(" ========================= 비동기 통신 파일 ========================= ")
USER_MAX = 100
BATCH_SIZE = 10

async def main():
    # MongoDB 비동기 클라이언트 연결
    mongo_client = AsyncIOMotorClient('mongodb://192.168.10.254:27018/')
    db = mongo_client['atechTestMongo']
    collection = db['productiontimeseriesdata']

    # PostgreSQL 비동기 클라이언트 연결 (Connection Pool 생성)
    pool = await asyncpg.create_pool(
        user='interx', password='interx@504',
        database='INTERONE', host='192.168.160.199', port='15432'
    )

    # MongoDB에서 데이터 가져오기
    field_API = await collection.find({
        "API": {"$exists": True},
    }).sort("fromDateTime", -1).limit(USER_MAX).to_list(None)  # USER_MAX만큼 가져오기

    # BATCH_SIZE로 데이터 분할
    batches = [field_API[i:i + BATCH_SIZE] for i in range(0, len(field_API), BATCH_SIZE)]
    
    start_time = time.time()

    # CASE 1: 모든 BATCH를 비동기로 처리
    tasks = []
    for batch in batches:
        task = process_batch(batch, pool, collection)  # BATCH마다 처리
        tasks.append(task)

    # 모든 BATCH를 비동기로 처리
    await asyncio.gather(*tasks)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"실행 시간: {execution_time}초")

    # 연결 종료
    await pool.close()
    mongo_client.close()
    print("MongoDB 및 PostgreSQL 연결 종료")

async def process_batch(batch, pool, collection):
    tasks = []
    for doc in batch:
        task = process_document(doc, pool, collection)  # 문서 처리
        tasks.append(task)

    # 각 BATCH 내 문서들을 비동기로 처리
    await asyncio.gather(*tasks)

async def process_document(doc, pool, collection):
    # PostgreSQL 비동기 조회 예시 (PostgreSQL 조회 부분)
    async with pool.acquire() as conn:  # 연결 풀에서 안전하게 연결 획득
        fromDateTime = doc['API']["fromDateTime"]
        toDateTime = doc['API']["toDateTime"]

        fsString = doc['API']["fsString"]
        element_list = [item.strip('"').lower() for item in fsString.split(',')] + ['received_time']
        fscode = element_list[0].split("_")[0].upper()

        for i, element in enumerate(element_list):
            element_list[i] = "_".join(element.split('_')[1:])

        fromDateTime = int(fromDateTime.timestamp() * 1000)
        toDateTime = int(toDateTime.timestamp() * 1000)

        query1 = f"""
            SELECT * FROM temp.api_datas_engel
            WHERE received_time BETWEEN {fromDateTime} AND {toDateTime}
            AND fscode = '{fscode}'
            LIMIT 1
        """
        rows1 = await conn.fetch(query1)

        query2 = f"""
            SELECT * FROM temp.api_datas_lsm
            WHERE received_time BETWEEN {fromDateTime} AND {toDateTime}
            AND fscode = '{fscode}'
            LIMIT 1
        """
        rows2 = await conn.fetch(query2)

        if len(rows1) + len(rows2) == 0:
            return

        for row in rows1 + rows2:
            mongo_update_data = {key: row[key] for key in element_list if key in row}
            
            timestamp_s = int(row['received_time']) / 1000
            dt = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
            mongo_update_data['received_time'] = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+00:00'
            
            await collection.update_one(
                {"_id": doc["_id"]},
                {"$set": mongo_update_data}
            )


# 메인 함수 실행
asyncio.run(main())