import os
from flask import Flask, request, jsonify, render_template_string
from groq import Groq
from duckduckgo_search import DDGS

app = Flask(__name__)

# Инициализация клиента Groq из переменной окружения GROQ_API_KEY
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Системный промпт по умолчанию
SYSTEM_PROMPT = """Ты — Halva AI, умный и дружелюбный ассистент. 
Отвечай грамотно, четко и по делу. Если к запросу приложены результаты поиска, используй их для актуального ответа."""

# Список актуальных моделей Groq
AVAILABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "deepseek-r1-distill-llama-70b",
    "llama-3.1-8b-instant"
]

def search_duckduckgo(query):
    """Функция поиска через DuckDuckGo"""
    try:
        results = []
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=3))
            for r in search_results:
                results.append(f"Заголовок: {r.get('title')}\nОписание: {r.get('body')}")
        return "\n\n".join(results)
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return None

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Halva AI</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #fff; margin: 0; padding: 20px; }
        .chat-container { max-width: 600px; margin: 0 auto; display: flex; flex-direction: column; height: 90vh; }
        .messages { flex: 1; overflow-y: auto; border: 1px solid #333; padding: 15px; border-radius: 8px; background: #1e1e1e; }
        .msg { margin-bottom: 15px; line-height: 1.4; }
        .msg.user { color: #4da6ff; text-align: right; }
        .msg.bot { color: #e1e1e1; text-align: left; }
        .input-area { display: flex; gap: 10px; margin-top: 15px; }
        input[type="text"] { flex: 1; padding: 12px; border-radius: 6px; border: 1px solid #444; background: #2a2a2a; color: #fff; }
        select { padding: 10px; border-radius: 6px; background: #2a2a2a; color: #fff; border: 1px solid #444; }
        button { padding: 12px 20px; border: none; border-radius: 6px; background: #0084ff; color: #fff; font-weight: bold; cursor: pointer; }
        button:disabled { background: #555; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>Halva AI</h2>
        <div style="margin-bottom: 10px;">
            <label>Модель: </label>
            <select id="model-select">
                {% for model in models %}
                    <option value="{{ model }}">{{ model }}</option>
                {% endfor %}
            </select>
            <label style="margin-left: 15px;">
                <input type="checkbox" id="web-search"> Включить поиск в сети
            </label>
        </div>
        <div class="messages" id="messages"></div>
        <div class="input-area">
            <input type="text" id="user-input" placeholder="Введите сообщение..." onkeydown="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()" id="send-btn">Отправить</button>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('user-input');
            const btn = document.getElementById('send-btn');
            const messages = document.getElementById('messages');
            const model = document.getElementById('model-select').value;
            const useWeb = document.getElementById('web-search').checked;

            const text = input.value.trim();
            if (!text) return;

            // Добавляем сообщение пользователя
            messages.innerHTML += `<div class="msg user"><b>Вы:</b> ${text}</div>`;
            input.value = '';
            btn.disabled = true;
            messages.scrollTop = messages.scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, model: model, web_search: useWeb })
                });
                const data = await response.json();
                
                if (data.error) {
                    messages.innerHTML += `<div class="msg bot" style="color: #ff5555;"><b>Ошибка:</b> ${data.error}</div>`;
                } else {
                    messages.innerHTML += `<div class="msg bot"><b>Halva AI:</b> ${data.response}</div>`;
                }
            } catch (err) {
                messages.innerHTML += `<div class="msg bot" style="color: #ff5555;"><b>Ошибка сети</b></div>`;
            }

            btn.disabled = false;
            messages.scrollTop = messages.scrollHeight;
        }
    </script>
</body>
</html>
    """, models=AVAILABLE_MODELS)

@app.route("/admin-lol2010", methods=["GET", "POST"])
def admin():
    global SYSTEM_PROMPT
    message = ""
    if request.method == "POST":
        SYSTEM_PROMPT = request.form.get("prompt", SYSTEM_PROMPT)
        message = "Системный промпт успешно обновлен!"

    return render_template_string("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Админ-панель - Halva AI</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #fff; padding: 40px; }
        textarea { width: 100%; height: 200px; background: #2a2a2a; color: #fff; border: 1px solid #444; padding: 10px; border-radius: 6px; }
        button { padding: 10px 20px; background: #28a745; color: #fff; border: none; border-radius: 6px; cursor: pointer; margin-top: 10px; }
        .msg { color: #00ff66; margin-bottom: 10px; }
    </style>
</head>
<body>
    <h2>Панель управления Halva AI</h2>
    {% if message %}<div class="msg">{{ message }}</div>{% endif %}
    <form method="POST">
        <label>Системный промпт:</label><br><br>
        <textarea name="prompt">{{ prompt }}</textarea><br>
        <button type="submit">Сохранить</button>
    </form>
    <br>
    <a href="/" style="color: #4da6ff;">← На главную</a>
</body>
</html>
    """, prompt=SYSTEM_PROMPT, message=message)

@app.route("/api/chat", methods=["POST"])
def chat_api():
    data = request.json or {}
    user_message = data.get("message", "")
    selected_model = data.get("model", "llama-3.3-70b-versatile")
    use_web = data.get("web_search", False)

    if not user_message:
        return jsonify({"error": "Пустой запрос"}), 400

    messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Поиск в веб
    if use_web:
        search_data = search_duckduckgo(user_message)
        if search_data:
            context = f"Результаты поиска из интернета:\n{search_data}\n\nЗапрос пользователя: {user_message}"
            messages_payload.append({"role": "user", "content": context})
        else:
            messages_payload.append({"role": "user", "content": user_message})
    else:
        messages_payload.append({"role": "user", "content": user_message})

    try:
        completion = client.chat.completions.create(
            model=selected_model,
            messages=messages_payload,
            temperature=0.7
        )
        bot_response = completion.choices[0].message.content
        return jsonify({"response": bot_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
