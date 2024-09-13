from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields, Namespace
from pymongo import MongoClient

# Flask 및 Flask-RESTx 설정
app = Flask(__name__) # Flask 객체 선언
api = Api(app, version='1.0', title='My API',
          description='LeeYS MongoDB API + Flask + Swagger') # Api(app) Flask 객체에 Api 객체 등록
user_ns = Namespace("user/", decorators="사용자 정보 조회/수정/추가/삭제") # Namespace 사용안하면 그냥 default로 들어감

# MongoDB 연결
client = MongoClient('mongodb://192.168.10.254:27018/') # 책임님 주소
# client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
collection = db['mycollection']

# 데이터 모델 정의 (Swagger에서 보여줄 필드 정의)
user_model = api.model('User', {
    'name': fields.String(required=True, description='이름'),
    'age': fields.Integer(required=True, description='나이'),
    'city': fields.String(required=True, description='사는 곳')
})

@api.route('/user')
class User(Resource):
    @api.doc('create_user') # doc은 설명용 기능구현과 관련 X
    @api.expect(user_model) # API 엔드포인트에서 클라이언트로부터 받을 데이터를 지정된 user_model에 따라 유효성 검사를 수행
    # DATA INSERT / POST = 등록
    def post(self):
        """유저 등록"""
        data = request.json
        collection.insert_one(data)  # MongoDB에 데이터 삽입
        return jsonify({'result': 'User created successfully'})

    # @api.doc('update_user')
    # @api.expect(user_model)
    # # PUT = 수정
    # def put(self):
    #     """유저 수정"""
    #     data = request.json
    #     query = {'name': data['name']}
    #     update_data = {"$set": data}
    #     result = collection.update_one(query, update_data)

    #     if result.matched_count == 0:
    #         return jsonify({'result': 'User not found'}), 404
    #     return jsonify({'result': 'User updated successfully'})

    @api.doc('delete_user')
    @api.param('name', 'The user name')
    # DATA DELETE / DELETE = 삭제 
    def delete(self):
        """유저 삭제"""
        name = request.args.get('name')
        result = collection.delete_one({'name': name})

        if result.deleted_count == 0:
            return jsonify({'result': 'User not found'}), 404
        return jsonify({'result': 'User deleted successfully'})
    
    # GET = 조회
    @api.doc('get_all_users')
    def get(self):
        """모든 유저 조회"""
        users = list(collection.find({}, {'_id': 0}))  # MongoDB에서 전체 유저 조회
        return jsonify(users)
    
# DATA SEARCH
@api.route('/user/<string:name>')
class UserByName(Resource):
    @api.doc('get_user_by_name')
    def get(self, name):
        """특정 유저 조회"""
        user = collection.find_one({'name': name}, {'_id': 0})  # 이름으로 유저 조회
        if user:
            return jsonify(user)
        else:
            return jsonify({'result': 'User not found'}), 404
            
# API 실행
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5555) # 0.0.0.0은 외부에서도 열려고
