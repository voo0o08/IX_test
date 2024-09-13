# MongoDB document에 데이터 추가
#################################### 0. 모듈 로딩
from pymongo import MongoClient
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor # 컬럼명 때문
from datetime import datetime, timezone
import json # 편안한 내 눈을 위함 
import time

def json_default(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')  # 원하는 형식으로 변환
    raise TypeError(f"Type {type(value)} not serializable")

#################################### 1. MongoDB -> API 항목 있는 document 조회

# MongoDB 서버에 접속
client = MongoClient('mongodb://192.168.10.254:27018/') # 책임릠 주소 

# 데이터베이스 선택
db = client['atechTestMongo']

# 컬렉션 선택
collection = db['productiontimeseriesdata']

#  API 항목이 존재하는 document 조회
print("여러 데이터 조회")
# field_API = collection.find({ "API": { "$exists": True } })
field_API = collection.find({
    "API": { "$exists": True },
    "CURRENT_BACKPRESS": { "$exists": False }
}).sort("fromDateTime", -1).limit(100)

# postgres 연결
db_params = {
        'dbname': 'INTERONE',
        'user': 'interx',
        'password': 'interx@504',
        'host': '192.168.160.199',
        'port': '15432'  # Default is 5432
    }
try:
    # PostgreSQL 연결
    conn = psycopg2.connect(**db_params)
    print("PostgreSQL 연결 성공")

    # Create a cursor object
    cursor = conn.cursor(cursor_factory=RealDictCursor) # 딕셔너리 형태 

except Exception as error:
    print("PostgreSQL 연결 오류:", error)
    
#################################### 2. API 항목 데이터(from, to, column이름)를 토대로 postgreSQL 조회
col_name_list = []
max_cnt = 100
start_time = time.time()
# MongoDB 문서마다 처리
for i, doc in enumerate(field_API):
    # if i == max_cnt:
    #     break

    # print(json.dumps(doc['API'], indent=4, ensure_ascii=False, default=json_default))
    fromDateTime = doc['API']["fromDateTime"]
    toDateTime = doc['API']["toDateTime"]
    # print(fromDateTime, toDateTime)

    # 주어진 문자열 => '"PD2007_CURRENT_BACKPRESS..."'
    fsString = doc['API']["fsString"]
    # 문자열을 ,로 분리하고 각 요소에서 양 끝의 "를 제거
    element_list = [item.strip('"').lower() for item in fsString.split(',')] + ['received_time']# column명 list 
    # fscode를 알아내보자,,,  
    fscode = element_list[0].split("_")[0].upper()
    # print(fscode)
    for i, element in enumerate(element_list):
        element_list[i] = "_".join(element.split('_')[1:])

    # SQL 쿼리 작성 및 실행
    fromDateTime = int(fromDateTime.timestamp() * 1000)
    toDateTime = int(toDateTime.timestamp() * 1000)

    query1 = f"""
        SELECT * FROM temp.api_datas_engel
        WHERE received_time BETWEEN {fromDateTime} AND {toDateTime}
        AND fscode = '{fscode}'
        LIMIT 1
    """
    cursor.execute(query1)
    rows1 = cursor.fetchall()

    query2 = f"""
        SELECT * FROM temp.api_datas_lsm
        WHERE received_time BETWEEN {fromDateTime} AND {toDateTime}
        AND fscode = '{fscode}'
        LIMIT 1
    """
    cursor.execute(query2)
    rows2 = cursor.fetchall()

    # 데이터 없으면 SKIP
    if len(rows1) + len(rows2) == 0:
        continue

    # print(fromDateTime, toDateTime)
    # PostgreSQL에서 조회한 데이터 중 element_list에 있는 컬럼만 MongoDB에 추가
    # print(rows1 + rows2) [RealDictRow([('received_time', 1717425000326), ('fscode', 'PD2006'),...
    for row in rows1 + rows2:
        mongo_update_data = {}
        # 필요한 컬럼만 선택하여 MongoDB에 추가할 데이터 준비
        mongo_update_data = {key: row[key] for key in element_list if key in row}
        
        # timestamp 원하는 형식으로 변환
        timestamp_s = int(row['received_time']) / 1000
        dt = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
        mongo_update_data['received_time'] = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+00:00'
        

        # MongoDB에 업데이트 (예시로 문서를 업데이트)
        collection.update_one(
            {"_id": doc["_id"]},  # 기존 MongoDB 문서 ID를 기준으로 업데이트
            {"$set": mongo_update_data}
        )
    # print(mongo_update_data)
    # print(f"Updated MongoDB document with _id: {doc['_id']}")

 # 종료 시간 기록
end_time = time.time()
execution_time = end_time - start_time
print(f"실행 시간: {execution_time}초")


#################################### DB 서버와 연결 종료
client.close()
print("MongoDB 연결 종료")

if cursor:
    cursor.close()
if conn:
    conn.close()
print("PostgreSQL 연결 종료")
