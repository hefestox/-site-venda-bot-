import os
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder=".")

PORT = int(os.environ.get("PORT", 8080))


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
