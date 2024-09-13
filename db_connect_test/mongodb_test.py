from pymongo import MongoClient

# MongoDB 서버에 접속
client = MongoClient('mongodb://192.168.10.254:27018/') # 책임릠 주소 
# client = MongoClient('mongodb://localhost:27017/')

# 데이터베이스 선택
db = client['mydatabase']

# 컬렉션 선택 : 주의 임의 변경 금지
collection = db['mycollection']

# 데이터 삽입
data = {
    'name': '이윤서',
    'age': 100,
    'city': '지구'
}
result = collection.insert_one(data)
print(f'Data inserted with id: {result.inserted_id}')

# 데이터 조회
query = {'name': 'John Doe'}
result = collection.find_one(query)
print('Data found:', result)

# 여러 데이터 조회
print("여러 데이터 조회")
results = collection.find({'age': {'$gt': 20}})
for doc in results:
    print(doc)

# MongoDB 서버와의 연결 종료
client.close()