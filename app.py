from flask import Flask, request, render_template, redirect, send_from_directory,jsonify
import os
import subprocess
import uuid
import json
import os, signal
from datetime import datetime


app = Flask(__name__)
IMAGE_DIR = 'static/images'

LOCK_FILE = '/tmp/generate.lock'


@app.route('/lock_status')
def lock_status():
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE) as f:
            pid = f.read().strip()
        started_at = os.path.getmtime(LOCK_FILE)

        if pid.isdigit() and os.path.exists(f"/proc/{pid}"):
            return jsonify({
                'locked': True,
                'started_at': started_at
            })
        else:
            os.remove(LOCK_FILE)
    return jsonify({'locked': False})

@app.route('/latest_metadata')
def latest_metadata():
    import os, json
    from glob import glob

    json_files = sorted(
        glob('static/images/*.json'),
        key=os.path.getmtime,
        reverse=True
    )

    if not json_files:
        return jsonify({})

    with open(json_files[0]) as f:
        data = json.load(f)

    return jsonify(data)

@app.route('/')
def index():
    image_entries = []
    for image_file in sorted(os.listdir(IMAGE_DIR), reverse=True):
        if image_file.endswith(".png"):
            json_file = os.path.join(IMAGE_DIR, image_file + '.json')
            metadata = {}
            if os.path.exists(json_file):
                with open(json_file) as f:
                    metadata = json.load(f)
            image_entries.append({
                "filename": image_file,
                "metadata": metadata
            })
    #デフォルトフォーム値を設定
    prompt = request.args.get('prompt', '')
    negative_prompt = request.args.get('negative_prompt', '')
    steps = request.args.get('steps', '1')
    image_width = request.args.get("image_width", "512").strip()
    image_height = request.args.get("image_height", "512").strip()

    return render_template(
        'index.html',
        image_entries=image_entries,
        prompt=prompt,
        negative_prompt=negative_prompt,
        steps=steps,
        image_width=int(image_width),
        image_height=int(image_height)
     )

@app.route("/cancel", methods=["POST"])
def cancel_generation():

    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE) as f:
            pid = int(f.read())
        try:
            os.kill(pid, signal.SIGTERM)
            return jsonify({"status": "killed", "pid": pid})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    else:
        return jsonify({"status": "no_pidfile"})

@app.route('/handle_form', methods=['POST'])
def handle_form():
    action = request.form.get('action')
    prompt = request.form.get('prompt')
    negative_prompt = request.form.get('negative_prompt')
    steps = request.form.get('steps', '1')
    image_width = request.form.get('image_width', '512')
    image_height = request.form.get('image_height', '512')

    if action == 'generate':
        filename = datetime.now().strftime("%Y-%m-%d_%H%M%S.png")
        filepath = os.path.join(IMAGE_DIR, filename)
        subprocess.run(["bash", "generate_image.sh", filepath, prompt, negative_prompt, steps, image_width, image_height])

    return redirect(f"/?prompt={prompt}&negative_prompt={negative_prompt}&steps={steps}&image_width={image_width}&image_height={image_height}")

@app.route('/delete/<filename>')
def delete_image(filename):
    filepath = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    if os.path.exists(filepath + ".json"):
        os.remove(filepath + ".json")
    return redirect('/')

@app.route('/download/<filename>')
def download_image(filename):
    return send_from_directory(IMAGE_DIR, filename,as_attachment=True)

if __name__ == '__main__':
    os.makedirs(IMAGE_DIR, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)

