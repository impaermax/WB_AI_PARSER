import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

class WBProductParser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
        }

    def parse_product(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            self._validate_wb_page(soup)
            
            return {
                'success': True,
                'url': url,
                'raw_html': response.text,
                'product_id': self._get_product_id(soup),
                'name': self._get_product_name(soup),
                'price': self._get_price(soup),
                'seller': self._get_seller(soup),
                'rating': self._get_rating(soup),
                'characteristics': self._get_characteristics(soup),
                'images': self._get_images(soup)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    def _validate_wb_page(self, soup):
        if not soup.find('div', {'id': 'productNmId'}):
            raise ValueError('Это не страница товара Wildberries')

    def _get_product_id(self, soup):
        return soup.find('div', {'id': 'productNmId'})['content']

    def _get_product_name(self, soup):
        return soup.find('h1', class_='product-page__title').text.strip()

    def _get_price(self, soup):
        price_block = soup.find('div', class_='product-page__price-block')
        return {
            'current': price_block.find('ins').text.strip(),
            'original': price_block.find('del').text.strip() if price_block.find('del') else None
        }

    def _get_seller(self, soup):
        seller_link = soup.find('a', class_='seller-info__name')
        return {
            'id': seller_link['href'].split('/')[-1],
            'name': seller_link.text.strip(),
            'url': urljoin('https://www.wildberries.ru', seller_link['href'])
        }

    def _get_rating(self, soup):
        rating_block = soup.find('div', class_='product-page__rating')
        return {
            'score': rating_block.find('span', class_='product-review__rating').text.strip(),
            'reviews': rating_block.find('a', class_='product-review__count').text.strip().split()[0]
        }

    def _get_characteristics(self, soup):
        chars = {}
        table = soup.find('div', class_='product-params')
        for row in table.find_all('div', class_='product-params__row'):
            key = row.find('span', class_='product-params__label').text.strip().replace(':', '')
            value = row.find('span', class_='product-params__value').text.strip()
            chars[key] = value
        return chars

    def _get_images(self, soup):
        try:
            script = soup.find('script', type='application/ld+json').string
            data = json.loads(script)
            return [image['url'] for image in data['image']]
        except:
            return []
