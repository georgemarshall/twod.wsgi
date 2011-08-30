# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010, 2degrees Limited <gustavonarea@2degreesnetwork.com>.
# All Rights Reserved.
#
# This file is part of twod.wsgi <https://github.com/2degrees/twod.wsgi/>,
# which is subject to the provisions of the BSD at
# <http://dev.2degreesnetwork.com/p/2degrees-license.html>. A copy of the
# license should accompany this distribution. THIS SOFTWARE IS PROVIDED "AS IS"
# AND ANY AND ALL EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST
# INFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
Test the set up of the Django applications as WSGI applications.

"""
import os

from django.core.handlers.wsgi import WSGIHandler
from django.utils import unittest

from twod.wsgi.appsetup import (wsgify_django, _set_up_settings,
    _convert_options, _DJANGO_BOOLEANS, _DJANGO_INTEGERS,
    _DJANGO_NESTED_TUPLES, _DJANGO_TUPLES, _DJANGO_DICTIONARIES,
    _DJANGO_NONE_IF_EMPTY_SETTINGS, _DJANGO_UNSUPPORTED_SETTINGS,
    as_tree_tuple, _DJANGO_TREE_TUPLES)

from . import BaseDjangoTestCase

_HERE = os.path.dirname(__file__)
_FIXTURES = os.path.join(_HERE, "fixtures", "sampledjango")


class TestDjangoWsgifytor(BaseDjangoTestCase):
    """Tests for :func:`wsgify_django`."""
    
    setup_fixture = False
    
    def test_it(self):
        global_conf = {
            'debug': "no",
            'django_settings_module': "tests.fixtures.sampledjango.settings",
            }
        app = wsgify_django(
            global_conf,
            FOO=10,
            debug="yes",
            )
        
        self.assertIsInstance(app, WSGIHandler)
        from django.conf import settings
        self.assertFalse(settings.DEBUG)
        self.assertEqual(settings.FOO, 10)


class TestSettingUpSettings(BaseDjangoTestCase):
    """Tests for the internal :func:`_set_up_settings`."""
    
    setup_fixture = False
    
    def test_no_initial_settings(self):
        """
        Additional settings must be added even if there's no initial settings.
        
        """
        global_conf = {
            'debug': "yes",
            'django_settings_module': "tests.fixtures.empty_module",
            }
        local_conf = {
            'setting1': object(),
            'setting2': object(),
            }
        _set_up_settings(global_conf, local_conf)
        from tests.fixtures import empty_module
        
        self.assertEqual(os.environ['DJANGO_SETTINGS_MODULE'], "tests.fixtures.empty_module")
        self.assertTrue(hasattr(empty_module, "setting1"))
        self.assertTrue(hasattr(empty_module, "setting2"))
        self.assertEqual(empty_module.setting1, local_conf['setting1'])
        self.assertEqual(empty_module.setting2, local_conf['setting2'])
    
    def test_no_additional_settings(self):
        """
        The settings module must be left as is if there are no additional
        settings.
        
        """
        global_conf = {
            'debug': "yes",
            'django_settings_module': "tests.fixtures.empty_module2",
            }
        _set_up_settings(global_conf, {})
        from tests.fixtures import empty_module2
        
        self.assertEqual(os.environ['DJANGO_SETTINGS_MODULE'], "tests.fixtures.empty_module2")
        # Ignoring the built-in members:
        scope = [value for value in dir(empty_module2)
                 if not value.startswith("__") and value.endswith("__")]
        self.assertEqual(len(scope), 0)
    
    def test_name_clash(self):
        """
        Additional settings must not override initial values in settings.py.
        
        """
        global_conf = {
            'debug': "yes",
            'django_settings_module': "tests.fixtures.one_member_module",
            }
        local_conf = {
            'MEMBER': "FOO",
            }
        _set_up_settings(global_conf, local_conf)
        from tests.fixtures import one_member_module
        
        self.assertEqual(os.environ['DJANGO_SETTINGS_MODULE'],
            "tests.fixtures.one_member_module")
        self.assertEqual(one_member_module.MEMBER, "MEMBER")
        self.assertTrue(len(self.logs['warning']), 1)
        self.assertEqual('"MEMBER" will not be overridden in tests.fixtures.one_member_module',
            self.logs['warning'][0])
    
    def test_list(self):
        """
        Additional settings can extend lists in the original module.
        
        """
        global_conf = {
            'debug': "yes",
            'django_settings_module': "tests.fixtures.list_module",
            }
        local_conf = {
            'DA_LIST': (8, 9),
            }
        _set_up_settings(global_conf, local_conf)
        from tests.fixtures import list_module
        
        self.assertEqual(os.environ['DJANGO_SETTINGS_MODULE'], "tests.fixtures.list_module")
        self.assertEqual(list_module.DA_LIST, (1, 2, 3, 8, 9))
        
        
    
    def test_non_django_settings_module(self):
        """
        ValueError must be raised if django_settings_module is not set.
        
        """
        global_conf = {
            'debug': "yes",
            }
        self.assertRaises(ValueError, _set_up_settings, global_conf, {})
    
    def test_DEBUG_in_python_configuration(self):
        """DEBUG must not be set in the Django settings module."""
        global_conf = {
            'django_settings_module':
                "tests.fixtures.sampledjango.debug_settings",
            }
        self.assertRaises(ValueError, _set_up_settings, global_conf, {})
    
    def test_non_existing_module(self):
        """
        ImportError must be propagated if the settings module doesn't exist.
        
        """
        global_conf = {
            'debug': "yes",
            'django_settings_module': "non_existing_module",
            }
        self.assertRaises(ImportError, _set_up_settings, global_conf, {})


class TestSettingsConvertion(unittest.TestCase):
    """Unit tests for :func:`_convert_options`."""
    
    def test_official_booleans(self):
        """Django's boolean settings must be converted."""
        # We must exclude "DEBUG" because it's not supposed to be set in the
        # initial settings:
        booleans = _DJANGO_BOOLEANS - frozenset(["DEBUG"])
        
        for setting_name in booleans:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: "True"}
            settings = _convert_options(global_conf, local_conf)
            
            self.assertEqual(settings[setting_name],
                True,
                "%s must be a boolean, but it is %r" % (setting_name,
                                                        settings[setting_name]),
                )
    
    def test_custom_boolean(self):
        """Custom booleans should be converted."""
        global_conf = {
            'debug': "yes",
            'twod.booleans': ("mybool", ),
            }
        local_conf = {'mybool': "no"}
        settings = _convert_options(global_conf, local_conf)
        
        self.assertEqual(settings['mybool'], False)
        self.assertNotIn("twod.booleans", settings)
    
    def test_official_integers(self):
        """Django's integer settings must be converted."""
        for setting_name in _DJANGO_INTEGERS:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: 2}
            settings = _convert_options(global_conf, local_conf)
            
            self.assertEqual(settings[setting_name],
                2,
                "%s must be a integer, but it is %r" % (setting_name,
                                                        settings[setting_name]),
                )
    
    def test_custom_integer(self):
        """Custom integers should be converted."""
        global_conf = {
            'debug': "yes",
            'twod.integers': ("myint", ),
            }
        local_conf = {'myint': "3"}
        settings = _convert_options(global_conf, local_conf)
        
        self.assertEqual(settings['myint'], 3)
        self.assertNotIn("twod.integers", settings)
    
    def test_official_tuples(self):
        """Django's tuple settings must be converted."""
        items = ("foo", "bar", "baz")
        for setting_name in _DJANGO_TUPLES:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: "\n " + "\n    ".join(items)}
            settings = _convert_options(global_conf, local_conf)
            
            self.assertEqual(settings[setting_name], items,
                "%s must be a tuple, but it is %r" % (setting_name,
                                                      settings[setting_name]),
                )
    
    def test_custom_tuple(self):
        """Custom tuples should be converted."""
        items = ("foo", "bar", "baz")
        global_conf = {
            'debug': "yes",
            'twod.tuples': ("mytuple", ),
            }
        local_conf = {'mytuple': "\n " + "\n    ".join(items)}
        settings = _convert_options(global_conf, local_conf)
        
        self.assertEqual(settings['mytuple'], items)
        self.assertNotIn("twod.tuples", settings)
    
    def test_official_nested_tuples(self):
        """Django's nested tuple settings must be converted."""
        items = ("foo;the bar;  baz", "bar ;foo", "baz")
        nested_items = (("foo", "the bar", "baz"), ("bar", "foo"), ("baz",))
        
        for setting_name in _DJANGO_NESTED_TUPLES:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: "\n " + "\n    ".join(items)}
            settings = _convert_options(global_conf, local_conf)
            
            self.assertEqual(settings[setting_name], nested_items)
    
    def test_custom_nested_tuple(self):
        """Custom nested tuples should be converted."""
        items = ("foo;the bar;  baz", "bar ;foo", "baz")
        nested_items = (("foo", "the bar", "baz"), ("bar", "foo"), ("baz",))
        global_conf = {
            'debug': "yes",
            'twod.nested_tuples': ("my_nested_tuple", ),
            }
        local_conf = {'my_nested_tuple': "\n " + "\n    ".join(items)}
        
        settings = _convert_options(global_conf, local_conf)
        
        self.assertEqual(settings['my_nested_tuple'], nested_items)
        self.assertNotIn("twod.nested_tuples", settings)
    
    def test_official_dictionaries(self):
        """Django's dictionary settings must be converted."""
        items = ("foo = bar", "baz=abc", " xyz = mno ")
        dict_items = {'foo': "bar", 'baz': "abc", 'xyz': "mno"}
        
        for setting_name in _DJANGO_DICTIONARIES:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: "\n " + "\n    ".join(items)}
            settings = _convert_options(global_conf, local_conf)
            
            self.assertEqual(settings[setting_name], dict_items,
                "%s must be a dict, but it is %r" % (setting_name,
                                                     settings[setting_name]),
                )
    
    def test_custom_dictionary(self):
        """Custom dictionaries should be converted."""
        items = ("foo = bar", "baz=abc", " xyz = mno ")
        global_conf = {
            'debug': "yes",
            'twod.dictionaries': ("mydict", ),
            }
        local_conf = {'mydict': "\n " + "\n    ".join(items)}
        settings = _convert_options(global_conf, local_conf)
        
        self.assertEqual(settings['mydict'], {'foo': "bar", 'baz': "abc", 'xyz': "mno"})
        self.assertNotIn("twod.dictionaries", settings)
        
    def test_official_none_if_empty_settings(self):
        """Django's settings which are None if unspecified must be converted."""
        
        for setting_name in _DJANGO_NONE_IF_EMPTY_SETTINGS:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: ""}
            settings = _convert_options(global_conf, local_conf)
            
            self.assertIsNone(settings[setting_name],
                "%s must be NoneType, but it is %r" % (setting_name,
                                                       settings[setting_name]),
                )
    
    def test_custom_none_if_empty_settings(self):
        """Custom NoneTypes should be converted."""

        global_conf = {
            'debug': "yes",
            'twod.none_if_empty_settings': ("mynone", "mynonewithspace"),
            }
        local_conf = {'mynone': '', 'mynonewithspace': '    '}
        settings = _convert_options(global_conf, local_conf)
        
        self.assertIsNone(settings['mynone'])
        self.assertIsNone(settings['mynonewithspace'])
        self.assertNotIn("twod.none_if_empty_settings", settings)
        
    def test_non_if_empty_non_empty_settings(self):
        """Non-empty 'none if empty' settings are left as strings."""
        
        global_conf = {
            'debug': "yes",
            'twod.none_if_empty_settings': ("mynone", "mynonewithspace"),
            }
        local_conf = {'mynone': 'I am a string',
                      'mynonewithspace': ' I am a string '}
        settings = _convert_options(global_conf, local_conf)
        
        self.assertEqual(settings['mynone'], 'I am a string')
        self.assertEqual(settings['mynonewithspace'], 'I am a string')
        self.assertNotIn("twod.none_if_empty_settings", settings)
    
    def test_strings(self):
        """
        Values whose values are not requested to be converted should be kept as
        is.
        
        """
        global_conf = {'debug': "yes"}
        local_conf = {'parameter': "value"}
        settings = _convert_options(global_conf, local_conf)
        
        self.assertIn("parameter", settings)
        self.assertEqual(settings['parameter'], "value")
    
    def test_unsupported_settings(self):
        """Unsupported settings are definitely not supported."""
        for setting_name in _DJANGO_UNSUPPORTED_SETTINGS:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: "foo"}
            
            self.assertRaises(ValueError, _convert_options, global_conf,
                          local_conf)
    
    def test__file__is_ignored(self):
        """The __file__ argument must be renamed to paste_configuration_file."""
        global_conf = {'debug': "yes", '__file__': "somewhere"}
        local_conf = {}
        
        settings = _convert_options(global_conf, local_conf)
        
        self.assertNotIn("__file__", settings)
        self.assertIn("paste_configuration_file", settings)
        self.assertEqual(settings['paste_configuration_file'], "somewhere")
    
    def test_DEBUG_in_ini_config(self):
        """Django's DEBUG must not be set in the .ini configuration file."""
        bad_conf = {'DEBUG': "True"}
        # Neither in DEFAULTS:
        self.assertRaises(ValueError, _convert_options, bad_conf, {})
        # Nor on the application definition:
        self.assertRaises(ValueError, _convert_options, {}, bad_conf)
        
    
    def test_pastes_debug(self):
        """Django's "DEBUG" must be set to Paster's "debug"."""
        global_conf = {'debug': "true"}
        local_conf = {}
        settings = _convert_options(global_conf, local_conf)
        self.assertIn("DEBUG", settings)
        self.assertEqual(settings['DEBUG'], True)
    
    def test_no_paste_debug(self):
        """Ensure the "debug" directive for Paste is set."""
        self.assertRaises(ValueError, _convert_options, {}, {})
    
    def test_official_tree_tuples(self):
        """Django's tree tuple settings must be converted."""
        definition = """ 
            a
             - aa,
             - ab,
            b
             - ba,
             - bb,
            """
        tree_tuple = (
            ('a', ('aa', 'ab')),
            ('b', ('ba', 'bb')),
            )
        
        for setting_name in _DJANGO_TREE_TUPLES:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: "\n " + definition}
            settings = _convert_options(global_conf, local_conf)
            
            self.assertEqual(settings[setting_name], tree_tuple)
    
    def test_custom_tree_tuple(self):
        """Custom tree tuples should be converted."""
        definition = """ 
            a
             - aa,
             - ab,
            b
             - ba,
             - bb,
            """
        tree_tuple = (
            ('a', ('aa', 'ab')),
            ('b', ('ba', 'bb')),
            )
        global_conf = {
            'debug': "yes",
            'twod.tree_tuples': ("my_tree_tuple", ),
            }
        local_conf = {'my_tree_tuple': "\n " + definition}
        
        settings = _convert_options(global_conf, local_conf)
        
        self.assertEqual(settings['my_tree_tuple'], tree_tuple)
        self.assertNotIn("twod.tree_tuples", settings)


class TestTreeTuple(unittest.TestCase):
    
    def test_two_levels(self):
        """Generation of two-levels tuples""" 
        definition = """ 
            a
             - aa,
             - ab,
            b
             - ba,
             - bb,
            """
        expected = (
            ('a', ('aa', 'ab')),
            ('b', ('ba', 'bb')),
            )
        
        result = as_tree_tuple(definition)
        self.assertEqual(result, expected)
    
    def test_three_levels(self):
        """Generation of three-levels tuples""" 
        definition = """ 
            a
             - aa,
              -- aaa
             - ab,
            """
        expected = ('a', (('aa', 'aaa'), 'ab'))
        
        result = as_tree_tuple(definition)
        self.assertEqual(result[0], expected)
    
    def test_single_element_with_comma(self):
        """A trailing comma forces tuple creation for single elements""" 
        definition = """ 
            a
             - aa,
            b
            """
        expected = (('a', ('aa',)), 'b')
        
        result = as_tree_tuple(definition)
        self.assertEqual(result, expected)

    def test_single_element_without_comma(self):
        """
        A single element without a trailing comma is not inserted in a tuple
        """ 
        definition = """ 
            a
             - aa
            b
            """
        expected = (('a', 'aa'), 'b')
        
        result = as_tree_tuple(definition)
        self.assertEqual(result, expected)
