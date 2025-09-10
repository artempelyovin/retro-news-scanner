# retro-news-scanner

### Примеры запуска:

```shell
python evaluate.py --prompt-id=3 --ollama-model=qwen2.5:7b-instruct-q4_K_M
```

С обрезкой новостей до 800 символов (экономия токенов и ускорение ответов):

```shell
python evaluate.py --prompt-id=3 --ollama-model=qwen2.5:3b-instruct-q4_K_M --max-news-content-len=800
```

