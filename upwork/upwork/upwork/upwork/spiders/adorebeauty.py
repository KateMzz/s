import scrapy
from requests.models import Response
import json
import math
from scrapy.shell import inspect_response
from scrapy.http import headers, request
from io import StringIO
from html.parser import HTMLParser
from scrapy.crawler import CrawlerProcess
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from urllib.parse import urlparse

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def html_to_text(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

class AdorebeautySpider(scrapy.Spider):
    name = 'adorebeauty'

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9',
        'sec-ch-ua': ' Not A;Brand";v="99", "Chromium";v="92", "Opera";v="78"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 OPR/78.0.4093.112'
        
    }

    def start_requests(self):  
        yield scrapy.Request(url='https://www.adorebeauty.co.nz/api/cat?identifier=skin-care&locale=en-NZ', callback=self.category, headers=self.headers)
   
  
    def times_loop(self, response):
        resp = json.loads(response.body)
        prod_number = int(resp.get('result_count'))
        pages = math.ceil(prod_number/23) 
        for page in range(pages):
            yield scrapy.Request(
                url=f'https://www.adorebeauty.co.nz/api/cat?identifier=skin-care&p={page}&locale=en-NZ',
                 callback=self.parse_prod_end,
                  headers=self.headers)
   


    def parse_prod_end(self, response):
        resp = json.loads(response.body)
        items = resp.get('products')
        endpoint_bank = []
        for item in items:
            prod_endpoint = item.get('url_key_s')
            if prod_endpoint not in endpoint_bank:
                endpoint_bank.append(prod_endpoint)
                prod_api = f'https://www.adorebeauty.co.nz/api/product?identifier={prod_endpoint}&locale=en-NZ'
                yield scrapy.Request(url=prod_api, callback=self.parse_prod_info, headers=self.headers)
            else:
                continue

    def parse_prod_info(self, response):
        resp = json.loads(response.body)
        prod_url_bank=[]
        prod_url = resp.get('productUrl')
        prod_url_bank.append(prod_url)
        prod_name = resp.get('name_t')
        brand_name = resp.get('manufacturer_t_mv')
        prod_category = resp.get('category_name_t_mv')[0]
        prod_subcategory = resp.get('ec_category_nonindex')
        prod_description = resp.get('short_description_nonindex')
        prod_description = prod_description.replace(';', '')
        prod_description = html_to_text(prod_description)
        prod_description_en = prod_description.encode("ascii", "ignore")
        prod_description_de = prod_description_en.decode()
        prod_benefits = resp.get('description')
        prod_benefits = prod_benefits.replace(';', '')
        prod_benefits = html_to_text(prod_benefits)
        prod_benefits_en = prod_benefits.encode("ascii", "ignore")
        prod_benefits_de = prod_benefits_en.decode()
        prod_ingredients = resp.get('ingredients')
        # prod_ingredients = html_to_text(prod_ingredients)
        # prod_ingredients_en = prod_ingredients.encode("ascii", "ignore")
        # prod_ingredients_de = prod_ingredients_en.decode()       
        made_without = resp.get('choices_t_mv')       
        price = resp.get('price')
        special_price = resp.get('specialPrice')
        in_stock = resp.get('qty_i')
        prod_img = resp.get('productImages')
        reviews = resp.get('reviews')
        reviews_list = []   
        for review in reviews:
            full_review = review.get('review_detail')
            full_review = html_to_text(full_review)
            full_review_en = full_review.encode("ascii", "ignore")
            full_review_de = full_review_en.decode()
            review_dic={
                'review_name' : review.get('review_nickname'),
                'review_stars' : review.get('rating_value'),
                'date_review' : review.get('created_at'),
                'review_title ': review.get('review_title'),
                'review': full_review_de,
                'verified_purchaser' : review.get('verified_purchaser')

            }
            reviews_list.append(review_dic)


        yield{
            
            'prod_name': prod_name,
            'brand_name': brand_name,
            'prod_category': prod_category,
            'prod_subcategory': prod_subcategory,
            'prod_description': prod_description_de,
            'prod_benefits': prod_benefits_de,
            'prod_ingredients': prod_ingredients,
            'made_without': made_without,
            'price': price,
            'special_price': special_price,
            'in_stock': in_stock,
            'reviewTotal': resp.get('reviewTotal'),
            'reviews': reviews_list,
            'prod_img': prod_img
    }




# class AdorebeautySpider2(scrapy.Spider):
#     name = 'adorebeauty'

#     headers = {
#         'accept': 'application/json, text/plain, */*',
#         'accept-encoding': 'gzip, deflate, br',
#         'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
#         'sec-ch-ua': ' Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91',
#         'sec-ch-ua-mobile': '?0',
#         'sec-fetch-dest': 'empty',
#         'sec-fetch-mode': 'cors',
#         'sec-fetch-site': 'same-origin',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
#         'x-forwarded-proto': 'https'    
#     }


#     def start_requests(self):  
#         yield scrapy.Request(url='https://www.adorebeauty.co.nz/skin-care.html', callback=self.category, headers=self.headers)

#     def category(self, response):
#         for category in response.xpath("//ul[@class='list']/li/a/@href"):
#             category = category.get()
#             yield scrapy.Request(url=f'https://www.adorebeauty.co.nz{category}', callback=self.next_page, headers=self.headers)
    
#     def next_page(self, response):
#         for next_page in response.xpath("//section[@class='pagination']/ul/li/a/@href"):
#             next = next_page.get()
#             url = f'https://www.adorebeauty.com.au{next}'
#             if next:
#                 yield scrapy.Request(url=url, callback= self.times_loop, headers=self.headers
#             )

#     def times_loop(self, response):
#         endpoint_bank=[]
#         for product in response.xpath("//div[@class='product']"):
#             product_url = product.xpath(".//a[@class='product__hero']/@href").get()
#             if product_url not in endpoint_bank:
#                 endpoint_bank.append(product_url)
#                 yield scrapy.Request(url=f'https://www.adorebeauty.co.nz{product_url}',
#                  callback=self.parse_prod_end,
#                   headers=self.headers)
#             else:
#                 continue


#     def parse_prod_end(self, response):
#         for prod_info in response.xpath("//div/section[@class='catalog-product-view']"):
#             prod_name = prod_info.xpath(".//h1/text()").get() 
#             prod_name = prod_name.strip()
          
#             brand_name = prod_info.xpath(".//img/@title").get()
#             prod_categ_bank=[]
#             category=response.xpath(".//li/a/span[@itemprop='name']/text()")
#             for prod_category in response.xpath(".//li/a/span[@itemprop='name']/text()"):
#                 prod_categ_bank.append(prod_category.get())
#             made_without=[]
#             for made in response.xpath("//ul[@class='tickmark-list pad-lr-24']/li/text()"):
#                 made_without.append(made.get())
            

#             price = response.xpath(".//div/span[@class='live-price']/text()").get()
#             in_stock = response.xpath(".//strong[@class='stock-message__info']/text()").get()
#             in_stock = html_to_text(str(in_stock))
#             in_stock_en = in_stock.encode("ascii", "ignore")
#             in_stock_de = in_stock_en.decode()
#             prod_img=[]
#             for link in response.xpath("//div/span/img[@class='mx-auto']/@src"):
#                 prod_img.append(link.get())
#             reviews=[]
#             for review in response.xpath("//ol[@class='all-reviews__list']/li/article/span"):
#                 review_name = review.xpath(".//meta/@content").get()
#                 date_review = review.xpath(".//meta[@itemprop='datePublished']/@content").get()
#                 review_title = review.xpath(".//meta[@itemprop='name']/@content").get()
#                 full_review = review.xpath(".//meta[@itemprop='reviewBody']/@content").get()
#                 review_stars = review.xpath(".//meta[@itemprop='ratingValue']/@content").get()
#                 review_dic={
#                     'review_name' : review_name,
#                     'review_stars' : review_stars,
#                     'date_review' : date_review,
#                     'review_title ': review_title,
#                     'review': full_review
#                 }
#                 reviews.append(review_dic)
#             prod_subcategory=[]
#             for subcat in response.xpath("(//section[@class='product-categories']/ul)[1]/li/a/@title"):
#                 prod_subcategory.append(subcat.get())


#             prod_ingredients_list=[]

#             prod_ingredient= response.xpath("//div[@class='product-tab__content wysiwyg product-tab__content--full-width']/text()")
#             if type(prod_ingredient) == list:  
#                 for ingred in prod_ingredient:
#                     if ingred not in prod_ingredients_list:
#                         prod_ingredients_list.append(ingred.get())
#             else:
#                 prod_ingredient= prod_ingredient.get()
#                 if prod_ingredient not in prod_ingredients_list:
#                     prod_ingredients_list.append(prod_ingredient)
                    

#             pr_ing = response.xpath("//div[@class='product-tab__content wysiwyg product-tab__content--full-width']/div/text()")
#             if type(prod_ingredient)==list:
#                 for ingred in pr_ing:
#                     prod_ingredients_list.append(ingred.get())
#             else:
#                 pr_ing = pr_ing.get()
#                 if pr_ing:
#                     prod_ingredients_list.append(pr_ing)
                
            
#             for ing in response.xpath("//div[@class='product-tab__content wysiwyg product-tab__content--full-width']/p/span/text()"):
#                 ing = ing.get()
#                 if ing not in prod_ingredients_list:
#                     prod_ingredients_list.append(ing)
                    
#             ingr = response.xpath("//div[@class='product-tab__content wysiwyg product-tab__content--full-width']/p/text()")
#             if type(ingr)==list:
#                 for i in ingr:
#                     if i not in prod_ingredients_list:
#                         prod_ingredients_list.append(i.get())                  
#             else:
#                 ingr = ingr.get()
#                 if ingr not in prod_ingredients_list:
#                     prod_ingredients_list.append(ingr)
                    

#             for n in response.xpath("//div[@class='product-tab__content wysiwyg product-tab__content--full-width']/text()"):
#                 n = n.get()
#                 if n:
#                     prod_ingredients_list.append(n)
                    
#             for u in response.xpath("(//div[@class='product-tab__content wysiwyg product-tab__content--full-width']/ul)[1]/li/text()"):
#                 u = u.get()
#                 if u:
#                     prod_ingredients_list.append(u)
                    
#             for y in response.xpath("//div[@class='product-tab__content wysiwyg product-tab__content--full-width']/div/text()"):
#                 y=y.get()
#                 if y:
#                     prod_ingredients_list.append(y)

#             prod_ingredients_list = "".join(map(str, prod_ingredients_list))
#             prod_ingredients_list = html_to_text(prod_ingredients_list)
#             prod_ingredients_list_en = prod_ingredients_list.encode("ascii", "ignore")
#             prod_ingredients_list_de = prod_ingredients_list_en.decode()

#             product_description = []       
#             for descr in response.xpath("//div[@itemprop='description']/p/text()"):
#                 product_description.append(descr.get())

#             for descr in response.xpath("//div[@itemprop='description']/p/span/text()"):
#                 product_description.append(descr.get())
            
#             for descr in response.xpath("//div[@itemprop='description']/div/text()"):
#                 product_description.append(descr.get())

#             product_description =  "".join(map(str, product_description))
#             product_description = html_to_text(product_description)
#             product_description_en = product_description.encode("ascii", "ignore")
#             product_description_de = product_description_en.decode()

#             prod_benefits=[]
#             for benef in response.xpath("(//div[@itemprop='description']/div/ul)[1]/li/text()"):
#                 prod_benefits.append(benef.get())

#             for benef in response.xpath("//div[@itemprop='description']/ul/li/text()"):
#                 prod_benefits.append(benef.get())
            
#             prod_benefits = "".join(map(str, prod_benefits))
#             prod_benefits = html_to_text(prod_benefits)
#             prod_benefits_en = prod_benefits.encode("ascii", "ignore")
#             prod_benefits_de = prod_benefits_en.decode()      

           
#             yield{
            
#                 'prod_name': prod_name,
#                 'brand_name': brand_name,
#                 'prod_category': prod_categ_bank,
#                 'prod_subcategory': prod_subcategory,
#                 'prod_description': product_description_de,
#                 'prod_benefits': prod_benefits_de,
#                 'prod_ingredients': prod_ingredients_list_de, 
#                 'made_without': made_without,
#                 'price': price,
#                 'in_stock': in_stock_de,
#                 'reviews': reviews,
#                 'prod_img': prod_img
#         }


# # configure_logging()
# # runner = CrawlerRunner()

# # @defer.inlineCallbacks
# # def crawl():
# #     yield(runner.crawl(AdorebeautySpider), runner.crawl(AdorebeautySpider2))
# #     reactor.stop()

# # crawl()
# # reactor.run()        

# settings = get_project_settings() 
# process = CrawlerProcess(settings)
# process.crawl(AdorebeautySpider)
# process.crawl(AdorebeautySpider2)
# process.start()
     
        


  
     
        


  