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
URL definitions for the mock Django application.

"""
from __future__ import absolute_import

from django.conf.urls.defaults import patterns, include, url
from twod.wsgi import make_wsgi_view

from .... import MockApp
from .. import mock_view

app = make_wsgi_view(MockApp("206 One step at a time",
                             [("X-SALUTATION", "Hey")]))

ok_app = make_wsgi_view(MockApp("200 OK", [("X-SALUTATION", "Hey")]))

urlpatterns = patterns('',
    url(r'^blog', mock_view),
    url(r'^admin', mock_view),
    url(r'^secret', mock_view),
    url(r"wsgi-view-ok(/.*)?", ok_app),
    url(r"wsgi-view(/.*)?", app),
)
