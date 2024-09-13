'''
1. MongoDB -> API 항목 있는 document 조회
2. 1번 API 항목 데이터(from, to, column이름)를 토대로 postgreSQL 조회 (table : temp.api_datas_engel , temp.api_datas_lsm)
3. MongoDB '기존 document에' 새로운 Field 추가
'''
#################################### 0. 모듈 로딩
from pymongo import MongoClient
import psycopg2
from psycopg2 import sql
from datetime import datetime
import json # 편안한 내 눈을 위함 
def json_default(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')  # 원하는 형식으로 변환
    raise TypeError(f"Type {type(value)} not serializable")

#################################### 1. MongoDB -> API 항목 있는 document 조회

# MongoDB 서버에 접속
client = MongoClient('mongodb://192.168.10.254:27018/') # 책임릠 주소 
# client = MongoClient('mongodb://localhost:27017/')

# 데이터베이스 선택
db = client['atechTestMongo']

# 컬렉션 선택
collection = db['productiontimeseriesdata']

#  API 항목이 존재하는 document 조회
print("여러 데이터 조회")
field_API = collection.find({ "API": { "$exists": True } })
print(type(field_API))
# for doc in field_API:
#     print(doc)
#     break

#################################### 2. API 항목 데이터(from, to, column이름)를 토대로 postgreSQL 조회 (table : temp.api_datas_engel , temp.api_datas_lsm)
################ 2-1 API 항목 분석하기
col_name_list = []
max_cnt = 100

# pymongo.cursor.Cursor(field_API) 파일포인터 처럼 작용해서 한번 접근하면 다음으로 넘어감
for i, doc in enumerate(field_API):
    if i == max_cnt:
        break
    # print(json.dumps(doc['API'], indent=4, ensure_ascii=False, default=json_default))
    fromDateTime = doc['API']["fromDateTime"]
    toDateTime = doc['API']["toDateTime"]
    print(fromDateTime, toDateTime)

    # 주어진 문자열 => '"PD2007_CURRENT_BACKPRESS..."'
    fsString = doc['API']["fsString"]
    # 문자열을 ,로 분리하고 각 요소에서 양 끝의 "를 제거
    element_list = [item.strip('"') for item in fsString.split(',')]
    # fscode를 알아내보자,,,  
    fscode = element_list[0].split("_")[0]
    print(fscode)
    for i, element in enumerate(element_list):
        element_list[i] = "_".join(element.split('_')[1:])

    # 결과 출력
    print(element_list)
    print()

################ 2-2 postgreSQL 조회하기
# Postgre Database connection parameters
db_params = {
    'dbname': 'INTERONE',
    'user': 'interx',
    'password': 'interx@504',
    'host': '192.168.160.199',
    'port': '15432'  # Default is 5432
}

try:
    # Establish a connection to the PostgreSQL database 연결 
    conn = psycopg2.connect(**db_params)
    print("Connection established")

    # Create a cursor object
    cursor = conn.cursor()

    # Execute a SQL query
    cursor.execute("SELECT version();")

    # Fetch the result of the query
    db_version = cursor.fetchone()
    print("연결 잘 됐나 확인,,, PostgreSQL database version:", db_version)
    
    test_table1 = "api_datas_engel"
    test_table2 = "api_datas_lsm"
    # Example of fetching data from the table
   
    # cursor.execute(f"SELECT * FROM temp.{test_table1} ade limit 1;")
    # SQL query to fetch rows where received_time and fscode match between the two tables

    # MongoDB에서 가져온 fromDateTime과 toDateTime을 유닉스 타임스탬프 밀리초로 변환
    fromDateTime = int(fromDateTime.timestamp() * 1000)
    toDateTime = int(toDateTime.timestamp() * 1000)   
    print(fromDateTime, toDateTime)

    # 첫 번째 테이블 조회 쿼리
    query1 = f"""
        SELECT * FROM temp.{test_table1}
        WHERE received_time BETWEEN {fromDateTime} AND {toDateTime}
        LIMIT 10
    """

    # 두 번째 테이블 조회 쿼리
    query2 = f"""
        SELECT * FROM temp.{test_table2}
        WHERE received_time BETWEEN {fromDateTime} AND {toDateTime}
        LIMIT 10
    """

    # Execute the SQL queries
    cursor.execute(query1)
    rows1 = cursor.fetchall()

    cursor.execute(query2)
    rows2 = cursor.fetchall()

    # 결과 출력
    print("Results from", test_table1)
    for row in rows1:
        print(row)

    print("Results from", test_table2)
    for row in rows2:
        print(row)

except Exception as error:
    print("Error connecting to PostgreSQL database:", error)
finally:
    # Close the cursor and connection
    if cursor:
        cursor.close()
    if conn:
        conn.close()
    print("Connection closed")

#################################### MongoDB 서버와의 연결 종료
client.close()