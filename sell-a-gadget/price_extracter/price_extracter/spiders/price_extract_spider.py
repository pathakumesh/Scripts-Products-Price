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
    allowed_domains = ["sellagadget.com"]
    start_urls = ['https://sellagadget.com/']
    final_url = "https://sellagadget.com/question-builder.php"
    dev_type = {
        'Laptop': "1",
        'Phone': "2",
        'Tablet': "3",
        'Robot Vacuum': "4",
        'Camera': "5",
        'Smartwatch': "6",
        'Other Gadgets': "7",
        'Desktops/AIO': "8",
    }

    def parse(self, response):
        types = response.xpath('//h4[@class="bottom-h4"]')
        print 'url is ', response.url
        for _type in types:
            next_link = _type.xpath('a/@href').extract_first()
            
            request =  scrapy.Request(next_link, callback = self.parse_each_type)
            request.meta['_type'] = _type.xpath('a').re(r'Sell (.*?)<')[0]
            
            yield request

    def parse_each_type(self, response):
        _type = response.meta['_type']
        brands = response.xpath('//a[@class="btn btn-primary btn-block brand-buttons"]')
        for brand in brands:
            next_link = brand.xpath('@href').extract_first()
            
            request =  scrapy.Request(next_link, callback = self.parse_each_brand)
            request.meta['brand'] = brand.xpath('text()').extract_first()
            request.meta['_type'] = _type
            
            yield request
            
            
    def parse_each_brand(self, response):
        _type = response.meta['_type']
        brand = response.meta['brand']

        names = response.xpath('//div[@class="form-group mt-3 hide-modal"]/select/option[@data-price]')
        for name in names:
            item = PriceExtractItem()
            item['name'] = name.xpath('text()').extract_first()
            model_id = name.xpath('@value').extract_first()
            item['brand'] = brand
            item['_type'] = _type
            formdata = {"dev_type": self.dev_type[_type],
                        "model_id": model_id
            }
            request =  scrapy.FormRequest(
                                self.final_url,
                                method="POST", 
                                formdata=formdata,
                                headers = {'X-Requested-With': 'XMLHttpRequest','Referer':'https://sellagadget.com/sell-VRHeadsets-OtherGadgets'},
                                callback=self.get_price_from_item,
                    )
        
            request.meta['item'] = item
            request.meta['formdata'] = formdata
            yield request    
    
    def get_price_from_item(self, response):
        item = response.meta['item']
        data = json.loads(response.text)
        if data.get('items'):
            price = data['items']['price']
            item['price'] = price
            yield item