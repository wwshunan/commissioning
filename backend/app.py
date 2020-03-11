from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from lattice import load_lattice

app = Flask(__name__)
app.config.from_object(__name__)

CORS(app, resources=r'/*')

@app.route('/lattice-setting', methods=['POST'])
def lattice_setting():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(f.filename))
        load_lattice(f.filename)
        return jsonify({'name': 'tell you'})
    #tw_file = request.form['file']
    #with open(tw_file) as f:
    #    text = f.read()
    #    print(text)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')



