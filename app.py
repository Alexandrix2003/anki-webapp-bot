import os
import genanki
from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from google import genai  # Новый официальный SDK

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Инициализация клиента нового SDK (автоматически подхватит GEMINI_API_KEY из переменных окружения)
client = genai.Client()

# Создаем шаблон карточки Anki
anki_model = genanki.Model(
    1607392319,
    "Telegram Vocab Model",
    fields=[
        {"name": "Word"},
        {"name": "Translation"},
        {"name": "Definition"},
    ],
    templates=[
        {
            "name": "Card 1",
            "fmt": (
                "<b>Слово:</b> {{Word}}<br><br><b>Перевод:</b>"
                " {{Translation}}<br><br><b>Контекст:</b> {{Definition}}"
            ),
        },
    ],
)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})


@app.post("/translate")
async def translate_word(word: str = Form(...)):
  prompt = (
      f"Переведи слово '{word}' на русский язык, дай краткое определение и"
      " пример использования на английском с переводом. Формат строго: Перевод"
      " | Определение и пример"
  )

  try:
    # Запрос через актуальный метод нового SDK
    response = client.models.generate_content(
        model="gemini-2.5-flash",  # Или gemini-1.5-flash / gemini-2.0-flash
        contents=prompt,
    )
    ai_text = response.text

    parts = ai_text.split("|")
    translation = parts[0].strip() if len(parts) > 0 else "Перевод"
    definition = parts[1].strip() if len(parts) > 1 else ai_text

  except Exception as e:
    translation = "Ошибка генерации"
    definition = str(e)
    ai_text = f"Ошибка: {e}"

  # Создаем файл карточки Anki (.apkg)
  deck_id = 2059400110
  deck = genanki.Deck(deck_id, "Telegram WebApp Vocab")
  note = genanki.Note(
      model=anki_model, fields=[word, translation, definition]
  )
  deck.add_note(note)

  filename = f"{word.replace(' ', '_')}.apkg"
  genanki.Package(deck).write_to_file(filename)

  return {
      "word": word,
      "translation": ai_text,
      "download_url": f"/download/{filename}",
  }


@app.get("/download/{filename}")
async def download_apkg(filename: str):
  file_path = filename
  if os.path.exists(file_path):
    return FileResponse(
        file_path, media_type="application/octet-stream", filename=filename
    )
  return {"error": "Файл не найден"}
