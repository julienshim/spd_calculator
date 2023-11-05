from requests import get
from bs4 import BeautifulSoup
from random import randint
from time import sleep


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

page = get(url, params=payload)
soup = BeautifulSoup(page.text, 'html.parser')
products = soup.find_all('div', class_='boost-pfs-filter-product-item')
products = list(map(parse_product, products))

