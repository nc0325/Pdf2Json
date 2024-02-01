import pandas as pd
import pdfquery
import functools
import numpy as np
from datetime import datetime
import io, json

def validate_and_format_date(date_str):
    date_str_no_space = date_str.split(' ')[-1].strip()

    try:
        # Try to parse the date string using the expected format (e.g., '%m/%d/%Y')
        valid_date = datetime.strptime(date_str_no_space, '%d/%m/%Y')
        return valid_date.strftime('%d/%m/%Y')
    except ValueError:
        # If there is a ValueError, return the default date
        return '01/01/1900'

# Function to validate and format numeric value
def validate_and_format_numeric(numeric_str):
    numeric_str_no_commas = numeric_str.replace(',', '').strip()

    if numeric_str_no_commas.isdigit():
        return numeric_str_no_commas
    else:
        # If not a valid number, return the default numeric value
        return '99999999'

def cmp_element(elementA, elementB):
  aX = float(elementA.attrib['x0'])
  aY = float(elementA.attrib['y0'])
  bX = float(elementB.attrib['x0'])
  bY = float(elementB.attrib['y0'])

  if(aY > bY + 5 ):
    return -1
  if(aY >= bY and aY <= bY + 5): 
    if(aX < bX): 
      return -1
  return 1

def parseItem(item_data):
  if(item_data.__len__() < 20):
    return {}
  
  if item_data.__len__() > 27:
    item_data = list(filter(lambda p: p != "" , item_data))

  # If Service History have
  while item_data.__len__() < 26:
    item_data = np.insert(item_data,13,'')
  
  if item_data.__len__() < 27:
    # Check if SERVICE PRINT have
    if all('SERVICE PRINT' in text for text in item_data):
      item_data = np.insert(item_data,13,'')
    else:
      item_data = np.insert(item_data,16,'')

  if(item_data[0].strip() == '10180'):
    print(item_data)
    print(item_data)

  # Split fuel data
  fuel_data = item_data[11].split(', ')
  while fuel_data.__len__() < 3:
    fuel_data = np.insert(fuel_data,fuel_data.__len__(),'')

  # Get Previous regisration and service history 
  prev_registration = ''
  service_history = ''
  if item_data[13].find('Previous Registration No') > -1 or item_data[14].find('Service History') > -1 :
    prev_registration = item_data[13]
    service_history = item_data[14]
  else:
    prev_registration = item_data[14]
    service_history = item_data[13]

  prev_registration = prev_registration.split(': ')[-1]
  service_history = service_history.split('-')[-1]


  item = {}
  item['lot']                 = item_data[0].strip()
  item['registration']        = item_data[1].strip()
  item['make_model']          = item_data[2].strip()
  item['colour']              = item_data[3].strip()
  item['mileage']             = validate_and_format_numeric(item_data[4].strip())
  item['row']                 = item_data[5].strip()
  item['running_order']       = item_data[6].strip()
  item['registration_date']   = validate_and_format_date(item_data[7].strip())
  item['body_type']           = item_data[8].strip()
  item['location']            = item_data[9].strip()
  item['mileage_warranty']    = item_data[10].strip()
  item['fuel_type']           = fuel_data[0].strip()
  item['v5_location']         = fuel_data[1].strip()
  item['MOT']                 = validate_and_format_date(fuel_data[2].strip())
  item['owners']              = item_data[12].strip()
  item['previous_registration']= prev_registration.strip()
  item['service_history']     = service_history.strip()
  item['extras']              = item_data[15].strip()
  item['service_history_detail'] = item_data[16].strip()
  item['supplier']            = item_data[17].strip()
  item['at_retail']           = validate_and_format_numeric(item_data[19].strip())
  item['price_CAP_retail']    = validate_and_format_numeric(item_data[21].strip().split(' ')[0])
  item['price_clean']         = validate_and_format_numeric(item_data[22].strip())
  item['price_average']       = validate_and_format_numeric(item_data[24].strip())
  item['price_below']         = validate_and_format_numeric(item_data[26].strip())


  return item

def getItems(text_data):
  arr = np.array(text_data)

  startIndex = np.where(arr == '/ Location')[0][0] + 1
  belowIndexes = np.where(arr == "Below:")[0]
  items = []
  for endIndex in belowIndexes:
    item_data = arr[startIndex:endIndex + 2]
    item = parseItem(item_data)
    items.append(item)
    startIndex = endIndex + 2
  return items

#read the PDF
pdf = pdfquery.PDFQuery('test.pdf')

pdf.load(0)

title_element = pdf.pq('LTTextBoxHorizontal').eq(0)

result = {}
if title_element:
  result['document_date'] = title_element.text()
else:
  result['document_date'] = ''
  
result['JSON_creation_date_time'] = datetime.today().strftime('%d/%m/%Y %H.%M')


pdf.load()

# Get the number of pages

number_of_pages = pdf.doc.catalog['Pages'].resolve()['Count']
print(number_of_pages)

page_index = 0
items = []
while page_index < number_of_pages:
  pdf.load(page_index)
  # Use CSS-like selectors to locate the elements
  text_elements = pdf.pq('LTPage *')
  text_elements = filter(lambda p: p.text and p.text != "" , text_elements)
  text_elements = sorted(text_elements, key = functools.cmp_to_key(cmp_element))

  # Extract the text from the elements
  texts = [t.text.strip() for t in text_elements]

  items = items + getItems(texts)
  page_index = page_index + 1

result['source_pdf_pages'] = number_of_pages
result['vehicles'] = items

with io.open('output.json', 'w', encoding='utf-8') as f:
  f.write(json.dumps(result, ensure_ascii=False))
  print(f'Object successfully saved ')

