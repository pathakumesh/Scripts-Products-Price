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
    allowed_domains = ["sellbroke.com"]
    start_urls = ['https://sellbroke.com']
    price_url = "https://sellbroke.com/wp-admin/admin-ajax.php"

    def parse(self, response):
        categories = response.xpath('//div[@id="lte_device_selector_container"]/div/a')
        for category in categories:
            category_url = category.xpath('@href').extract_first()
            if 'https://sellbroke.com/sell/other/' in category_url:
                continue
            yield scrapy.Request(category_url, callback = self.parse_each_category)
    
    def parse_each_category(self, response):
        brands = response.xpath('//div[@id="lte_device_selector_container"]/div/a')
        for brand in brands:
            item = PriceExtractItem()
            item['brand'] = brand.xpath('div/div/div/h4/text()').extract_first()
            brand_url = brand.xpath('@href').extract_first()
            if 'MacBook Pro' in item['brand']:
                print 'apple url is ', brand_url, item['brand']
            request = scrapy.Request(brand_url, callback=self.parse_each_brand)
            request.meta['item'] = item
            yield request
    

    def parse_each_brand(self, response):
        item = response.meta['item']
        items = response.xpath('//div[@id="lte_device_selector_container"]/div/a')
        for _item in items:
            item = PriceExtractItem(item)
            item_url = _item.xpath('@href').extract_first()
            name = _item.xpath('div//h4/text()').extract_first()
            item['name'] = name
            request = scrapy.Request(item_url, callback=self.parse_each_item)
            request.meta['item'] = item
            yield request

        next_page = response.xpath('//a[@class="nextpostslink"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
            
    def parse_each_item(self, response):
        table_rows = response.xpath('//table/tr')
        options_dict = dict()
        if table_rows:
            for row in table_rows:
                _type = row.xpath('td/select/@name').extract_first()
                # values = [_value for _value in row.xpath('td/select/option/@value').extract() if _value]
                options_dict.update({_type:[_value for _value in row.xpath('td/select/option/@value').extract() if _value]})
        item = response.meta['item']
        device_id = response.xpath('//link[@rel="shortlink"]/@href').re(r'.*p=(\S+)')[0]
        if options_dict:
            revised_list= get_revised_list(options_dict)
            for r in revised_list:
                new_item = PriceExtractItem(item)
                used_item = PriceExtractItem(item)
                for k,v in r.iteritems():
                    option_type = re.search(r'selected_options\[(\w+)\]',k).group(1)
                    if option_type in ['Stordge', 'Hard_Drive', 'Storage450', 'Hard_drive']:
                        option_type = "Storage"
                    if option_type not in ['Display', 'Processor']:
                        new_item[option_type] = v
                        used_item[option_type] = v
                    
                formdata_new = {
                    "device_id": device_id,
                    "action": "lte_getquote",
                    "condition": "new",
                }
                formdata_new.update(r)
                new_item['condition'] = "Like New"
                request =  scrapy.FormRequest(url = self.price_url, formdata=formdata_new, callback=self.get_price_from_item)
                request.meta['item'] = new_item
                yield request
                # time.sleep(1.5)
                used_item['condition'] = "Used (Good)"
                formdata_good = {
                    "device_id": device_id,
                    "action": "lte_getquote",
                    "condition": "used_good"
                }
                formdata_good.update(r)
                request =  scrapy.FormRequest(url = self.price_url, formdata=formdata_good, callback=self.get_price_from_item)
                request.meta['item'] = used_item
                yield request        
        else:
            formdata_new = {
                "device_id": device_id,
                "action": "lte_getquote",
                "condition": "new"
            }
            item['condition'] = "Like New"
            request =  scrapy.FormRequest(url = self.price_url, formdata=formdata_new, callback=self.get_price_from_item)
            request.meta['item'] = item
            yield request
            # time.sleep(1.5)
            used_item = PriceExtractItem(item)
            used_item['condition'] = "Used (Good)"
            formdata_good = {
                "device_id": device_id,
                "action": "lte_getquote",
                "condition": "used_good"
            }
            
            request =  scrapy.FormRequest(url = self.price_url, formdata=formdata_good, callback=self.get_price_from_item)
            request.meta['item'] = used_item
            yield request

        

    def get_price_from_item(self, response):
        item = response.meta['item']
        data = json.loads(response.text)
        item['price'] = data['quote']
        yield item

def get_revised_list(mydict):
    if mydict.get('selected_options[Memory]') and mydict.get('selected_options[Storage]'):
        l1= [{'selected_options[Storage]':i[0],'selected_options[Memory]':i[1]} for i in itertools.product(mydict.get('selected_options[Storage]'), mydict.get('selected_options[Memory]'))]
    elif mydict.get('selected_options[Storage]'):
        l1= [{'selected_options[Storage]':i[0]} for i in itertools.product(mydict.get('selected_options[Storage]'))]
    elif mydict.get('selected_options[Memory]'):
        l1= [{'selected_options[Memory]':i[0]} for i in itertools.product(mydict.get('selected_options[Memory]'))]
    elif mydict.get('selected_options[Storage450]'):
        l1= [{'selected_options[Storage450]':i[0]} for i in itertools.product(mydict.get('selected_options[Storage450]'))]
    elif mydict.get('selected_options[Stordge]'):
        l1= [{'selected_options[Stordge]':i[0]} for i in itertools.product(mydict.get('selected_options[Stordge]'))]
    elif mydict.get('selected_options[Hard_Drive]'):
        l1= [{'selected_options[Hard_Drive]':i[0]} for i in itertools.product(mydict.get('selected_options[Hard_Drive]'))]
    elif mydict.get('selected_options[Hard_drive]'):
        l1= [{'selected_options[Hard_drive]':i[0]} for i in itertools.product(mydict.get('selected_options[Hard_drive]'))]
    elif mydict.get('selected_options[Processor]'):
        l1= [{'selected_options[Processor]':i[0]} for i in itertools.product(mydict.get('selected_options[Processor]'))]
        l1 = l1[:1]
    elif mydict.get('selected_options[Display]'):
        l1= [{'selected_options[Display]':i[0]} for i in itertools.product(mydict.get('selected_options[Display]'))]
        l1 = l1[:1]
    return l1

        