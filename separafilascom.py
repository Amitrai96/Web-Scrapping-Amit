import scrapy,json
from scrapy.http import Request
from scrapping.data_format import product_data
from scrapping.post_data import post_data

class SeparafilascomSpider(scrapy.Spider):
    name = "separafilascom"
    allowed_domains = ["www.separafilas.cl"]
    start_urls = ["https://www.separafilas.cl/"]

    def parse(self, response):
        cat_lst = response.xpath('//div[@class="elementor-button-wrapper"]/a/@href').getall()
        cat_lst.append('https://www.separafilas.cl/')
        for cat_link in cat_lst:
            yield Request(cat_link, callback=self.parse_pages)

    def parse_pages(self, response):

        products_url = response.xpath('//div[@class="product-element-top"]/a/@href').extract()
        for product_url in products_url:
            abs_product_url = response.urljoin(product_url)
            yield Request(abs_product_url, callback=self.parse_products)

    def parse_products(self, response):
        item = product_data.copy()
        prod_name= response.xpath('//h1[@itemprop="name"]/text()').get()
        category = response.xpath('//*[contains(text(),"Categoría: ")]/a/text()').get()
        price = response.xpath('//p[@class="price"]/del/span/bdi/text()').get('')
        price_after_discount= response.xpath('//p[@class="price"]/span/bdi/text() | //p[@class="price"]/ins/span/bdi/text()').get('')
        if price == '':
            price = price_after_discount
        perc_disc = response.xpath('//div[@class="product-images-inner"]//span[@class="onsale product-label"]/text()').get('').replace('-','').replace('%','')
        data_json = response.xpath('//script[@type="application/ld+json"][contains(text(),"sku")]/text()').get()
        images_url = list()
        images_name = list()
        data_json = json.loads(data_json)
        sku = data_json['@graph'][1]['sku']
        long_description = data_json['@graph'][1]['description']
        images_ur = data_json['@graph'][1]['image']
        image_name = images_ur.split('/')[-1]
        images_url.append(images_ur)
        images_name.append(image_name)
        product_url  = data_json['@graph'][1]['url']


        if price:
            price = str(price.replace('.', ''))
        else:
            price = 0

        if price_after_discount:
            price_after_discount = str(price_after_discount.replace('.', ''))
        else:
            price_after_discount = 0

        if int(price) != 0:
            status = 'Active'
        else:
            status = 'InActive'
        stock_lst = [{
            "quantity": "",
            "comment": ""
        }]
        #
        short_description = response.xpath('//div[@class="product-short-description"]/a/text()').get().strip()
        breadcrum_lst = response.xpath('//div[@class="single-breadcrumbs"]/nav//text()').extract()
        breadcrum_lst = [x.strip() for x in breadcrum_lst if x.strip()]
        breadcrum = "/".join(breadcrum_lst)
        item['code'] = "XCF"
        item['name'] = prod_name
        item['sku'] = sku
        item['url_scraped'] = product_url
        item['price'] = price
        item['percent_discount'] = perc_disc
        item['price_discount'] = price_after_discount
        item['tax'] = ''
        item['price'] = price
        item['price_included_taxes'] = price_after_discount
        item['price_mt2'] = 'null'
        item['price_mtl'] = 'null'
        item['stock'] = stock_lst
        item['images_url'] = images_url
        item['images_name'] = images_name
        item['category'] = category
        item['route_product'] = breadcrum
        item['short_description'] = short_description
        item['long_description'] = long_description
        item['pdf'] = ''
        item['dimensions'] = ''
        item['main_color'] = ''
        item['glossy_or_matte'] = ''
        item['main_material'] = ''
        item['origin'] = 'Spain'
        item['Status'] = status


        if response.status_code == 200 or response.status_code == 201:
            self.logger.info('Data saved successfully:', response.json())
            yield item
        else:
            self.logger.error('Error saving data:', response.status_code, response.text, item)

