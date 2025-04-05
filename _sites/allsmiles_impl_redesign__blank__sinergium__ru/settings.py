from core.settings import *
from core.helpers import is_dev

# Сайт, который является шаблоном текущего
TEMPLATE_SITE = None

MEDIA_URL = '/media/allsmiles_impl_redesign__blank__sinergium__ru/'
MEDIA_ROOT = BASE_DIR / 'media/allsmiles_impl_redesign__blank__sinergium__ru'

# Query параметры, которые необходимо кэшировать
WHITE_QUERY_KEYS = ()

# Email'ы для заявок
if is_dev():
    MAIL_FROM = 'mailer-dev@sinergium.ru'
    MAIL_TO = ('mailer-dev@sinergium.ru',)
else:
    MAIL_FROM = 'noreply@allsmiles-impl-redesign.blank.sinergium.ru'

GOALS = {
    'ym': 'form-send',
    'gl': {
        'action': 'g-send',
        'category': 'g-form',
    }
}

GOALS_PIXEL = {
    'vk': 'submit_application',
}

# Добавлены ли файлы версии Б? True/False
B_FILE_AVAILABILITY = False

#meta-тег для Facebook
FACEBOOK_META_TAG = None
