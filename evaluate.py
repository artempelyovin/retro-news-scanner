import json
import logging
import math
import sqlite3
import argparse
from datetime import datetime
from typing import Any

import ollama

from config import config
from service import get_news_without_evaluation, get_prompt_by_id, add_news_evaluation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def process_and_evaluate_news(
    conn, prompt_template: str, news: tuple[Any, ...], ollama_model: str, max_news_content_len: int
) -> int:
    news_id, url, title, content, published_date, *_ = news

    if max_news_content_len and len(content) > max_news_content_len:
        content = content[: max_news_content_len - 3] + "..."
    prompt = prompt_template.format(title=title, content=content, published_date=published_date)

    start_time = datetime.now()
    response = ollama.generate(model=ollama_model, prompt=prompt)
    elapsed_seconds = (datetime.now() - start_time).seconds

    try:
        scores = json.loads(response["response"])
    except Exception:
        logging.exception(f"Ошибка парсинга JSON для новости id={news_id}:")
        return elapsed_seconds

    final_score = sum(score for score in scores.values()) / len(scores.values())  # mean score
    final_score = round(final_score, 2)

    try:
        add_news_evaluation(
            conn,
            news_id=news_id,
            model=ollama_model,
            prompt_id=args.prompt_id,
            scores=json.dumps(scores),
            final_score=final_score,
        )
    except Exception:
        logging.exception(f"Ошибка записи в БД для id={news_id}:")
    return elapsed_seconds


def main() -> None:
    conn = sqlite3.connect(config.database_file)

    prompt_template = get_prompt_by_id(conn, args.prompt_id)
    if not prompt_template:
        logging.error(f"Промпт с id={args.prompt_id} не найден")
        return

    logging.info(
        f"Старт обработки новостей с параметрами: prompt_id={args.prompt_id}, "
        f"model={args.ollama_model}, max_content_len={args.max_news_content_len}"
    )

    min_elapsed_time = math.inf
    max_elapsed_time = 0
    total_elapsed_time = 0
    processed_count = 1

    while True:
        news_batch = get_news_without_evaluation(conn)
        if not news_batch:
            break
        for news in news_batch:
            elapsed_time = process_and_evaluate_news(
                conn, prompt_template, news, args.ollama_model, args.max_news_content_len
            )
            if elapsed_time < min_elapsed_time:
                min_elapsed_time = elapsed_time
            if elapsed_time > max_elapsed_time:
                max_elapsed_time = elapsed_time
            total_elapsed_time += elapsed_time
            mean_time = round(total_elapsed_time / processed_count, 2)
            logging.info(
                f"[{processed_count}] Затрачено {elapsed_time} сек "
                f"(среднее: {mean_time} сек; лучшее: {min_elapsed_time} сек; худшее: {max_elapsed_time}) "
            )
            processed_count += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Обработка и оценка новостей с использованием Ollama")

    parser.add_argument("--prompt-id", type=int, required=True, help="ID промпта из базы данных")
    parser.add_argument("--ollama-model", type=str, required=True, help="Название модели Ollama для использования")
    parser.add_argument(
        "--max-news-content-len", type=int, default=None, help="Максимальная длина контента новости (по умолчанию: 800)"
    )
    args = parser.parse_args()
    main()
