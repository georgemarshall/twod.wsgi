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
Enhanced WSGI support for Django applications.
"""
from __future__ import absolute_import

# Importing elements that should be available from this namespace:
from .handler import DjangoApplication, TwodResponse
from .middleware import RoutingArgsMiddleware
from .embedded_wsgi import call_wsgi_app, make_wsgi_view
from .appsetup import wsgify_django

__all__ = ("DjangoApplication", "TwodResponse", "RoutingArgsMiddleware",
           "call_wsgi_app", "make_wsgi_view", "wsgify_django")
