# -*- coding: utf-8 -*-
"""
URL definitions for the mock Django application.

"""
from __future__ import absolute_import

from django.conf.urls.defaults import patterns, include, url

from .. import mock_view

urlpatterns = patterns('',
    url(r'^secret', mock_view),
    url(r'^nothing', mock_view),
)

