"""``python -m sweetpea_gui`` starts the server and opens the GUI in a browser."""

import threading
import webbrowser

import uvicorn

from .server import app

PORT = 8765

threading.Timer(1.0, webbrowser.open, ["http://127.0.0.1:{}".format(PORT)]).start()
uvicorn.run(app, host="127.0.0.1", port=PORT)
