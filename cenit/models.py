#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  models.py
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

from .api import CenitModel


################################################################################
# Collections
################################################################################

# TODO: Collections


################################################################################
# Data definitions
################################################################################

class Library(CenitModel):

    root = 'library'
    properties = ['id', 'name', 'slug']

    def __init__(self, name, slug=None, id_=None):
        super(Library, self).__init__(name, id_=id_)
        self.__schemas = []
        self.__data_types = []

        if slug:
            self.slug = slug
        else:
            self.slug = Library._sluggify(name)

    @property
    def schemas(self):
        return self.__schemas[:]

    @schemas.setter
    def schemas(self, value):
        for schema in self.__schemas:
            self.remove_schema(schema)

        if not value:
            return

        assert isinstance(value, list), \
            "'Schemas' attribute must be a list"
        assert all(isinstance(x, Schema) for x in value), \
            "All elements of 'Schemas' must be " \
            "instance of %s" % (Schema,)

        for schema in value:
            self.append_schema(schema)

    def append_schema(self, schema):
        assert isinstance(schema, Schema), \
            "Object %s is not a Cenit Schema" % (schema,)

        rc = schema not in self.__schemas
        if rc:
            self.__schemas.append(schema)
        return rc

    def remove_schema(self, schema):
        assert isinstance(schema, Schema), \
            "Object %s is not a Cenit Schema" % (schema,)

        rc = schema in self.__schemas
        if rc:
            self.__schemas.remove(schema)
        return rc

    @property
    def data_types(self):
        return self.__data_types[:]

    @data_types.setter
    def data_types(self, value):
        for dt in self.__data_types:
            self.remove_data_type(dt)

        if not value:
            return

        assert isinstance(value, list), \
            "'Data types' attribute must be a list"
        assert all(isinstance(x, DataType) for x in value), \
            "All elements of 'Data Types' must be " \
            "instance of %s" % (DataType,)

        for dt in value:
            self.append_data_type(dt)

    def append_data_type(self, data_type):
        assert isinstance(data_type, DataType), \
            "Object %s is not a Cenit Data type" % (data_type,)

        rc = data_type not in self.__data_types
        if rc:
            self.__data_types.append(data_type)
        return rc

    def remove_data_type(self, data_type):
        assert isinstance(data_type, DataType), \
            "Object %s is not a Cenit Data type" % (data_type,)

        rc = data_type in self.__data_types
        if rc:
            print "\tRemoving %s" % (data_type, )
            self.__data_types.remove(data_type)
        return rc

    @classmethod
    def from_values(cls, values):
        rc = []
        for entry in values:
            name = entry.get('name')
            slug = entry.get('slug', None)
            id_ = entry.get('id', None)

            library = Library(name, slug=slug, id_=id_)

            Schema.from_values(entry.get('schemas', []))
            DataType.from_values(entry.get('data_types', []))

            rc.append(library)

        return rc

    def _del(self):
        return

    def __repr__(self):
        return "<%s [%s]: '%s'>" % (
            self._namify(self.root),
            getattr(self, "id", None),
            getattr(self, "name", '')
        )


class Schema(CenitModel):

    root = 'schema'
    properties = ['id', 'library', 'uri', 'schema']

    def __init__(self, library, uri, schema, id_=None):
        super(Schema, self).__init__(uri, id_=id_, namespace=library.name)

        self.__library = None

        self.library = library
        self.uri = uri
        self.schema = schema

    @property
    def library(self):
        return self.__library

    @library.setter
    def library(self, value):
        assert isinstance(value, Library), \
            "Object %s is not a Cenit Library" % (value,)
        if self.__library is not None:
            self.__library.remove_schema(self)
        value.append_schema(self)
        self.__library = value

    @classmethod
    def from_values(cls, values):
        rc = []
        for entry in values:
            library = Library.get_instance(
                entry.get('library', {}).get('id', None))
            uri = entry.get('uri')
            schema = entry.get('slug', None)
            id_ = entry.get('id', None)

            rc.append(cls(library, uri, schema, id_=id_))

        return rc

    def _del(self):
        self.__library.remove_schema(self)


class DataType(CenitModel):

    root = 'data_type'

    def __init__(self, library, name, title=None, slug=None, id_=None):
        super(DataType, self).__init__(name, id_=id_, namespace=library.name)

        self.__library = None

        self.library = library
        self.slug = slug or DataType._sluggify(name.split(".")[0])
        self.title = title or DataType._namify(self.slug)

        self._type = None

    @property
    def library(self):
        return self.__library

    @library.setter
    def library(self, value):
        assert isinstance(value, Library), \
            "Object %s is not a Cenit Library" % (value,)
        if self.__library is not None:
            self.__library.remove_data_type(self)
        value.append_data_type(self)
        self.__library = value

    def push(self):
        if not self._type:
            raise NotImplementedError()
        return super(DataType, self).push()

    @classmethod
    def from_values(cls, values):
        sub = {
            "Setup::FileDataType": FileDataType,
            "Setup::SchemaDataType": SchemaDataType,
        }
        rc = []
        for entry in values:
            dt = sub.get(entry.get("_type")).from_values([entry])
            rc.extend(dt)
        return rc

    def _del(self):
        self.__library.remove_data_type(self)


class SchemaDataType(DataType):
    root = 'schema_data_type'
    properties = ['id', 'library', 'name', 'schema', 'title', 'slug', '_type']

    def __init__(self, library, name, schema, title=None, slug=None, id_=None):
        super(SchemaDataType, self).__init__(library, name, title=title,
                                             slug=slug, id_=id_)
        self.schema = schema
        self._type = "Setup::SchemaDataType"

    @classmethod
    def from_values(cls, values):
        rc = []
        for entry in values:
            library = Library.get_instance(
                entry.get('library', {}).get('id', None))
            name = entry.get('name')
            schema = entry.get('schema')
            title = entry.get('title', None)
            slug = entry.get('slug', None)
            id_ = entry.get('id', None)

            rc.append(
                cls(library, name, schema, title=title, slug=slug, id_=id_))

        return rc
    
    def _del(self):
        return super(SchemaDataType, self)._del()


class FileDataType(DataType):
    root = 'file_data_type'

    def __init__(self, library, name, title=None, slug=None, id_=None):
        super(FileDataType, self).__init__(library, name, title=title,
                                           slug=slug, id_=id_)

        self._type = "Setup::FileDataType"

    @classmethod
    def from_values(cls, values):
        rc = []
        for entry in values:
            library = Library.get_instance(
                entry.get('library', {}).get('id', None))
            name = entry.get('name')
            title = entry.get('title', None)
            slug = entry.get('slug', None)
            id_ = entry.get('id', None)

            rc.append(
                cls(library, name, title=title, slug=slug, id_=id_))

        return rc
    
    def _del(self):
        return super(FileDataType, self)._del()


################################################################################
# Setup
################################################################################

class Parameter(CenitModel):
    root = 'parameter'
    properties = ['id', 'key', 'value']

    def __init__(self, key, value, id_=None):
        super(Parameter, self).__init__(key, id_=id_)

        self.key = key
        self.value = value

    @classmethod
    def from_values(cls, values):
        rc = []
        for entry in values:
            key = entry.get('key')
            value = entry.get('value')
            id_ = entry.get('id')
            rc.append(cls(key, value, id_=id_))

        return rc

    def _del(self):
        pass

    def __repr__(self):
        return "<%s [%s]: '%s'>" % (
            self._namify(self.root),
            getattr(self, "id", None),
            getattr(self, "name", '')
        )


class Connection(CenitModel):
    root = "connection"
    properties = ['id', 'namespace', 'name', 'url', 'number', 'token',
                  'parameters', 'headers', 'template_parameters']

    def __init__(self, name, url, namespace=None, parameters=None, headers=None,
                 template_parameters=None, id_=None, number=None, token=None):
        super(Connection, self).__init__(name, id_=id_, namespace=namespace)

        self.__parameters = []
        self.__headers = []
        self.__template_parameters = []
        self.__connection_roles = []

        self.url = url
        self.number = number
        self.token = token
        self.parameters = parameters or []
        self.headers = headers or []
        self.template_parameters = template_parameters or []

    @property
    def parameters(self):
        return self.__parameters[:]

    @parameters.setter
    def parameters(self, value):
        if not value:
            self.__parameters = []
            return

        assert isinstance(value, list), "'Parameters' attribute must be a list"
        assert all(isinstance(x, Parameter) for x in value), \
            "All elements of 'Parameters' must be instance of %s" % (Parameter,)

        self.__parameters = value

    @property
    def headers(self):
        return self.__headers[:]

    @headers.setter
    def headers(self, value):
        if not value:
            self.__headers = []
            return

        assert isinstance(value, list), "'Headers' attribute must be a list"
        assert all(isinstance(x, Parameter) for x in value), \
            "All elements of 'Headers' must be instance of %s" % (Parameter,)

        self.__headers = value

    @property
    def template_parameters(self):
        return self.__template_parameters[:]

    @template_parameters.setter
    def template_parameters(self, value):
        if not value:
            self.__template_parameters = []
            return

        assert isinstance(value, list), \
            "'Template Parameters' attribute must be a list"
        assert all(isinstance(x, Parameter) for x in value), \
            "All elements of 'Template Parameters' must be " \
            "instance of %s" % (Parameter,)

        self.__template_parameters = value

    @property
    def connection_roles(self):
        return self.__connection_roles[:]

    @connection_roles.setter
    def connection_roles(self, value):
        for role in self.__connection_roles:
            self.remove_connection_role(role)

        if not value:
            return

        assert isinstance(value, list), \
            "'Connection roles' attribute must be a list"
        assert all(isinstance(x, ConnectionRole) for x in value), \
            "All elements of 'Connection Roles' must be " \
            "instance of %s" % (ConnectionRole,)

        for role in value:
            self.append_connection_role(role)

    def append_connection_role(self, role):
        assert isinstance(role, ConnectionRole), \
            "Object %s is not a Cenit Connectio Role"

        rc = role not in self.__connection_roles
        if rc:
            self.__connection_roles.append(role)
            if self not in role.connections:
                role.append_connection(self)

        return rc

    def remove_connection_role(self, role):
        assert isinstance(role, ConnectionRole), \
            "Object %s is not a Cenit Connectio Role"

        rc = role in self.__connection_roles
        if rc:
            self.__connection_roles.remove(role)
            if self in role.connections:
                role.remove_connection(self)

        return rc

    @classmethod
    def from_values(cls, values):
        rc = []

        for entry in values:
            id_ = entry.get('id', None)
            namespace = entry.get('namespace')
            name = entry.get('name')
            url = entry.get('url')
            number = entry.get('number')
            token = entry.get('token')

            parameters = Parameter.from_values(entry.get('parameters', []))
            headers = Parameter.from_values(entry.get('headers', []))
            template_parameters = Parameter.from_values(
                entry.get('template_parameters', []))

            conn = cls(name, url, namespace=namespace, parameters=parameters,
                       headers=headers, template_parameters=template_parameters,
                       id_=id_, number=number, token=token)
            rc.append(conn)
        return rc

    def _del(self):
        for role in self.__connection_roles:
            role.remove_connection(self)


class WebhookMethod:
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    PATCH = 'patch'
    DELETE = 'delete'
    COPY = 'copy'
    HEAD = 'head'
    OPTIONS = 'options'
    LINK = 'link'
    UNLINK = 'unlink'
    PURGE = 'purge'
    LOCK = 'lock'
    UNLOCK = 'unlock'
    PROPFIND = 'propfind'


class Webhook(CenitModel):
    root = "webhook"
    properties = ['id', 'namespace', 'name', 'path', 'method']

    def __init__(self, name, path, method, namespace=None, parameters=None,
                 headers=None, template_parameters=None, id_=None):
        super(Webhook, self).__init__(name, id_=id_, namespace=namespace)

        self.path = path
        self.__method = None
        self.__parameters = []
        self.__headers = []
        self.__template_parameters = []
        self.__connection_roles = []

        self.method = method
        self.parameters = parameters or []
        self.headers = headers or []
        self.template_parameters = template_parameters or []

    @property
    def method(self):
        return self.__method

    @method.setter
    def method(self, value):
        assert value in vars(WebhookMethod).values(), \
            "'Method' must be one of %s" % (WebhookMethod,)
        self.__method = value

    @property
    def parameters(self):
        return self.__parameters[:]

    @parameters.setter
    def parameters(self, value):
        if not value:
            self.__parameters = []
            return

        assert isinstance(value, list), "'Parameters' attribute must be a list"
        assert all(isinstance(x, Parameter) for x in value), \
            "All elements of 'Parameters' must be instance of %s" % (Parameter,)

        self.__parameters = value

    @property
    def headers(self):
        return self.__headers[:]

    @headers.setter
    def headers(self, value):
        if not value:
            self.__headers = []
            return

        assert isinstance(value, list), "'Headers' attribute must be a list"
        assert all(isinstance(x, Parameter) for x in value), \
            "All elements of 'Headers' must be instance of %s" % (Parameter,)

        self.__headers = value

    @property
    def template_parameters(self):
        return self.__template_parameters[:]

    @template_parameters.setter
    def template_parameters(self, value):
        if not value:
            self.__template_parameters = []
            return

        assert isinstance(value, list), \
            "'Template Parameters' attribute must be a list"
        assert all(isinstance(x, Parameter) for x in value), \
            "All elements of 'Template Parameters' must be " \
            "instance of %s" % (Parameter,)

        self.__template_parameters = value

    @property
    def connection_roles(self):
        return self.__connection_roles[:]

    @connection_roles.setter
    def connection_roles(self, value):
        for role in self.__connection_roles:
            self.remove_connection_role(role)

        if not value:
            return

        assert isinstance(value, list), \
            "'Connection roles' attribute must be a list"
        assert all(isinstance(x, ConnectionRole) for x in value), \
            "All elements of 'Connection Roles' must be " \
            "instance of %s" % (ConnectionRole,)

        for role in value:
            self.append_connection_role(role)

    def append_connection_role(self, role):
        assert isinstance(role, ConnectionRole), \
            "Object %s is not a Cenit Connectio Role"

        rc = role not in self.__connection_roles
        if rc:
            self.__connection_roles.append(role)
            if self not in role.webhooks:
                role.append_webhook(self)

        return rc

    def remove_connection_role(self, role):
        assert isinstance(role, ConnectionRole), \
            "Object %s is not a Cenit Connectio Role"

        rc = role in self.__connection_roles
        if rc:
            self.__connection_roles.remove(role)
            if self in role.webhooks:
                role.remove_webhook(self)

        return rc

    @classmethod
    def from_values(cls, values):
        rc = []

        for entry in values:
            id_ = entry.get('id', None)
            namespace = entry.get('namespace')
            name = entry.get('name')
            path = entry.get('path')
            method = entry.get('method')

            parameters = Parameter.from_values(entry.get('parameters', []))
            headers = Parameter.from_values(entry.get('headers', []))
            template_parameters = Parameter.from_values(
                entry.get('template_parameters', []))

            conn = cls(name, path, method, namespace=namespace,
                       parameters=parameters, headers=headers,
                       template_parameters=template_parameters, id_=id_)
            rc.append(conn)
        return rc

    def _del(self):
        for role in self.__connection_roles:
            role.remove_webhook(self)


class ConnectionRole(CenitModel):
    root = "connection_role"
    properties = ['id', 'namespace', 'name', 'webhooks', 'connections']

    def __init__(self, name, namespace=None, webhooks=None, connections=None,
                 id_=None):
        super(ConnectionRole, self).__init__(name, namespace=namespace, id_=id_)

        self.__webhooks = []
        self.__connections = []

        self.webhooks = webhooks or []
        self.connections = connections or []

    @property
    def webhooks(self):
        return self.__webhooks[:]

    @webhooks.setter
    def webhooks(self, value):
        for hook in self.__webhooks:
            self.remove_webhook(hook)

        if not value:
            return

        assert isinstance(value, list), \
            "'Webhooks' attribute must be a list"
        assert all(isinstance(x, Webhook) for x in value), \
            "All elements of 'Webhooks' must be " \
            "instance of %s" % (Webhook,)

        for hook in value:
            self.append_webhook(hook)

    def append_webhook(self, webhook):
        assert isinstance(webhook, Webhook), \
            "Object %s is not a Cenit Webhook" % (webhook,)

        rc = webhook not in self.__webhooks
        if rc:
            self.__webhooks.append(webhook)
            if self not in webhook.connection_roles:
                webhook.append_connection_role(self)

        return rc

    def remove_webhook(self, webhook):
        assert isinstance(webhook, Webhook), \
            "Object %s is not a Cenit Webhook" % (webhook,)

        rc = webhook in self.__webhooks
        if rc:
            self.__webhooks.remove(webhook)
            if self in webhook.connection_roles:
                webhook.remove_connection_role(self)

        return rc

    @property
    def connections(self):
        return self.__connections[:]

    @connections.setter
    def connections(self, value):
        for conn in self.__connections:
            self.remove_connection(conn)

        if not value:
            return

        assert isinstance(value, list), \
            "'Connections' attribute must be a list"
        assert all(isinstance(x, Connection) for x in value), \
            "All elements of 'Connections' must be " \
            "instance of %s" % (Connection,)

        for conn in value:
            self.append_connection(conn)

    def append_connection(self, connection):
        assert isinstance(connection, Connection), \
            "Object %s is not a Cenit Connection" % (connection,)

        rc = connection not in self.__connections
        if rc:
            self.__connections.append(connection)
            if self not in connection.connection_roles:
                connection.append_connection_role(self)

        return rc

    def remove_connection(self, connection):
        assert isinstance(connection, Connection), \
            "Object %s is not a Cenit Connection" % (connection,)

        rc = connection in self.__connections
        if rc:
            self.__connections.remove(connection)
            if self in connection.connection_roles:
                connection.remove_connection_role(self)

        return rc

    @classmethod
    def from_values(cls, values):
        rc = []

        for entry in values:
            id_ = entry.get('id', None)
            namespace = entry.get('namespace')
            name = entry.get('name')

            connections = Connection.from_values(entry.get('connections', []))
            webhooks = Webhook.from_values(entry.get('webhooks', []))

            conn = cls(name, namespace=namespace,
                       connections=connections, webhooks=webhooks, id_=id_)
            rc.append(conn)
        return rc

    def _del(self):
        pass


class Event(CenitModel):
    root = "event"

    def __init__(self, name, namespace=None, id_=None):
        super(Event, self).__init__(name, namespace=namespace, id_=id_)

        self._type = None

    @classmethod
    def from_values(cls, values):
        print values

    def _del(self):
        pass


class Observer(Event):
    root = "observer"
    properties = ['id', 'namespace', 'name', 'data_type', 'triggers']

    def __init__(self, name, data_type, triggers, namespace=None, id_=None):
        super(Observer, self).__init__(name, namespace=namespace, id_=id_)

        self.__data_type = None
        self._type = 'Setup::Observer'

        self.data_type = data_type
        self.triggers = triggers

    @property
    def data_type(self):
        return self.__data_type

    @data_type.setter
    def data_type(self, value):
        assert isinstance(value, DataType), \
            "Object %s is not a Cenit Data Type" % (value,)

        self.__data_type = value

    @classmethod
    def from_values(cls, values):
        rc = []

        for entry in values:
            id_ = entry.get('id', None)
            namespace = entry.get('namespace')
            name = entry.get('name')
            triggers = entry.get('triggers')

            data_type = DataType.get_instance(
                entry.get('data_type', {}).get('id', None))
            if not data_type:
                data_type = DataType.from_values(entry.get('data_type'))

            obs = cls(name, data_type, triggers, namespace=namespace, id_=id_)
            rc.append(obs)

        return rc

    def _del(self):
        pass
