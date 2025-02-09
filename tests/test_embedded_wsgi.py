# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009-2010, 2degrees Limited <gustavonarea@2degreesnetwork.com>.
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
Tests for the use of WSGI applications within Django.

"""
from twod.wsgi import call_wsgi_app, make_wsgi_view
from twod.wsgi.exc import ApplicationCallError
from twod.wsgi.handler import TwodWSGIRequest

from . import (BaseDjangoTestCase, MockApp, MockClosingApp, MockWriteApp,
                   MockGeneratorApp, complete_environ)


class TestCallWSGIApp(BaseDjangoTestCase):
    """
    Tests for call_wsgi_app()
    
    """
    
    def test_original_environ_not_modified(self):
        """The original environ must have not been modified."""
        original_environ = complete_environ(SCRIPT_NAME="/blog",
                                            PATH_INFO="/admin/models")
        request = _make_request(**original_environ)
        expected_environ = original_environ.copy()
        # Running the app:
        app = MockApp("200 OK", [])
        call_wsgi_app(app, request, "/models")
        # Checking the environment after calling the WSGI application, but first
        # let's remove WebOb's ad-hoc attributes:
        del request.environ['webob.adhoc_attrs']
        self.assertEqual(request.environ, expected_environ)
    
    def test_routing_args_are_removed(self):
        """The ``wsgiorg.routing_args`` environment key must be removed."""
        environ = {
            'wsgiorg.routing_args': ((), {}),
            'PATH_INFO': "/admin/models",
            }
        environ = complete_environ(**environ)
        request = _make_request(**environ)
        # Running the app:
        app = MockApp("200 OK", [])
        call_wsgi_app(app, request, "/models")
        self.assertNotIn("wsgiorg.routing_args", app.environ)
    
    def test_webob_adhoc_attrs_are_removed(self):
        """WebOb's ad-hoc attributes must be removed."""
        environ = {
            'PATH_INFO': "/admin/models",
            'wsgiorg.routing_args': ((), {}),
            'webob.adhoc_attrs': {'foo': "bar"},
            }
        environ = complete_environ(**environ)
        request = _make_request(**environ)
        # Running the app:
        app = MockApp("200 OK", [])
        call_wsgi_app(app, request, "/models")
        self.assertNotIn("webob.adhoc_attrs", app.environ)
    
    def test_mount_point(self):
        environ = complete_environ(SCRIPT_NAME="/dev", PATH_INFO="/trac/wiki")
        request = _make_request(**environ)
        # Running the app:
        app = MockApp("200 OK", [])
        call_wsgi_app(app, request, "/wiki")
        self.assertEqual(app.environ['SCRIPT_NAME'], "/dev/trac")
        self.assertEqual(app.environ['PATH_INFO'], "/wiki")
    
    def test_incorrect_mount_point(self):
        """
        WSGI apps are not run when the path left to them is not the last
        portion of the PATH_INFO in the original request.
        
        """
        environ = complete_environ(SCRIPT_NAME="/dev",
                                   PATH_INFO="/trac/wiki")
        request = _make_request(**environ)
        path_info = "/trac"
        # Running the app:
        app = MockApp("200 OK", [])
        self.assertRaises(ApplicationCallError, call_wsgi_app, app, request,
                      path_info)
    
    def test_http_status(self):
        environ = complete_environ(SCRIPT_NAME="/dev", PATH_INFO="/trac/wiki")
        request = _make_request(**environ)
        # Running the app and make a valid request:
        app_ok = MockApp("200 Alright", [])
        django_response_ok = call_wsgi_app(app_ok, request, "/wiki")
        self.assertEqual(200, django_response_ok.status_code)
        self.assertEqual("Alright", django_response_ok.status_reason)
        # Running the app and make an invalid request:
        app_bad = MockApp("403 What are you trying to do?", [])
        django_response_bad = call_wsgi_app(app_bad, request, "/wiki")
        self.assertEqual(403, django_response_bad.status_code)
        self.assertEqual("What are you trying to do?", django_response_bad.status_reason)
    
    def test_headers_are_copied_over(self):
        environ = complete_environ(SCRIPT_NAME="/dev", PATH_INFO="/trac/wiki")
        request = _make_request(**environ)
        headers = [
            ("X-Foo", "bar"),
            ("Content-Type", "text/plain"),
            ]
        # The same headers, but set in the format used by HttpResponse
        expected_headers = {
            'x-foo': ("X-Foo", "bar"),
            'content-type': ("Content-Type", "text/plain"),
            'x-actual-status-reason': ("X-Actual-Status-Reason", "200 OK"),
            }
        # Running the app:
        app = MockApp("200 OK", headers)
        django_response = call_wsgi_app(app, request, "/wiki")
        self.assertEqual(expected_headers, django_response._headers)
    
    def test_authenticated_user(self):
        environ = complete_environ(SCRIPT_NAME="/dev", PATH_INFO="/trac/wiki")
        request = _make_request(authenticated=True, **environ)
        # Running the app:
        app = MockApp("200 OK", [])
        call_wsgi_app(app, request, "/wiki")
        self.assertEqual("foobar", app.environ['REMOTE_USER'])
    
    def test_cookies_sent(self):
        environ = complete_environ(SCRIPT_NAME="/dev", PATH_INFO="/trac/wiki")
        request = _make_request(**environ)
        headers = [
            ("Set-Cookie", "arg1=val1"),
            ("Set-Cookie", "arg2=val2; expires=Fri,%2031-Dec-2010%2023:59:59%20GMT"),
            ("Set-Cookie", "arg3=val3; path=/"),
            ("Set-Cookie", "arg4=val4; path=/wiki"),
            ("Set-Cookie", "arg5=val5; domain=.example.org"),
            ("Set-Cookie", "arg6=val6; max-age=3600"),
            ("Set-Cookie", "arg7=val7; expires=Fri,%2031-Dec-2010%2023:59:59%20GMT; max-age=3600; domain=.example.org; path=/wiki"),
            # Now let's try an Unicode cookie:
            ("Set-Cookie", u"arg8=val8; max-age=3600"),
            # TODO: The "secure" cookie *attribute* is broken in SimpleCookie.
            # See: http://bugs.python.org/issue1028088
            #("Set-Cookie", "arg9=val9; secure"),
            ]
        expected_cookies = {
            'arg1': {'value': "val1"},
            'arg2': {'value': "val2", 'expires': "Fri,%2031-Dec-2010%2023:59:59%20GMT"},
            'arg3': {'value': "val3", 'path': "/"},
            'arg4': {'value': "val4", 'path': "/wiki"},
            'arg5': {'value': "val5", 'domain': ".example.org"},
            'arg6': {'value': "val6", 'max-age': "3600"},
            'arg7': {
                'value': "val7",
                'expires': "Fri,%2031-Dec-2010%2023:59:59%20GMT",
                'path': "/wiki",
                'domain': ".example.org",
                'max-age': "3600",
                },
            'arg8': {'value': "val8", 'max-age': "3600"},
            # Why the next item as disabled? Check the `headers` variable above
            #'arg9': {'value': "val9", 'secure': True},
            }
        # Running the app:
        app = MockApp("200 OK", headers)
        django_response = call_wsgi_app(app, request, "/wiki")
        # Checking the cookies:
        self.assertEqual(len(expected_cookies), len(django_response.cookies))
        # Finally, let's check each cookie:
        for (cookie_set_name, cookie_set) in django_response.cookies.items():
            expected_cookie = expected_cookies[cookie_set_name]
            expected_cookie_value = expected_cookie.pop("value")
            self.assertEqual(expected_cookie_value, cookie_set.value,
                             'Cookie "%s" has a wrong value ("%s")' %
                             (cookie_set_name, cookie_set.value))
            for (attr_key, attr_val) in expected_cookie.items():
                self.assertEqual(cookie_set[attr_key], attr_val,
                                 'Attribute "%s" in cookie "%s" is wrong (%s)' %
                                 (attr_key, cookie_set_name, cookie_set[attr_key]))
    
    def test_string_as_response(self):
        app = MockApp("200 It is OK", [("X-HEADER", "Foo")])
        # Running a request:
        environ = complete_environ(SCRIPT_NAME="/dev", PATH_INFO="/blog/posts")
        request = _make_request(**environ)
        django_response = call_wsgi_app(app, request, "/posts")
        # Checking the response:
        http_response = (
            "X-HEADER: Foo\n"
            "Content-Type: text/html; charset=utf-8\n"
            "X-Actual-Status-Reason: 200 It is OK\n"
            "\n"
            "body"
            )
        self.assertEqual(http_response, str(django_response))
    
    def test_iterable_as_response(self):
        app = MockGeneratorApp("200 It is OK", [("X-HEADER", "Foo")])
        # Running a request:
        environ = complete_environ(SCRIPT_NAME="/dev", PATH_INFO="/blog/posts")
        request = _make_request(**environ)
        django_response = call_wsgi_app(app, request, "/posts")
        # Checking the response:
        self.assertFalse(django_response._is_string)
        self.assertTrue(django_response.has_header("X-HEADER"))
        http_response = (
            "X-HEADER: Foo\n"
            "Content-Type: text/html; charset=utf-8\n"
            "X-Actual-Status-Reason: 200 It is OK\n"
            "\n"
            "body as iterable"
            )
        self.assertEqual(http_response, str(django_response))
    
    def test_write_response(self):
        app = MockWriteApp("200 It is OK", [("X-HEADER", "Foo")])
        # Running a request:
        environ = complete_environ(SCRIPT_NAME="/dev", PATH_INFO="/blog/posts")
        request = _make_request(**environ)
        django_response = call_wsgi_app(app, request, "/posts")
        # Checking the response:
        self.assertFalse(django_response._is_string)
        self.assertTrue(django_response.has_header("X-HEADER"))
        http_response = (
            "X-HEADER: Foo\n"
            "Content-Type: text/html; charset=utf-8\n"
            "X-Actual-Status-Reason: 200 It is OK\n"
            "\n"
            "body as iterable"
            )
        self.assertEqual(http_response, str(django_response))
    
    def test_closure_response(self):
        """The .close() method in the response (if any) must be kept."""
        app = MockClosingApp("200 It is OK", [])
        # Running a request:
        environ = complete_environ(SCRIPT_NAME="/dev", PATH_INFO="/blog/posts")
        request = _make_request(**environ)
        django_response = call_wsgi_app(app, request, "/posts")
        # Checking the .close() call:
        self.assertFalse(app.app_iter.closed)
        django_response.close()
        self.assertTrue(app.app_iter.closed)


class TestWSGIView(BaseDjangoTestCase):
    """
    Tests for make_wsgi_view().
    
    """
    
    def test_right_path(self):
        """
        The WSGI application view must work when called with the right path.
        
        """
        # Loading a WSGI-powered Django view:
        headers = [("X-SALUTATION", "Hey")]
        app = MockApp("206 One step at a time", headers)
        django_view = make_wsgi_view(app)
        # Running a request:
        environ = complete_environ(SCRIPT_NAME="/dev",
                                   PATH_INFO="/app1/wsgi-view/foo/bar")
        request = _make_request(**environ)
        # Checking the response:
        django_response = django_view(request, "/foo/bar")
        self.assertEqual(django_response.status_code, 206)
        self.assertEqual(("X-SALUTATION", "Hey"), django_response._headers['x-salutation'])
        self.assertEqual(app.environ['PATH_INFO'], "/foo/bar")
        self.assertEqual(app.environ['SCRIPT_NAME'], "/dev/app1/wsgi-view")
    
    def test_not_final_path(self):
        """
        The path to be consumed by the WSGI app must be the end of the original
        PATH_INFO.
        
        """
        # Loading a WSGI-powered Django view:
        headers = [("X-SALUTATION", "Hey")]
        app = MockApp("206 One step at a time", headers)
        django_view = make_wsgi_view(app)
        # Running a request:
        environ = complete_environ(SCRIPT_NAME="/dev",
                                   PATH_INFO="/app1/wsgi-view/foo/bar")
        request = _make_request(**environ)
        # Checking the response. Note "/foo" is NOT the end of PATH_INFO:
        self.assertRaises(ApplicationCallError, django_view, request, "/foo")


#{ Test utilities


def _make_request(authenticated=False, **environ):
    """
    Make a Django request from the items in the WSGI ``environ``.
    
    """
    class MockDjangoUser(object):
        def __init__(self, authenticated):
            self.username = "foobar"
            self.authenticated = authenticated
        def is_authenticated(self):
            return self.authenticated
    request = TwodWSGIRequest(environ)
    request.user = MockDjangoUser(authenticated)
    return request


#}
