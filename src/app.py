from flask import Flask, render_template
import os

import settings
from api import ApiClient

app = Flask(__name__)

app.config["api"] = ApiClient(f"{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")


@app.route("/")
def home():
    api = app.config["api"]
    return render_template(
        "index.html",
        name=api.sayHello("Gonzalo"),
        items=api.getAll(length=10),
        items2=api.getStream(length=5)
    )
