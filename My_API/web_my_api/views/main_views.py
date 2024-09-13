from flask import Blueprint, redirect, jsonify
# Response, request => HTML 응답 요청을 처리하기 위함 
# render_template => HTML 파일을 렌더링
from flask import Flask, render_template, Response, request

bp = Blueprint("main", __name__, url_prefix="/")

# 데코레이터 
@bp.route("/")
def index():
    return render_template("index.html")

# 정적 수어 인식 SSLR 
@bp.route("/SSLR")
def SSLR():
    return render_template("SSLR.html")

# 독립 수어 인식 ISLR
@bp.route("/ISLR")
def ISLR():
    return render_template("ISLR.html")
