import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import requests

#НАСТРОЙКИ

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

OPENROUTER_MODELS = [
    "tngtech/deepseek-r1t-chimera:free",
    "openai/gpt-oss-120b:free",
    "google/gemma-3-27b-it:free",
    "z-ai/glm-4.5-air:free"
]

LANGUAGES = {
    "English": "English",
    "German": "German",
    "French": "French",
    "Russian": "Russian"
}

GENRES = [
    "Fantasy",
    "Science Fiction (Sci-Fi)",
    "Mystery",
    "Thriller",
    "Romance",
    "Horror",
    "Historical Fiction",
    "Young Adult (YA)",
    "Dystopian",
    "Adventure",
    "Crime",
    "Drama",
    "Contemporary Fiction",
    "Nonfiction",
    "Biography",
    "Autobiography",
    "Self-Help",
    "Classic Literature",
    "Graphic Novels",
    "Paranormal",
    "Urban Fantasy",
    "Literary Fiction",
    "Psychological Thriller",
    "Epic Fantasy",
    "Dark Fantasy"
]

#ЛОГИКА

def split_text_by_paragraphs(text, max_len):
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue

        if len(current) + len(p) + 2 <= max_len:
            current = p if not current else current + "\n\n" + p
        else:
            chunks.append(current)
            current = p

    if current:
        chunks.append(current)

    return chunks


def translate_openrouter(chunk, target_lang, api_key, model, genres,):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are a professional translator. "
                    f"Translate the text to {target_lang}. "
                    f"Translate while preserving the author's style. Preserve paragraphs and formatting exactly. Do not add any explanations. Don't add any extra comments, just send the translated text in response and nothing else. Observe the style of the genre {genres}"
                )
            },
            {"role": "user", "content": chunk}
        ],
        "temperature": 0.5
    }

    r = requests.post(
        OPENROUTER_API_URL,
        json=payload,
        headers=headers,
        timeout=90
    )

    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code}")

    data = r.json()
    text = data["choices"][0]["message"]["content"]

    if not text:
        raise Exception("Empty response")

    return text


#GUI

selected_file = None


def open_file():
    global selected_file
    selected_file = filedialog.askopenfilename(
        filetypes=[("Text files", "*.txt")]
    )
    if selected_file:
        file_label.config(text=selected_file)


def save_file(text):
    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt")]
    )
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        messagebox.showinfo("Готово", f"Файл сохранён:\n{path}")


def start_translation():
    threading.Thread(target=translate).start()


def translate():
    if not selected_file:
        messagebox.showerror("Ошибка", "Файл не выбран")
        return

    api_key = api_entry.get().strip()
    if not api_key:
        messagebox.showerror("Ошибка", "Введите OpenRouter API ключ")
        return

    try:
        max_len = int(chunk_entry.get())
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный размер чанка")
        return

    target_lang = lang_var.get()

    with open(selected_file, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = split_text_by_paragraphs(text, max_len)
    translated = []

    progress["maximum"] = len(chunks)
    progress["value"] = 0

    for i, chunk in enumerate(chunks):
        success = False

        for model in OPENROUTER_MODELS:
            try:
                result = translate_openrouter(
                    chunk, target_lang, api_key, model
                )
                translated.append(result)
                success = True
                break
            except Exception:
                continue

        if not success:
            translated.append("[TRANSLATION FAILED]")

        root.after(0, lambda v=i + 1: progress.config(value=v))

    save_file("\n\n".join(translated))

#ОКНО

root = tk.Tk()
root.title("AI Translator (OpenRouter)")
root.geometry("620x520")

tk.Label(root, text="Translator", font=("Arial", 18)).pack(pady=10)

tk.Button(root, text="Выбрать файл", command=open_file).pack()
file_label = tk.Label(root, text="Файл не выбран", wraplength=500)
file_label.pack(pady=5)

tk.Label(root, text="Стартовая модель").pack()
model_var = tk.StringVar(value=OPENROUTER_MODELS[0])
tk.OptionMenu(root, model_var, *OPENROUTER_MODELS).pack()

tk.Label(root, text="Язык перевода").pack()
lang_var = tk.StringVar(value="Russian")
tk.OptionMenu(root, lang_var, *LANGUAGES.keys()).pack()

tk.Label(root, text="Жанр").pack()
genres = tk.StringVar(value="Fantasy")
tk.OptionMenu(root, genres, *GENRES).pack()

tk.Label(root, text="Макс. символов в чанке").pack()
chunk_entry = tk.Entry(root)
chunk_entry.insert(0, "2000")
chunk_entry.pack()

tk.Label(root, text="OpenRouter API Key").pack()
api_entry = tk.Entry(root, width=50)
api_entry.pack()

tk.Button(root, text="Перевести", command=start_translation).pack(pady=10)

progress = ttk.Progressbar(root, length=420)
progress.pack(pady=10)

root.mainloop()
