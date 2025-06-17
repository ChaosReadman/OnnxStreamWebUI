from flask import Flask, request, render_template, redirect, send_from_directory
import os
import subprocess
import uuid
import json

app = Flask(__name__)
IMAGE_DIR = 'static/images'
CONFIG_DIR = 'config'
LOCK_FILE = 'generate.lock'

def is_locked():
    """Check if the generation process is locked."""
    return os.path.exists(LOCK_FILE)

@app.route('/lock_status')
def lock_status():
    return {'locked': is_locked()}

@app.route('/')
def index():
    images = os.listdir(IMAGE_DIR)
    images.sort(reverse=True)

    config_files=[f for f in os.listdir(CONFIG_DIR) if f.endswith('.json')]
    #デフォルトフォーム値を設定
    prompt = request.args.get('prompt', '')
    negative_prompt = request.args.get('negative_prompt', '')
    steps = request.args.get('steps', '1')

    return render_template(
        'index.html',
        images=images,
        config_files=config_files,
        prompt=prompt,
        negative_prompt=negative_prompt,
        steps=steps,
        locked=is_locked(),
     )

@app.route('/load_config', methods=['POST'])
def load_config():
    config_name = request.form.get('config_name')
    config_path = os.path.join(CONFIG_DIR, config_name)
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        return redirect(f"/?prompt={config_data['prompt']}&negative_prompt={config_data['negative_prompt']}&steps={config_data['steps']}")
    return redirect('/')

@app.route('/delete_config', methods=['POST'])
def delete_config():
    config_name = request.form.get('config_name')
    config_path = os.path.join(CONFIG_DIR, config_name)
    if os.path.exists(config_path):
        os.remove(config_path)
    return redirect('/')

@app.route('/handle_form', methods=['POST'])
def handle_form():
    action = request.form.get('action')
    prompt = request.form.get('prompt')
    negative_prompt = request.form.get('negative_prompt')
    steps = request.form.get('steps', '1')
    config_name = request.form.get('config_name')

    if action == 'generate':
        if is_locked():
            return redirect('/?error=locked')

        # filename = f"{uuid.uuid4()}.png"
        filename = datetime.now().strftime("%Y-%m-%d_%H%M%S.png")
        filepath = os.path.join(IMAGE_DIR, filename)
        subprocess.run(["bash", "generate_image.sh", filepath, prompt, negative_prompt, steps])
        return redirect(f"/?prompt={prompt}&negative_prompt={negative_prompt}&steps={steps}")
        # return redirect('/')

    elif action == 'save_config' and config_name:
        config = {
            'prompt': prompt,
            'negative_prompt': negative_prompt,
            'steps': steps
        }
        config_path = os.path.join(CONFIG_DIR, f"{config_name}.json")
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return redirect('/')

    return redirect('/')

@app.route('/delete/<filename>')
def delete_image(filename):
    filepath = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect('/')

@app.route('/download/<filename>')
def download_image(filename):
    return send_from_directory(IMAGE_DIR, filename,as_attachment=True)

if __name__ == '__main__':
    os.makedirs(IMAGE_DIR, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)

