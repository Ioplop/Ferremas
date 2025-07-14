from app import create_app
from flask import send_file
import os

app = create_app()

@app.route('/')
def index():
    # Ruta absoluta al archivo index.html
    ruta = os.path.join(os.getcwd(), 'app', 'static', 'index.html')
    return send_file(ruta)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
