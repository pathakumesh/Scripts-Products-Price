# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class PriceExtractItem(scrapy.Item):
    # define the fields for your item here like:
    brand = scrapy.Field()
    name = scrapy.Field()
    condition = scrapy.Field()
    price = scrapy.Field()
    pass
