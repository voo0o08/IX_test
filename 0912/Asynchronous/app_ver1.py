import asyncio
import time
import threading
from flask import Flask, jsonify
from flask_restx import Api, Resource, Namespace
import motor.motor_asyncio  # 비동기 MongoDB 클라이언트
import asyncpg  # 비동기 PostgreSQL 클라이언트
from datetime import datetime, timezone

COUNT = 0
BATCH_SIZE = 100  # 배치 크기 설정 (1000건 또는 10000건으로 변경 가능)

# MongoDB 비동기 클라이언트 연결
client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://192.168.10.254:27018/')
db = client['atechTestMongo']
collection = db['productiontimeseriesdata']
print("MongoDB 연결 성공")  # MongoDB 연결 성공 메시지 추가

# PostgreSQL 비동기 클라이언트 설정
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

        # MongoDB에서 API 항목이 존재하는 문서 조회 (Batch 단위로)
        cursor = collection.find({
            "API": {"$exists": True},
            "CURRENT_BACKPRESS": {"$exists": False}
        }).sort("fromDateTime", -1).allow_disk_use(True)  # Disk 사용 허용
        
        batch = []
        temp_i = 0
        async for doc in cursor:
            print(temp_i)
            batch.append(doc)
            if len(batch) == BATCH_SIZE:  # 배치 크기만큼 수집되었을 때 처리
                await process_batch(batch, conn)
                batch.clear()  # 배치 처리 후 비우기
            temp_i += 1

        # 남은 데이터 처리
        if batch:
            await process_batch(batch, conn)

    except Exception as error:
        print("오류 발생:", error)
    finally:
        if conn:
            await conn.close()
        print("PostgreSQL 연결 종료")
        
        # 작업 종료 시간 기록 및 실행 시간 계산
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"실행 시간: {execution_time}초")
        
        # MongoDB 연결 종료 메시지 추가
        client.close()
        print("MongoDB 연결 종료")



async def process_batch(batch, conn):
    """
    주어진 배치를 처리하는 함수.
    각 문서의 fromDateTime과 toDateTime에 맞춰 PostgreSQL에 데이터를 요청하고, MongoDB를 업데이트함.
    """
    global COUNT

    # 배치 내 fsString 처리 및 PostgreSQL 쿼리 생성
    for doc in batch:
        from_timestamp = int(doc['API']['fromDateTime'].timestamp() * 1000)
        to_timestamp = int(doc['API']['toDateTime'].timestamp() * 1000)

        fsString = doc['API']["fsString"]
        element_list = [item.strip('"').lower() for item in fsString.split(',')] + ['received_time']
        fscode = element_list[0].split("_")[0].upper()

        # PostgreSQL에서 데이터를 조회
        query1 = f"""
            SELECT * FROM temp.api_datas_engel
            WHERE received_time BETWEEN {from_timestamp} AND {to_timestamp}
            AND fscode = '{fscode}'
        """
        rows1 = await conn.fetch(query1)

        query2 = f"""
            SELECT * FROM temp.api_datas_lsm
            WHERE received_time BETWEEN {from_timestamp} AND {to_timestamp}
            AND fscode = '{fscode}'
        """
        rows2 = await conn.fetch(query2)

        # PostgreSQL에서 조회한 데이터를 MongoDB에 업데이트
        if rows1 or rows2:
            await update_mongo([doc], rows1 + rows2)

    # 데이터가 없더라도 COUNT를 증가시키도록 처리
    COUNT += len(batch)  # 처리된 문서 수 업데이트
    print(f"배치 처리 완료: {len(batch)}건 처리됨")


async def update_mongo(batch, rows):
    """
    PostgreSQL에서 가져온 데이터를 MongoDB에 업데이트하는 함수.
    """
    for row in rows:
        mongo_update_data = {}
        element_list = [key for key in row.keys()]  # PostgreSQL에서 가져온 컬럼들
        for doc in batch:
            fsString = doc['API']["fsString"]
            element_list_mongo = [item.strip('"').lower() for item in fsString.split(',')] + ['received_time']

            # PostgreSQL 데이터에서 필요한 컬럼만 추출
            mongo_update_data = {key: row[key] for key in element_list_mongo if key in row}

            # timestamp 원하는 형식으로 변환
            timestamp_s = int(row['received_time']) / 1000
            dt = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
            mongo_update_data['received_time'] = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+00:00'

            # MongoDB에 업데이트
            await collection.update_one(
                {"_id": doc["_id"]},
                {"$set": mongo_update_data}
            )


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
    app.run(debug=True, host='0.0.0.0', port=5555, use_reloader=False)  # Flask reloader 비활성화
