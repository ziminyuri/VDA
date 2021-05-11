# Verbal-Decision-Analysis
Вербальный анализ решений. ШНУР, ПАРК

Для старта оптимальнее использовать:
`gunicorn --workers=5 Verbal_Decision_Analysis.wsgi`

Необходимо запустить Redis
`redis-server`

Запустить Celery
`celery -A Verbal_Decision_Analysis worker -l INFO 
`
Запуск просмотра задач Celery
`celery flower -A Verbal_Decision_Analysis --address=127.0.0.1 --port=5555`



