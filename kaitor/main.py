from app_factory import create_app

app = create_app(db_uri="sqlite:///site.db")

if __name__=="__main__":
    app.run(debug=True)