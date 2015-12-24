#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  api.py
#
#  Copyright 2015 D.H. Bahr <dhbahr@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import requests
import simplejson

from exceptions import AccessError, ValidationError, UnauthorizedError


class _Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args,
                                                                  **kwargs)
        return cls._instances[cls]


class Storage(object):
    _instances = {}

    def drop_instance(self, cls, key):
        raise NotImplementedError

    def get_instance(self, cls, key):
        raise NotImplementedError

    def set_instance(self, cls, key, instance):
        raise NotImplementedError


class _InternalStorage(Storage):

    def drop_instance(self, cls, key):
        Storage._instances.get(cls, {}).pop(key)

    def get_instance(self, cls, key):
        return Storage._instances.get(cls, {}).get(key, None)

    def set_instance(self, cls, key, instance):
        assert issubclass(cls, CenitModel), \
            "Class %s must be subclass of CenitModel" % (cls,)
        assert isinstance(instance, CenitModel), \
            "Object %s must be instance of CenitModel" % (instance,)

        if cls not in Storage._instances:
            Storage._instances[cls] = {}
        Storage._instances[cls][key] = instance


class _RawV1(object):

    __metaclass__ = _Singleton

    DEFAULT_SCHEME = "https"
    DEFAULT_HOST = "cenithub.com"
    DEFAULT_PATH = "api/v1"

    PUSH_HOOK = "setup/push"

    def __init__(self, host=None, port=None, path=None, ssl=True, verify=True,
                 storage=None):
        self.__host = host or _RawV1.DEFAULT_HOST
        self.__port = port
        self.__path = path or _RawV1.DEFAULT_PATH
        self.__scheme = _RawV1.DEFAULT_SCHEME if ssl else "http"

        self.__verify = verify

        self.__key = None
        self.__token = None

        self.__storage = None
        self.set_storage(storage)

    def __get_url(self, hook):
        return "{scheme}://{host}{port}/{path}/{hook}".format(
            scheme=self.__scheme,
            host=self.__host,
            port="" if not self.__port else ":{}".format(self.__port),
            path=self.__path,
            hook=hook,
        )

    def __get_headers(self):
        headers = {'Content-Type': 'application/json'}

        if self.__key and self.__token:
            headers.update({
                'X-User-Access-Key': self.__key,
                'X-User-Access-Token': self.__token,
            })

        return headers

    def set_credentials(self, key, token):
        self.__key = key
        self.__token = token

    def unset_credentials(self):
        self.__key = None
        self.__token = None

    def set_storage(self, storage):
        if storage is not None:
            assert issubclass(storage, Storage), \
                "Class %s must be subclass of %s" % (storage, Storage)
        else:
            storage = _InternalStorage()

        self.__storage = storage

    def drop_instance(self, cls, key):
        return self.__storage.drop_instance(cls, key)

    def get_instance(self, cls, key):
        return self.__storage.get_instance(cls, key)

    def set_instance(self, cls, key, instance):
        return self.__storage.set_instance(cls, key, instance)

    def get(self, path, params=None):
        url = self.__get_url(path)
        headers = self.__get_headers()

        try:
            r = requests.get(url, params=params, headers=headers)
        except Exception as e:
            raise AccessError()

        if 200 <= r.status_code < 300:
            return r.json()

        try:
            error = r.json()
        except Exception as e:
            raise ValidationError()

        if 400 <= error.get('code', 400) < 500:
            raise AccessError()

        raise ValidationError()

    def post(self, path, values):
        url = self.__get_url(path)
        headers = self.__get_headers()
        payload = simplejson.dumps(values)

        print("[POST] %s ? %s (%s)" % (url, payload, headers))
        try:
            r = requests.post(url, data=payload, headers=headers)
        except Exception as e:
            raise AccessError()

        if 200 <= r.status_code < 300:
            return r.json()

        try:
            error = r.json()
        except Exception as e:
            raise ValidationError()

        code = error.get('code', 400)
        if 400 <= code < 500:
            if code == 401:
                raise UnauthorizedError()
            raise AccessError()

        raise ValidationError()

    def put(self, path, values):
        url = self.__get_url(path)
        headers = self.__get_headers()
        payload = simplejson.dumps(values)

        try:
            r = requests.put(url, data=payload, headers=headers)
        except Exception as e:
            raise AccessError()

        if 200 <= r.status_code < 300:
            return r.json()

        try:
            error = r.json()
        except Exception as e:
            raise ValidationError()

        if 400 <= error.get('code', 400) < 500:
            raise AccessError()

        raise ValidationError()

    def delete(self, path):
        url = self.__get_url(path)
        headers = self.__get_headers()

        try:
            r = requests.delete(url, headers=headers)
        except Exception as e:
            raise AccessError()

        if 200 <= r.status_code < 300:
            return True

        try:
            error = r.json()
        except Exception as e:
            raise ValidationError()

        print ("[DELETE] Error:", error)

        if 400 <= error.get('code', 400) < 500:
            raise AccessError()

        raise ValidationError()


def register_custom_cenit(host=None, port=None, path=None, ssl=True,
                          verify=True):
    _RawV1(host, port, path, ssl, verify)


def get_cenit_client():
    return _RawV1()


def use_credentials(key, token):
    client = get_cenit_client()
    client.set_credentials(key, token)


class CenitModel(object):

    api_client = None

    root = None
    properties = []

    def __init__(self, name, id_=None, namespace=None):
        self.__id = None
        self.id = id_

        self.name = name
        self.namespace = namespace

    @property
    def id(self):
        """Object's ID on the Cenit Platform"""
        return self.__id

    @id.setter
    def id(self, id_):
        if not CenitModel.api_client:
            CenitModel.api_client = get_cenit_client()
        client = CenitModel.api_client

        self.__id = id_
        if id_:
            client.set_instance(self.__class__, id_, self)
            # self.__class__._instances[id_] = self

    def to_dict(self, referenced=False):
        def _serialize(value):
            if isinstance(value, CenitModel):
                ref = value.id not in (None, False)
                rc_ = value.to_dict(ref)
            elif isinstance(value, list):
                rc_ = []
                for v in value:
                    rc_.append(_serialize(v))
            else:
                rc_ = value
            return rc_

        data = vars(self)

        rc = {}
        if referenced:
            rc.update({
                "id": self.id,
                "_reference": True
            })
            return rc

        for attr in data:
            if not data[attr]:
                continue

            prop = attr.rpartition("__")[-1]
            if prop not in self.properties:
                continue

            rc[prop] = _serialize(data[attr])
        return rc

    def push(self):
        payload = self.to_dict()

        if not CenitModel.api_client:
            CenitModel.api_client = get_cenit_client()
        client = CenitModel.api_client

        hook = "setup/{}".format(self.root)
        rc = client.post(hook, payload)
        print "[PUSH] RC:", rc

        if rc.get('success', False):
            self.id = rc['success'][self.root]['id']
        else:
            return False

        return True

    def drop(self):
        if not CenitModel.api_client:
            CenitModel.api_client = get_cenit_client()
        client = CenitModel.api_client

        hook = "setup/{}/{}".format(self.root, self.id)
        rc = client.delete(hook)
        print "[DROP] RC:", rc
        if rc:
            self._del()
            client.drop_instance(self.__class__, self.id)

        return rc

    @classmethod
    def fetch(cls, **filters):
        if not CenitModel.api_client:
            CenitModel.api_client = get_cenit_client()
        client = CenitModel.api_client

        hook = "setup/{}".format(cls.root)
        rc = client.get(hook, filters)

        print "[FETCH] RC:", rc
        objects = cls.from_values(rc[cls.root])
        return objects

    @classmethod
    def get_instance(cls, id_):
        if not CenitModel.api_client:
            CenitModel.api_client = get_cenit_client()
        client = CenitModel.api_client

        return client.get_instance(cls, id_)
        # return cls._instances.get(id_, None)

    @classmethod
    def from_values(cls, values):
        raise NotImplementedError

    @staticmethod
    def _sluggify(name):
        return name.lower().replace(" ", "_")

    @staticmethod
    def _namify(slug):
        return slug.replace("_", " ").title()

    def _del(self):
        raise NotImplementedError

    def __repr__(self):
        return "<%s [%s]: '%s | %s'>" % (
            self._namify(self.root),
            getattr(self, "id", None),
            getattr(self, "namespace", ''),
            getattr(self, "name", '')
        )

    def __eq__(self, other):
        return (self.__class__ == other.__class__) and \
               (self.id == other.id) and \
               (self.name == other.name)
