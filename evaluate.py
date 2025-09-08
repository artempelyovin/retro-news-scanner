import json
import logging
import sqlite3
from datetime import datetime

import ollama

from config import config
from service import get_news_without_evaluation, get_prompt_by_id, add_news_evaluation

PROMPT_ID = 3
MODEL = "qwen2.5:3b-instruct-q4_K_M"
MAX_CONTENT_LENGTH = 800

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def main() -> None:
    conn = sqlite3.connect(config.database_file)

    prompt = get_prompt_by_id(conn, PROMPT_ID)
    if not prompt:
        logging.error(f"Промпт с id={PROMPT_ID} не найден")
        return

    logging.info("Старт обработки новостей")

    while True:
        news_batch = get_news_without_evaluation(conn)

        for news in news_batch:
            news_id, url, title, content, published_date, *_ = news
            cut_title = title[:80] if len(title) > 80 else title
            logging.info(f"Обработка новости '{cut_title}' (id={news_id})")

            if len(content) > MAX_CONTENT_LENGTH:
                logging.info(
                    f"Текст статьи будет обрезан на {len(content) - MAX_CONTENT_LENGTH} сим. до {MAX_CONTENT_LENGTH}"
                )
                content = content[:MAX_CONTENT_LENGTH]
            current_prompt = prompt.format(title=title, content=content, published_date=published_date)

            start_time = datetime.now()
            response = ollama.generate(model=MODEL, prompt=current_prompt, keep_alive=0)
            elapsed_time = datetime.now() - start_time

            try:
                scores = json.loads(response["response"])
            except Exception:
                logging.exception(f"Ошибка парсинга JSON для новости id={news_id}:")
                continue

            final_score = sum(score for score in scores.values()) / len(scores.values())  # mean score
            final_score = round(final_score, 2)

            try:
                add_news_evaluation(
                    conn,
                    news_id=news_id,
                    model=MODEL,
                    prompt_id=PROMPT_ID,
                    scores=json.dumps(scores),
                    final_score=final_score,
                )

                logging.info(f"Вердикт за {elapsed_time.seconds} сек.: {final_score} ({scores})")
            except Exception:
                logging.exception(f"Ошибка записи в БД для id={news_id}:")


if __name__ == "__main__":
    main()
