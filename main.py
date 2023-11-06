from requests import get
from bs4 import BeautifulSoup
from time import sleep
from random import randint
from csv import writer
from json import dumps
from re import match
from datetime import datetime


setting_storage_option_cost = True

while setting_storage_option_cost:
    storage_option_cost = input('How much did your drive storage option cost? (USD, no commas) ')
    if not match(r'^\d+(\.\d{2})?$', storage_option_cost):
        print('Hint: USD, no commas, e.g. 1799.99')
    else:
        setting_storage_option_cost = False

setting_storage_option_slot_count = True

while setting_storage_option_slot_count:
    storage_option_slot_count = input('How many drive slots does your storage option have? (no commas) ')
    if not match(r'^\d+$', storage_option_slot_count):
        print('Hint: no commas, pick a number between 1-100 unless you have serious data hoarding issues')
    else:
        setting_storage_option_slot_count = False

url = 'https://serverpartdeals.com/collections/manufacturer-recertified-drives'

payload = { # default: sorted by best sellers
    'pf_t_interface_type': 'interface%3ASATA'
}

def get_price(product):
    price = product.find('span', class_='boost-pfs-filter-product-item-regular-price')
    price = price.text.replace('$', '')
    return price

def get_product_link(product):
    product_link = product.find('a', class_='boost-pfs-filter-product-item-image-link')['href']
    product_link = 'https://serverpartdeals.com' + product_link
    return product_link

def parse_specification(specifications):
    table_rows = specifications.find_all('tr')
    specifications_parsed = {}
    for table_row in table_rows:
        # header
        if table_row.find('th') is not None:
            header = table_row.find('th').text
            if 'datasheet' in header:
                header = 'datasheet'
            else:
                header = header.lower().replace(' ', '_')
        else:
            header = None

        # data
        if 'datasheet' in header:
            data = table_row.find('th').find('a')['href']
        elif table_row.find('td') is not None:
            data = table_row.find('td').text
        else:
            data = None

        specifications_parsed[header] = data
    
    return specifications_parsed

def get_selected_option(description):
    selected_option = description.find('li', class_='selected-option').text
    return selected_option

def get_stock_level(wrapper):
    text = wrapper.find('span', class_='stock-level--text').text.strip().split(' ')
    return text[1] if 'only' in text[0].lower() else text[0]

def get_product_details(product_link):
    # with open('./details.html') as f:
    #     page = f.read()
    page = get(product_link)
    soup = BeautifulSoup(page.text, 'html.parser')
    product_title = soup.find('h1', class_='product-title').text.strip()
    print(f'Fetch Product Details: {product_title}')
    print('-- Specifications')
    specifications = parse_specification(soup.find('div', id='specifications')) # dict
    print('-- Selected Option')
    selected_option = get_selected_option(soup.find('div', class_='product-description')) # str
    print('-- Stock Level')
    stock_level = get_stock_level(soup.find('div', class_='stock-level--wrapper')) # str
    product_details = {
        **specifications,
        'selected_option': selected_option,
        'stock_level': stock_level
    }
    rand_int = randint(30, 45)
    print(f'-- Sleeping {rand_int} seconds')
    sleep(rand_int)
    return product_details
        
def parse_product(product):
    price = get_price(product)
    product_link = get_product_link(product)
    product_details = get_product_details(product_link)

    product_parsed = {
        'price': price,
        'product_link': product_link,
        **product_details
    }
    return product_parsed

def add_calculations(product):
    price = product['price']
    capacity = product['capacity'].lower()
    if 'tb' not in capacity:
        raise ValueError('Why is capacity not in TB?')
    capacity = capacity.replace('tb', '')
    price_per_terrabyte = str(round(eval(f'{price}/{capacity}'),2))
    price_per_slot = str(round(eval(f'({price}+({storage_option_cost}/{float(storage_option_slot_count)}))/{float(capacity)}'), 2))
    product_calculated = {
        **product,
        'price_per_terrabyte': price_per_terrabyte,
        'price_per_slot': price_per_slot
    }
    return product_calculated

def fetch_header_row(products):
    header = []
    for product in products:
        keys = product.keys()
        for key in keys:
            if key not in header:
                header.append(key)
    return header

# with open('./sample.html') as f:
#     page = f.read()
page = get(url, params=payload)
soup = BeautifulSoup(page.text, 'html.parser')
products = soup.find_all('div', class_='boost-pfs-filter-product-item')
products = list(map(parse_product, products))
products = list(map(add_calculations, products))
products.sort(key=lambda x: x['price_per_slot'])
print('Recommeonded Purchase (based on cost per slot):')
print(dumps(products[0], indent=4))

## TO-DO: UPDATE WITH TODAYS DATE AND TIME

with open('results.tsv', 'w') as f:
    csv_writer = writer(f, delimiter='\t')
    header_row = fetch_header_row(products)
    csv_writer.writerow(header_row)
    for product in products:
        product_row = [product[h] if h in product else None for h in header_row]
        csv_writer.writerow(product_row)