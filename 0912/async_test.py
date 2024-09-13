'''
해당파일은 batch는 빠져있고 only 비동기만
계획
자,,, API 생각하지 말고 비동기만 생각해보자
1. 불러와!
2. 쪼개!
3. 돌려! -> 근데 그 안에서 비동기야
4. 다음 batch 오!
'''
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import asyncpg
from datetime import datetime, timezone
import time
print(" ========================= 비동기 통신 파일 ========================= ")
USER_MAX = 100

def json_default(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')  # 원하는 형식으로 변환
    raise TypeError(f"Type {type(value)} not serializable")

# 비동기 함수 정의
async def process_document(doc, conn, collection):
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

async def main():
    # MongoDB 비동기 클라이언트 연결
    mongo_client = AsyncIOMotorClient('mongodb://192.168.10.254:27018/')
    db = mongo_client['atechTestMongo']
    collection = db['productiontimeseriesdata']

    # PostgreSQL 비동기 클라이언트 연결 (Connection Pool 생성)
    # asyncpg : 하나의 연결에 대해 동시에 여러 개의 쿼리 요청 허용 X -> connection pool 사용하기 
    pool = await asyncpg.create_pool(
        user='interx', password='interx@504',
        database='INTERONE', host='192.168.160.199', port='15432'
    )

    field_API = collection.find({
        "API": {"$exists": True},
        # "CURRENT_BACKPRESS": {"$exists": False}
    }).sort("fromDateTime", -1).limit(USER_MAX)

    start_time = time.time()

    tasks = []
    async for doc in field_API:
        task = process_document(doc, pool, collection)
        tasks.append(task)

    await asyncio.gather(*tasks)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"실행 시간: {execution_time}초")

    # 연결 종료
    await pool.close()  # Pool을 닫아야 함
    mongo_client.close()
    print("MongoDB 및 PostgreSQL 연결 종료")

# 메인 함수 실행
asyncio.run(main())