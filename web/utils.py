import urllib2, urllib
import json
import os
import string
import random
import re
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.core.files.temp import NamedTemporaryFile
from tinypng import shrink_file
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.http import urlquote
from tinypng.api import shrink_data
from django.conf import settings
from api.raw import raw_information, raw_information_n

from cStringIO import StringIO
import sys

class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout

def shrinkImageFromData(data):
    api_key = settings.TINYPNG_API_KEY
    info, new_data = shrink_data(data, api_key)
    img_shrunked = NamedTemporaryFile(delete=False)
    img_shrunked.write(new_data)
    img_shrunked.flush()
    return ImageFile(img_shrunked)

def shrunkImage(picture, filename):
    api_key = settings.TINYPNG_API_KEY
    if not api_key or not filename.endswith('.png'):
        return picture
    img_shrunked = NamedTemporaryFile(delete=False)
    shrink_info = shrink_file(
            picture.name,
            api_key=api_key,
            out_filepath=img_shrunked.name
    )
    img_shrunked.flush()
    return ImageFile(img_shrunked)

def send_email(subject, template_name, to=[], context={}, from_email=settings.AWS_SES_RETURN_PATH):
    context = Context(context)
    plaintext = get_template('emails/' + template_name + '.txt').render(context)
    htmly = get_template('emails/' + template_name + '.html').render(context)
    email = EmailMultiAlternatives(subject, plaintext, from_email, to)
    email.attach_alternative(htmly, "text/html")
    email.send()

class HttpRedirectException(Exception):
    pass

def is_positive_integer(string):
    try:
        integer = int(string)
        if integer < 0:
            return False
    except ValueError:
        return False
    return True

def concat_args(*args):
    return u'\"' + u'","'.join([unicode(value).replace('"','\"') for value in args]) + u'\"'

def chibiimage(idol, small=True):
    prefix = 'small_' if small else ''
    if idol is not None:
        if idol in raw_information and 'chibi' in raw_information[idol]:
            if small:
                return random.choice(raw_information[idol]['chibi'])[0].replace('chibi/', 'chibi/small_')
            return random.choice(raw_information[idol]['chibi'])[0]
        if idol in raw_information_n and 'chibi' in raw_information_n[idol]:
            if small:
                return random.choice(raw_information_n[idol]['chibi'])[0].replace('chibi/', 'chibi/small_')
            return random.choice(raw_information_n[idol]['chibi'])[0]
    return 'http://i.schoolido.lu/static/idols/chibi/' + prefix + idol.replace(' ', '_').replace('\'', '-') + '.png'

def randomString(length, choice=(string.ascii_letters + string.digits)):
    return ''.join(random.SystemRandom().choice(choice) for _ in range(length))

def get_imgur_code(url):
    return re.compile(settings.IMGUR_REGEXP).match(url).group('imgur')

def get_parameters_to_string(request):
    return '?' + '&'.join([p[0] + '=' + p[1] for p in request.GET.items()])

def tourldash(string):
    return ''.join(e if e.isalnum() else '-' for e in string)

def singlecardurl(card):
    return urlquote(u'/cards/{}/{}-{}{}{}{}-{}/'.format(
        card.id,
        card.rarity,
        tourldash(card.name),
        '-' + tourldash(card.translated_collection) if card.translated_collection else '',
        '-promo' if card.is_promo else '',
        '-event' if card.event_id else '',
        card.attribute))
