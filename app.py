from flask import Flask, request, render_template, redirect, url_for, send_file, session
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

product_data = []
current_index = 0
skipped_indices = set()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    global product_data, current_index, skipped_indices
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            df = pd.read_excel(filepath)
            df = df[['SKU', 'ZSKU', 'TITLE', 'IMAGE-URLS']].copy()
            df['Price'] = None
            product_data = df.to_dict('records')
            current_index = 0
            skipped_indices = set()
            return redirect(url_for('entry'))
    return render_template('upload.html')

@app.route('/entry', methods=['GET', 'POST'])
def entry():
    global current_index, product_data, skipped_indices

    if request.method == 'POST':
        action = request.form.get('action')
        price = request.form.get('price')
        if action == 'save':
            if price:
                product_data[current_index]['Price'] = price
                if current_index in skipped_indices:
                    skipped_indices.remove(current_index)
        elif action == 'skip':
            skipped_indices.add(current_index)
        elif action == 'back':
            current_index = max(0, current_index - 1)
            return redirect(url_for('entry'))

        if current_index < len(product_data) - 1:
            current_index += 1
            return redirect(url_for('entry'))
        else:
            return redirect(url_for('complete'))

    if current_index < len(product_data):
        item = product_data[current_index]
        return render_template('entry.html', item=item, index=current_index + 1, total=len(product_data))
    return redirect(url_for('complete'))

@app.route('/complete')
def complete():
    return render_template('complete.html', skipped=len(skipped_indices))

@app.route('/export')
def export():
    df = pd.DataFrame(product_data)
    output_path = os.path.join(UPLOAD_FOLDER, 'priced_output.csv')
    df.to_csv(output_path, index=False)
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
