# импорты
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from sqlalchemy import create_engine
from config import comunity_token, acces_token, db_url_object
from core import VkTools
from data_store import Base, add_user, check_user


class BotInterface():

    def __init__(self,comunity_token, acces_token, engine):
        self.interface = vk_api.VkApi(token=comunity_token)
        self.api = VkTools(acces_token)
        self.longpoll = VkLongPoll(self.interface)
        self.params = {}
        self.worksheets = []
        self.offset = 0
        self.engine = engine

    def message_send(self, user_id, message, attachment=None):
        self.interface.method('messages.send',
                                {'user_id': user_id,
                                'message': message,
                                'attachment': attachment,
                                'random_id': get_random_id()
                                }
                                )
        
    def event_handler(self):
        
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                command = event.text.lower()
                if command == 'привет':
                    self.params = self.api.get_profile_info(event.user_id)
                    self.message_send(event.user_id, f'Здравствуй {self.params["name"]}\n Для поиска анкет введите поиск')
                elif command == 'поиск':
                    if self.params.get("year") is None:
                        self.message_send(
                            event.user_id,
                            'Не удалось установить ваш возраст, пожалуйста укажите ваш возраст ",' ' Пример "возрст 25"')
                        continue
                    if self.params.get("relation") is None:
                        self.message_send(
                            event.user_id,
                            '''Не удалось установить ваше семейное полдожение\n
                                Пожалуйста укажите ваше Семейное положение\n 
                                1 — не женат/не замужем;\n
                                2 — есть друг/есть подруга;\n
                                3 — помолвлен/помолвлена;\n
                                4 — женат/замужем;\n
                                5 — всё сложно;\n
                                6 — в активном поиске;\n
                                7 — влюблён/влюблена;\n
                                8 — в гражданском браке;\n
                                Пример "статус 1"\n''')
                        continue
                    if self.params.get("city") is None:
                        self.message_send(
                            event.user_id,
                            'Не удалось определить ваш город, пожалуйста укажите ваш город,' ' Пример "город Москва"')
                        continue
                    self.message_send(event.user_id, 'Начинаем поиск')
                    if not self.worksheets:
                        self.worksheets = self.api.search_worksheet(
                            self.params, self.offset)
                    worksheet = None
                    new_worksheets = []
                    for worksheet in self.worksheets:
                        if not check_user(self.engine, event.user_id, worksheet['id']):
                            new_worksheets.append(worksheet)
                    self.worksheets = new_worksheets.copy()
                    worksheet = self.worksheets.pop(0)

                    photos = self.api.get_photos(worksheet['id'])
                    attachment = ''
                    for photo in photos:
                        attachment += f'photo{photo["owner_id"]}_{photo["id"]},'
                    self.offset += 10

                    self.message_send(
                        event.user_id,
                        f'Встречайте: {worksheet["name"]} ссылка: vk.com/id{worksheet["id"]}',
                        attachment=attachment
                    )
                    'добавить анкету в бд'
                    add_user(self.engine, event.user_id, worksheet['id'])

                elif  event.text.lower().startswith("возраст "):
                    age = event.text.lower().split()[1]
                    try:
                        age = int(age)
                    except ValueError:
                        self.message_send(
                            event.user_id, 'Необходимо ввести число')
                        continue
                    if not 14 <= age <= 70:
                        self.message_send(
                            event.user_id, 'Ваш возраст должен быть от 14 до 70 лет')
                        continue
                    self.params['year'] = age
                    self.message_send(
                        event.user_id, '''Вы успешно установили свой возраст\n Введите поиск повторно''')  
                    continue    
                elif  event.text.lower().startswith("статус "):
                    relation = event.text.lower().split()[1]
                    try:
                        relation = int(relation)
                    except ValueError:
                        self.message_send(
                            event.user_id, 'Необходимо ввести число')
                        continue
                    if not 1 <= relation <= 8:
                        self.message_send(
                            event.user_id, 'Ваш статус должен быть от 1 до 8 лет')
                        continue
                    self.params['relation'] = relation
                    self.message_send(
                        event.user_id, '''Вы успешно установили свой статус\n Введите поиск повторно''')
                    continue  
                elif event.text.lower().startswith("город "):
                    city_name = ' '.join(event.text.lower().split()[1:])
                    city = self.api.get_city(city_name)
                    if city is None:
                        self.message_send(
                            event.user_id, 'Не удалось найти такой город')
                    else:
                        self.params['city'] = city['title']
                        self.message_send(
                            event.user_id, f'''Вы успешно установили город {city["title"]}\n Введите поиск повторно''')
                elif command == 'пока':
                    self.message_send(event.user_id, 'Пока')
                else:
                    self.message_send(event.user_id, 'Команда не опознана')



if __name__ == '__main__':
    engine = create_engine(db_url_object)
    Base.metadata.create_all(engine)
    bot = BotInterface(comunity_token, acces_token, engine)
    bot.event_handler()