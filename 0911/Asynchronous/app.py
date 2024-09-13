print("비동기")
want_row = 1000 # mongoDB limit

import asyncio
import time
import threading
from flask import Flask, jsonify
from flask_restx import Api, Resource, Namespace
import motor.motor_asyncio  # 비동기 MongoDB 클라이언트
import asyncpg  # 비동기 PostgreSQL 클라이언트
from datetime import datetime, timezone

COUNT = 0

# MongoDB 비동기 클라이언트 연결
client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://192.168.10.254:27018/')
db = client['atechTestMongo']
collection = db['productiontimeseriesdata']

# PostgreSQL 비동기 클라이언트 설정
# asyncpg는 파라미터로 dbname안쓰고 database씀 주의!!
db_params = {
    'database': 'INTERONE',
    'user': 'interx',
    'password': 'interx@504',
    'host': '192.168.160.199',
    'port': '15432'
}

# MongoDB 업데이트 비동기 함수
async def mongo_update():
    global COUNT
    start_time = time.time()  # 작업 시작 시간 기록
    try:
        conn = await asyncpg.connect(**db_params)
        print("PostgreSQL 연결 성공")

        # MongoDB에서 API 항목이 존재하는 문서 조회
        cursor = collection.find({
            "API": {"$exists": True},
            "CURRENT_BACKPRESS": {"$exists": False}
        }).sort("fromDateTime", -1).limit(want_row)

        async for doc in cursor:
            fromDateTime = doc['API']["fromDateTime"]
            toDateTime = doc['API']["toDateTime"]
            fsString = doc['API']["fsString"]

            # 필드 이름 가공
            element_list = [item.strip('"').lower() for item in fsString.split(',')] + ['received_time']
            fscode = element_list[0].split("_")[0].upper()

            for i, element in enumerate(element_list):
                element_list[i] = "_".join(element.split('_')[1:])

            # 시간 범위 설정
            from_timestamp = int(fromDateTime.timestamp() * 1000)
            to_timestamp = int(toDateTime.timestamp() * 1000)

            # PostgreSQL 쿼리
            query1 = f"""
                SELECT * FROM temp.api_datas_engel
                WHERE received_time BETWEEN {from_timestamp} AND {to_timestamp}
                AND fscode = '{fscode}'
                LIMIT 1
            """
            rows1 = await conn.fetch(query1)

            query2 = f"""
                SELECT * FROM temp.api_datas_lsm
                WHERE received_time BETWEEN {from_timestamp} AND {to_timestamp}
                AND fscode = '{fscode}'
                LIMIT 1
            """
            rows2 = await conn.fetch(query2)

            if len(rows1) + len(rows2) == 0:
                continue

            # MongoDB 업데이트
            for row in rows1 + rows2:
                mongo_update_data = {key: row[key] for key in element_list if key in row}

                timestamp_s = int(row['received_time']) / 1000
                dt = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
                mongo_update_data['received_time'] = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+00:00'

                await collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": mongo_update_data}
                )

            COUNT += 1
            # print(f"Updated document {doc['_id']}")

    except Exception as error:
        print("오류 발생:", error)
    finally:
        if conn:
            await conn.close()
        print("PostgreSQL 연결 종료")
        # 작업 종료 시간 기록 및 실행 시간 계산
        # MongoDB 연결 종료 메시지 추가
        client.close()
        print("MongoDB 연결 종료") 

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"실행 시간: {execution_time}초")

        

# Flask 및 Flask-RESTx 설정
app = Flask(__name__)
api = Api(app, version='1.0', title='My API', description='LeeYS MongoDB API + Flask + Swagger')
user_ns = Namespace("user/", decorators="사용자 정보 조회/수정/추가/삭제")

# API 엔드포인트
@api.route('/cnt')
class Count(Resource):
    @api.doc('현재 데이터 처리 개수')
    def get(self):
        # 동기 함수로 수정하여 비동기 호출을 하지 않음
        return jsonify({'Data Count': COUNT})

# 비동기 스레드 실행
def run_async_task():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(mongo_update())

# 백그라운드 작업 시작
count_thread = threading.Thread(target=run_async_task)
count_thread.start()

# API 실행
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5555, use_reloader=False) # 출력 2번 떠서 reload 끔 -> 왜 해결됨?
