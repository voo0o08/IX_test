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
    'name': 'test',
    'age': 40,
    'city': '대구'
}
result = collection.insert_one(data)
print(f'Data inserted with id: {result.inserted_id}')

# 데이터 조회
# query = {'name': 'John Doe'}
# result = collection.find_one(query)
# print('Data found:', result)

# 여러 데이터 조회
print("여러 데이터 조회")
results = collection.find({'age': {'$gt': 20}})
# 조회된 문서들의 age 값을 1씩 증가시키기
for doc in results:
    new_age = doc['age'] + 1  # 기존 age 값에 1 더하기
    collection.update_one({'_id': doc['_id']}, {'$set': {'age': new_age}})  # 새로운 age 값으로 업데이트

    # 값 추가 
    new_favorite_food = '피자'  # 예시로 좋아하는 음식을 피자로 설정
    collection.update_one({'_id': doc['_id']}, {'$set': {'favorite_food': new_favorite_food}})
    print(f"Updated document with _id: {doc['_id']} to new age: {new_age}")

# MongoDB 서버와의 연결 종료
client.close()