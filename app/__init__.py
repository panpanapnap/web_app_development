import os
from flask import Flask

def create_app(test_config=None):
    # 初始化 Flask 應用程式並設定 instance 目錄位置
    app = Flask(__name__, instance_relative_config=True)
    
    # 載入基本設定
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DATABASE=os.path.join(app.instance_path, 'database.db'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # 確保 instance folder 存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 註冊 Blueprints
    from app.routes.events import events_bp
    from app.routes.registrations import registrations_bp

    app.register_blueprint(events_bp)
    app.register_blueprint(registrations_bp)

    return app

def init_db():
    from app.models.database import get_db_connection
    conn = get_db_connection()
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database Initialized Successfully.")
