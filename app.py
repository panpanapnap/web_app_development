from app import create_app

# 建立專案入口 app
app = create_app()

if __name__ == '__main__':
    # 以 debug 模式啟動本地伺服器
    app.run(debug=True)
