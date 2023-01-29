# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from pymongo import MongoClient, errors


class InstaparserPipeline:
    def __init__(self):                             # Конструктор, где инициализируем подключение к СУБД
        client = MongoClient('localhost', 27017)
        self.mongo_base = client.instagram

    def add_to_db(self, item, collection_name):
        collection = self.mongo_base[collection_name]  # Выбираем коллекцию по имени паука
        collection.update_one({'_id': item['_id']}, {'$set': item}, upsert=True)  # Добавляем в базу данных
        pass

    def process_item(self, item, spider):
        collection_name = spider.name  # Выбираем коллекцию по имени паука
        user = {
            '_id': item['user_id'],
            'user_id': item['user_id'],
            'user_name': item['user_name'],
            'full_name': item['full_name'],
            'photo': item['photo'],
            'is_followed_by': item['is_followed_by'],
            'follows': item['follows']
        }

        self.add_to_db(user, collection_name)

        return item
