# -*- coding: utf-8 -*-

import pymongo

from django.conf import settings


class MongoClient(pymongo.MongoClient):
    pass 

client = pymongo.MongoClient(settings.MONGODB_HOST, settings.MONGODB_PORT)
db = client[settings.MONGODB_NAME]
