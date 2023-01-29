# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import HtmlResponse
from instaparser.items import InstaparserItem
import re
import json
from urllib.parse import urlencode
from copy import deepcopy


class InstagramSpider(scrapy.Spider):
    # атрибуты класса
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['https://instagram.com/']
    insta_login = 'nikojid870@farmdeu.com'
    insta_pwd = '#PWD_INSTAGRAM_BROWSER:10:1593966234:AWVQAEqi5e9XBd+R0Z/8dURO4TLB+XTvjbK9vBniYC8craN0BnmvX0SxrJo9HLJY9tKKTU8cly0oTbhc9kNxBLcQzAmlQXBut4oeOZ8lq7ebpJNUwNVbavxMciTeaiK2q/PR0gynHWOogpzIW+TGQ7So51hv8tKC21yIMgsABYoM3YlP6FTxdWHRWFlnhIVO'
    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    # usernames_to_parse = ['skills_lovers']  # Пользователь, у которого собираем посты. Можно указать список
    usernames_to_parse = ['qpaya__', 'mr_loser_0']  # Пользователь, у которого собираем посты. Можно указать список
    # usernames_to_parse = ['photo.me', 'datascience_enthusiast']  # Пользователь, у которого собираем посты. Можно указать список
    # usernames_to_parse = ['ai_machine_learning', 'learn.machinelearning', 'python.learning']  # Пользователь, у которого собираем посты. Можно указать список

    graphql_url = 'https://www.instagram.com/graphql/query/?'
    posts_hash = '15bf78a4ad24e33cbd838fdb31353ac1'  # hash для получения данных по постам с главной страницы
    user_followers_hash = 'c76146de99bb02f6415203be841dd25a'
    user_subscriptions_hash = 'd04b0a864b4b54837c0d870b0e77e076'

    def parse(self, response: HtmlResponse):  # Первый запрос на стартовую страницу
        csrf_token = self.fetch_csrf_token(response.text)  # csrf token забираем из html
        yield scrapy.FormRequest(  # заполняем форму для авторизации
            self.inst_login_link,
            method='POST',
            callback=self.open_userpage,
            formdata={
                'username': self.insta_login,
                'enc_password': self.insta_pwd
            },
            headers={
                'X-CSRFToken': csrf_token
            }
        )

    def open_userpage(self, response: HtmlResponse):
        j_body = json.loads(response.text)

        if j_body['authenticated']:  # Проверяем ответ после авторизации
            for username in self.usernames_to_parse:
                yield response.follow(
                    # Переходим на желаемую страницу пользователя. Сделать цикл для кол-ва пользователей больше двух
                    f'/{username}',
                    callback=self.parse_user_data,
                    cb_kwargs={'username': username}
                )

    def parse_user_data(self, response: HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)  # Получаем id пользователя

        variables = {                                          # Формируем словарь для передачи даных в запрос
            "id": user_id,
            "include_reel": True,
            "fetch_mutual": False,
            "first": 12                                        # 12 постов. Можно больше (макс. 50)
        }

        # Followers

        user_followers_url = f'{self.graphql_url}query_hash={self.user_followers_hash}&{urlencode(variables)}'
        # https://www.instagram.com/ai_machine_learning/followers/
        yield response.follow(
            user_followers_url,
            callback=self.parse_user_info,
            cb_kwargs={
                'username': username,
                'user_id': user_id,
                # 'variables': variables,
                'variables': deepcopy(variables),  # variables ч/з deepcopy во избежание гонок
                'followed_by': True
            }
        )

        # Subscriptions

        user_subscriptions_url = f'{self.graphql_url}query_hash={self.user_subscriptions_hash}&{urlencode(variables)}'
        # https://www.instagram.com/ai_machine_learning/following/
        yield response.follow(
            user_subscriptions_url,
            callback=self.parse_user_info,
            cb_kwargs={
                'username': username,
                'user_id': user_id,
                # 'variables': variables,
                'variables': deepcopy(variables),  # variables ч/з deepcopy во избежание гонок
                'followed_by': False  # +
            }
        )

    def parse_user_info(self, response: HtmlResponse, username, user_id, variables, followed_by):  # Принимаем ответ. Не забываем про параметры от cb_kwargs
        j_data = json.loads(response.text)

        page_info = j_data.get('data').get('user').get('edge_followed_by' if followed_by else 'edge_follow')

        if page_info is None:
            return

        page_info = page_info.get('page_info') if page_info is not None else None

        if page_info.get('has_next_page'):                           # Если есть следующая страница
            variables['after'] = page_info['end_cursor']             # Новый параметр для перехода на след. страницу

            user_followers_url = f'{self.graphql_url}query_hash={self.user_followers_hash}&{urlencode(variables)}'

            yield response.follow(
                user_followers_url,
                callback=self.parse_user_info,
                cb_kwargs={
                    'username': username,
                    'user_id': user_id,
                    # 'variables': variables
                    'variables': deepcopy(variables)  # variables ч/з deepcopy во избежание гонок
                }
            )

        users = j_data.get('data').get('user').get('edge_followed_by' if followed_by else 'edge_follow').get('edges')  # Сами подписчики
        for user in users:  # Перебираем подписчиков, собираем данные
            item = InstaparserItem(
                user_id=user.get('node').get('id'),
                user_name=user.get('node').get('username'),
                full_name=user.get('node').get('full_name'),
                photo=user.get('node').get('profile_pic_url'),
                is_followed_by=user_id if followed_by else None,
                follows=None if followed_by else user_id
            )

            yield item  # В пайплайн

    # Получаем токен для авторизации

    def fetch_csrf_token(self, text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    # Получаем id желаемого пользователя
    def fetch_user_id(self, text, username):
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
        ).group()
        return json.loads(matched).get('id')
