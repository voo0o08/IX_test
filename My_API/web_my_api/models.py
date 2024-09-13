# ## 모듈 로딩 --------------------------------------------------
# from my_web import db
# from datetime import datetime


# ## Translation 테이블 클래스 ---------------------------------------
# ## 컬럼 : id, original_text, translation_text, create_date
# class Translation(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     original_text = db.Column(db.Text(), nullable=False)
#     translation_text = db.Column(db.Text(), nullable=False)
#     create_date = db.Column(db.DateTime(), nullable=False, default=datetime.now())
