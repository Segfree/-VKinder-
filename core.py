from datetime import datetime 
from pprint import pprint
import vk_api
from vk_api.exceptions import ApiError
from config import acces_token



class VkTools():
    def __init__(self, acces_token):
       self.api = vk_api.VkApi(token=acces_token)

    def _bdate_toyear (self, bdate):
        user_year = bdate.split('.')[2]
        now = datetime.now().year
        return now - int(user_year)

    def get_profile_info(self, user_id):

        try:
            info, = self.api.method('users.get',
                                {'user_id': user_id,
                                'fields': 'city,bdate,sex,relation' 
                                }
                                )
        except ApiError:
            info = {}
            print(f'Error = {"Сервис VK недоступен"}')

        result = {'name': (info['first_name'] + ' '+ info['last_name']) if 
                    'first_name' in info and 'last_name' in info else None,
                     'year': self._bdate_toyear(info.get('bdate')) if info.get('bdate') is not None else None,
                     'sex': info.get('sex'), 
                     'city': info.get('city')['title'] if info.get('city') is not None else None, 
                     'relation' : info.get('relation') if info.get('relation') is not None else None
                     }
        return result
    
    def get_city(self, city_name):
        try:
            cities = self.api.method('database.getCities',
                                       {
                                         'q': city_name,
                                         'count': 1
                                       }
                                       )
            if len(cities['items']) > 0:
                return cities['items'][0]
        except ApiError:
            print(f'error = {"Сервис VK недоступен"}')
    
    def search_worksheet(self, params, offset):
        try:
            users = self.api.method('users.search',
                                {'count': 50,
                                 'offset' : offset,
                                 'hometown' : params['city'],
                                 'sex' : 1 if params['sex'] == 2 else 2,
                                 'has_photo' : True,
                                 'age_from' : params['year'] - 3,
                                 'age_to' : params['year'] + 3
                                }
                                )
        except ApiError:
            info = {}
            print(f'Error = {"Сервис VK недоступен"}')

        result = [{'name' : item ['first_name'] + ' ' + item ['last_name'],
                   'id' : item ['id'] 
                  } for item in users ['items'] if item ['is_closed'] is False
                 ]
        return result
    
    def get_photos(self, id):

        try:
            photos = self.api.method('photos.get',
                                {'owner_id': id,
                                'album_id': 'profile',
                                'extended' : 1
                                }
                                )
        except ApiError:
            photos = {}
            print(f'Error = {"Сервис VK недоступен"}')

        result = [{'owner_id' : item['owner_id'],
                   'id' : item['id'],
                   'likes' : item['likes']['count'],
                   'comments' : item['comments']['count']
                   } for item in photos['items']
                   ]
        #отсортировать по лайкам и коментам
        result = sorted(result, key=lambda x: (x['likes'], x['comments']), reverse=True)
        return result
    

if __name__ == '__main__':
    user_id = 125733018
    bot = VkTools(acces_token)
    params = bot.get_profile_info(user_id)
    worksheets = bot.search_worksheet(params, 1)
    worksheet = worksheets.pop()
    photos = bot.get_photos(worksheet['id'])
    
    pprint(worksheets) 