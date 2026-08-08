import os
import subprocess
import uuid
import json
import os, signal
import re
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from flask import Flask, request, render_template, redirect, send_from_directory,jsonify
from pathlib import Path
#from langdetect import detect
#from deep_translator import GoogleTranslator


app = Flask(__name__)
IMAGE_DIR = 'static/images'

# ensure image directory exists at import time to avoid FileNotFoundError in routes
os.makedirs(IMAGE_DIR, exist_ok=True)

LOCK_FILE = '/tmp/generate.lock'

from zoneinfo import ZoneInfo

# タイムゾーン取得部分を安全に固定する
def get_local_timezone():
    return ZoneInfo("Asia/Tokyo")

local_tz = get_local_timezone()

@app.route('/lock_status')
def lock_status():
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE) as f:
            pid_str = f.read().strip()
        started_at = os.path.getmtime(LOCK_FILE)

        is_running = False
        if pid_str.isdigit():
            pid = int(pid_str)
            try:
                # シグナル0を送ることで、プロセスが生存しているか確認（エラーが出なければ生存）
                os.kill(pid, 0)
                is_running = True
            except OSError:
                is_running = False

        if is_running:
            return jsonify({
                'locked': True,
                'started_at': started_at
            })
        else:
            # プロセスが死んでいたらロックファイルを削除
            try:
                os.remove(LOCK_FILE)
            except Exception:
                pass
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

    try:
        with open(json_files[0]) as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return jsonify({"error": "JSONファイルが壊れています"})
    except Exception as e:
        return jsonify({"error": f"メタデータの読み込みエラー: {str(e)}"})

    return jsonify(data)

@app.route('/')
def index():
    image_entries = []
    for image_file in sorted(os.listdir(IMAGE_DIR), reverse=True):
        if image_file.endswith(".png"):
            json_file = os.path.join(IMAGE_DIR, image_file + '.json')
            metadata = {}
            if os.path.exists(json_file):
                try:
                    with open(json_file) as f:
                        metadata = json.load(f)
                except json.JSONDecodeError:
                    print(f"[JSONエラー] {json_file}: JSONファイルが壊れています")
                except Exception as e:
                    print(f"[メタデータエラー] {json_file}: {str(e)}")
            image_entries.append({
                "filename": image_file,
                "metadata": metadata
            })

    for entry in image_entries:
        try:
            # ファイル名から日時を取得（naive → aware に変換）
            base_name = os.path.basename(entry['filename'])
            name_part = os.path.splitext(base_name)[0]
            start_time = datetime.strptime(name_part, '%Y-%m-%d_%H%M%S')
            start_time = start_time.replace(tzinfo=local_tz)

# JSON 側
            end_time_str = entry['metadata'].get('created_at')
            if end_time_str:
                # 末尾の 'Z' を '+00:00' に置換して Python 3.9 でも安全に読めるようにする
                if end_time_str.endswith('Z'):
                    end_time_str = end_time_str[:-1] + '+00:00'
                
                end_time = datetime.fromisoformat(end_time_str)
                
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)
                end_time = end_time.astimezone(local_tz)

                delta = end_time - start_time
                seconds = int(delta.total_seconds())
                hrs = str(seconds // 3600).zfill(2)
                mins = str((seconds % 3600) // 60).zfill(2)
                secs = str(seconds % 60).zfill(2)
                entry['metadata']['duration'] = f"{hrs}:{mins}:{secs}"
            else:
                entry['metadata']['duration'] = "不明"
        except Exception as e:
            entry['metadata']['duration'] = "不明"
            print(f"[生成時間エラー] {entry['filename']}: {e}")

    #デフォルトフォーム値を設定
    prompt = request.args.get('prompt', '')
    negative_prompt = request.args.get('negative_prompt', '')
    steps = request.args.get('steps', '1')
    image_width_str = request.args.get("image_width", "512").strip()
    image_height_str = request.args.get("image_height", "512").strip()

    # int()変換前に値が数字かチェック
    image_width = int(image_width_str) if image_width_str.isdigit() else 512
    image_height = int(image_height_str) if image_height_str.isdigit() else 512

    return render_template(
        'index.html',
        image_entries=image_entries,
        prompt=prompt,
        negative_prompt=negative_prompt,
        steps=steps,
        image_width=image_width,
        image_height=image_height
     )

@app.route("/cancel", methods=["POST"])
def cancel_generation():
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE) as f:
            content = f.read().strip()
        
        is_running = False
        pid = 0
        if content.isdigit():
            pid = int(content)
            try:
                os.kill(pid, 0)
                is_running = True
            except OSError:
                is_running = False

        if is_running:
            try:
                os.kill(pid, signal.SIGTERM)
                return jsonify({"status": "killed", "pid": pid})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)})
        else:
            try:
                os.remove(LOCK_FILE)
            except Exception:
                pass
            return jsonify({"status": "invalid_pid_or_not_running"})
    else:
        return jsonify({"status": "no_pidfile"})

@app.route('/handle_form', methods=['POST'])
def handle_form():
    action = request.form.get('action')
    prompt = request.form.get('prompt', '') or ''
    # 1. 改行(\r\n, \n, \r)をすべて半角スペース（または空文字）に置換
    prompt = prompt.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')

    # 2. ダブルクォーテーションを全角（” または ＂）に置換（シングルも同様に）
    prompt = prompt.replace('"', '”').replace("'", "’")

    negative_prompt = request.form.get('negative_prompt', '') or ''
    steps = request.form.get('steps', '1') or '1'
    image_width = request.form.get('image_width', '512') or '512'
    image_height = request.form.get('image_height', '512') or '512'

    if action == 'generate':
        filename = datetime.now().strftime("%Y-%m-%d_%H%M%S.png")
        filepath = os.path.join(IMAGE_DIR, filename)
        json_path = filepath + '.json'

        # JSON を安全に書き出す（禁則文字は json モジュールがエスケープする）
        metadata = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": steps,
            "width": str(image_width),
            "height": str(image_height),
            "created_at": datetime.now(local_tz).isoformat()
        }

        def write_json_safely(path, data):
            temp_path = path + '.tmp'
            try:
                with open(temp_path, 'w', encoding='utf-8') as jf:
                    json.dump(data, jf, ensure_ascii=False, indent=2)
                os.replace(temp_path, path)  # アトミックな書き込み
                return True
            except Exception as e:
                app.logger.exception("JSON書き込みエラー: %s", e)
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                return False

        # 初期メタデータの書き込み
        if not write_json_safely(json_path, metadata):
            return redirect('/')  # エラーが発生した場合は早期リターン

        try:
            # generate_image.sh が終了したタイミングで再度タイムスタンプを更新する
            subprocess.run(["bash", "generate_image.sh", filepath, prompt, negative_prompt, steps, image_width, image_height], check=False)
            metadata['created_at'] = datetime.now(local_tz).isoformat()
            write_json_safely(json_path, metadata)
        except Exception as e:
            app.logger.exception("generate_image.sh failed: %s", e)

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
