# -*- coding: utf-8 -*-

import re
import time
import scrapy
from scrapy.http import HtmlResponse
import json
import logging as log
from price_extracter.items import PriceExtractItem


class PriceExtractSpider(scrapy.Spider):
    name = "price_extract_spider"
    allowed_domains = ["getcashforlaptop.com"]
    start_urls = ['https://www.getcashforlaptop.com/_content/InstantQuote/_get_step1.php']
    get_model_url = "https://www.getcashforlaptop.com/_content/InstantQuote/_get_model.php?PHPSESSID=83372f28e601efd4ac2b98f6ff0b7d67&JsHttpRequest=111111-xml"

    def parse(self, response):

        #Request with payload
        for brand in response.xpath('//div[@class="partners"]/ul/*'):
            item = PriceExtractItem()
            item['brand'] = brand.xpath('a/img/@alt').extract_first()
            brend_id = brand.xpath('a/@onclick').re(r'.*Model\((\d+),')[0]
            request =  scrapy.Request(
                                  self.get_model_url, 
                                  callback = self.parse_each_model, 
                                  method="POST", 
                                  body="id=%s&a=&b=" % brend_id,
                                  headers={'Content-Type':'application/octet-stream'}
                        )
            request.meta['item'] = item
            request.meta['brend_id'] = brend_id
            yield request

    def parse_each_model(self, response):
        item = response.meta['item']
        brend_id = response.meta['brend_id']
        data =  json.loads(response.body)
        body = data['js']['strModel']
        response = HtmlResponse(url=response.url, body=body, encoding='utf-8')
        models = response.xpath('//select[@name="model_id"]/*')
        ignore_model = ['Select your model', 'My  model is not on this list']
        for model in models:
            if model.xpath('text()').extract_first() in ignore_model:
                continue
            new_item = PriceExtractItem(item)
            new_item['name'] = model.xpath('text()').extract_first().strip()
            model_id = model.xpath('@value').extract_first()
            request =  scrapy.FormRequest(
                                url= "https://www.getcashforlaptop.com/_content/InstantQuote/_get_step3.php",
                                formdata={"model_id": model_id,
                                        "brend_id": brend_id,
                                        "PhysicalCondition": "18",
                                        'func': "14",
                                        "step": "3",
                                },
                                callback=self.get_price_from_item,
                                headers = {
                                    # "Host": "www.getcashforlaptop.com",
                                    # "Connection": "keep-alive",
                                    # "Pragma": "no-cache",
                                    # "Cache-Control": "no-cache",
                                    # "Accept": "*/*",
                                    "Referer": "https://www.getcashforlaptop.com/InstantQuote/",
                                    "X-Requested-With": "XMLHttpRequest",
                                    # "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                                    # "Cookie": "PHPSESSID=83372f28e601efd4ac2b98f6ff0b7d67;"
                                }
                    )
        
            request.meta['item'] = new_item
            yield request    

    def get_price_from_item(self, response):
        item = response.meta['item']
        price = response.xpath('//span[@class="price"]/text()').extract_first()
        item['price'] = price.strip() if price else 0
        yield item

