from scrapy.crawler import CrawlerProcess                     # Импортируем класс для создания процесса
from scrapy.settings import Settings                          # Импортируем класс для настроек

from instaparser import settings                              # Наши настройки
from instaparser.spiders.instagram import InstagramSpider     # Класс паука
from pymongo import MongoClient
from pprint import pprint


client = MongoClient('localhost', 27017)
mongo_base = client.instagram
collection = mongo_base['instagram']

if __name__ == '__main__':
    crawler_settings = Settings()                             # Создаем объект с настройками
    crawler_settings.setmodule(settings)                      # Привязываем к нашим настройкам
    process = CrawlerProcess(settings=crawler_settings)       # Создаем объект процесса для работы
    process.crawl(InstagramSpider)                            # Добавляем нашего паука
    process.start()                                           # Пуск

for item in collection.find({}):
    pprint(item)
print(f'Всего в базе данных {collection.count_documents({})} записи')
collection.drop()  # удаляем БД для очистки памяти ! Опционально - в целях обучения
