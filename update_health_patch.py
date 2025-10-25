import os, re

APP_FILE = "app.py"

if not os.path.exists(APP_FILE):
    print(f"❌ File not found: {APP_FILE}")
else:
    with open(APP_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем, есть ли уже /health
    if '@app.route("/health")' in content:
        print("✅ Endpoint /health already exists.")
    else:
        # Добавляем endpoint перед последней строкой с if __name__ ...
        pattern = r'if\s+__name__\s*==\s*["\']__main__["\']\s*:'
        replacement = (
            '\n\n@app.route("/health")\n'
            'def health():\n'
            '    return {"status": "ok"}, 200\n\n'
            + r'if __name__ == "__main__":'
        )

        new_content, count = re.subn(pattern, replacement, content)
        if count == 0:
            print("⚠️ Не удалось найти место для вставки, добавляем в конец файла.")
            new_content = content + (
                '\n\n@app.route("/health")\n'
                'def health():\n'
                '    return {"status": "ok"}, 200\n'
            )

        with open(APP_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("✅ /health endpoint added to app.py")

print("Done. You can delete this file after deployment.")
