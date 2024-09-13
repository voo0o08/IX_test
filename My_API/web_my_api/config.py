import os

BASE_DIR = os.path.dirname(__file__)
DB_MANE_SQLITE = "app.db"

## 다양한 DBMS URI
DB_MYSQL_URI = "mysql+pymysql://root:kdt5@1.251.203.204:33065/Team4_TranslateDB"

## 사용할 DBMS 설정/ SQLALCHEMY_시작 변수명 고정
SQLALCHEMY_DATABASE_URI = DB_MYSQL_URI
# SQLALCHEMY_TRACK_MODIFICATIONS = False
