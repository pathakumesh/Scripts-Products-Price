# -*- coding: utf-8 -*-

import re
import time
import scrapy
import json
import itertools
import logging as log
from price_extracter.items import PriceExtractItem


class PriceExtractSpider(scrapy.Spider):
    name = "price_extract_spider"
    allowed_domains = ["laptopchicken.com"]
    start_urls = ['http://www.laptopchicken.com/']
    price_url = "https://sellbroke.com/wp-admin/admin-ajax.php"

    def parse(self, response):
        brands = response.xpath('//select[@name="brend_id"]/option')
        for brand in brands:
            item = PriceExtractItem()
            brand_id = brand.xpath('@value').extract_first()
            if brand_id in ["0", "/not-in-list/"]:
                continue
            item['brand'] = brand.xpath('text()').extract_first()
            request =  scrapy.FormRequest(
                                url= "http://www.laptopchicken.com/_content/popup_models.php",
                                formdata={"id": brand_id},
                                callback=self.parse_each_brand,
                    )
            request.meta['item'] = item
            request.meta['id'] = brand_id
            yield request

    def parse_each_brand(self, response):
        item = response.meta['item']
        brend_id = response.meta['id']
        items = response.xpath('//label[@class="Modarr"]')
        for _item in items:
            item = PriceExtractItem(item)
            name = _item.xpath('text()').extract_first()
            item['name'] = name
            model_id = _item.xpath('@for').extract_first()
            # item['condition'] = item_id
            # yield item
            request =  scrapy.FormRequest(
                                url= "http://www.laptopchicken.com/Simple-Questions/",
                                formdata={"brend_id": brend_id, "model_id": model_id},
                                callback=self.parse_each_item,
                    )
            request.meta['item'] = item
            yield request
            
            # request = scrapy.Request(item_url, callback=self.parse_each_item)
            # request.meta['item'] = item
            # yield request

            
    def parse_each_item(self, response):
        
        item = response.meta['item']
        price_content = response.xpath('//h2[@id="m-price"]')
        item['price'] = price_content.xpath('b/text()').extract_first()
        yield item