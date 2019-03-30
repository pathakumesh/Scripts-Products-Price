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
    allowed_domains = ["laptopnuts.com"]
    ajax_url = "https://www.laptopnuts.com/wp-admin/admin-ajax.php"
    brands = ["Acer", "Alienware", "Apple", "Aspire", "Asus", "Dell", "Elitebook", "Envy", "Gateway", "Gigabyte", "HP",
                "Lenovo", "MSI", "MacBook", "Microsoft", "Razer", "Sager", "Samsung", "Sony", "Toshiba"]
    
    def start_requests(self):
        for brand in self.brands:
            formdata = {
                    "action": "get_devices_list",
                    "manufacturer_id": brand,
                    "category_id": "1"
            }
            request = scrapy.FormRequest(
                                self.ajax_url,
                                method="POST", 
                                formdata=formdata,
                                headers = {'X-Requested-With': 'XMLHttpRequest','Referer':'https://www.laptopnuts.com/'},
            )
            request.meta['brand'] = brand
            yield request
    
    def parse(self, response):
        brand = response.meta['brand']
        data =  json.loads(response.text.replace(']0', ']'))
        for d in data:
            item = PriceExtractItem()
            item['brand'] = brand
            item['name'] = d['model']
            item['price'] = d['price']
            yield item