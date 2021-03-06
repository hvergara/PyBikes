# -*- coding: utf-8 -*-
# Copyright (C) 2010-2012, eskerda <eskerda@gmail.com>
# Distributed under the AGPL license, see LICENSE.txt

import re

from pyquery import PyQuery as pq
from .base import BikeShareSystem, BikeShareStation
from . import utils

__all__ = ['BCycleSystem', 'BCycleStation']

LAT_LNG_RGX = "var\ point\ =\ new\ google.maps.LatLng\(([+-]?\\d*\\.\\d+)(?![-+0-9\\.])\,\ ([+-]?\\d*\\.\\d+)(?![-+0-9\\.])\)"
DATA_RGX = "var\ marker\ =\ new\ createMarker\(point\,(.*?)\,\ icon\,\ back"
USERAGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/31.0.1650.63 Chrome/31.0.1650.63 Safari/537.36"

class BCycleError(Exception):
    def __init__(self, msg):
            self.msg = msg

    def __repr__(self):
            return self.msg
    __str__ = __repr__


class BCycleSystem(BikeShareSystem):

    feed_url = "http://{system}.bcycle.com"
    sync = True

    meta = {
        'system': 'B-cycle',
        'company': [ 'Trek Bicycle Corporation'
                     ,'Humana'
                     ,'Crispin Porter + Bogusky' ]
    }

    def __init__(self, tag, meta, system = None, feed_url = None):
        super( BCycleSystem, self).__init__(tag, meta)
        if feed_url is not None:
            self.feed_url = feed_url
        else:
            self.feed_url = BCycleSystem.feed_url.format(system =  system)

    def update(self, scraper = None):

        if scraper is None:
            scraper = utils.PyBikesScraper()
        scraper.setUserAgent(USERAGENT)

        html_data = scraper.request(self.feed_url)

        geopoints = re.findall(LAT_LNG_RGX, html_data)
        puzzle = re.findall(DATA_RGX, html_data)
        self.stations = [
            BCycleStation(latlng, fuzzle)
                for latlng, fuzzle in zip(geopoints, puzzle)
        ]


class BCycleStation(BikeShareStation):
    def __init__(self, latlng, fuzzle):
        """ Take a good look at this fuzzle:
            var point = new google.maps.LatLng(41.86727, -87.61527);
            var marker = new createMarker(
                point,                       .--- Fuzzle
                "<div class='location'>      '
                    <strong>Museum Campus</strong><br />
                    1200 S Lakeshore Drive<br />
                    Chicago, IL 60605
                </div>
                <div class='avail'>
                    Bikes available: <strong>0</strong><br />
                    Docks available: <strong>21</strong>
                </div>
                <br/>
                ", icon, back);
            Now, do something about it
        """
        super(BCycleStation, self).__init__()
        self.latitude = float(latlng[0])
        self.longitude = float(latlng[1])
        d = pq(fuzzle)('div')
        location = d.find('.location').html().split('<br/>')
        availability = d.find('.avail strong')

        self.name = pq(location[0]).html()
        self.bikes = int(availability.eq(0).text())
        self.free = int(availability.eq(1).text())

        self.extra = {
            'address' : u'{0} - {1}'.format(location[1], location[2])
        }

