# This driver calls the function from the developing_converter to extract the code related to the card text
# It does attempt to account for cards with choose one statements

import pandas as pd
import developing_converter
import re

num_dict = {
  'a' : '1',
  'one': '1',
  'two': '2',
  'three': '3',
  'four': '4',
  'five': '5',
  'six': '6',
  'seven': '7',
  'eight': '8',
  'nine': '9',
  'ten': '10',
  'X' : 'X'
}

def write_header(name):
  f_out.write("#" * 30)
  f_out.write("\n")
  f_out.write(name)
  f_out.write("\n")

def extract_content(name, text, choose_one):
  choose_one = 0
  test_list = []
  test_list.append(developing_converter.extract_targets(name, text, choose_one))
  test_list.append(developing_converter.extract_static_target_effect(name, text, choose_one))
  test_list.append(developing_converter.extract_numeric_target_effect(name, text, choose_one))
  #test_list.append(converter2.extract_token(name, text))
  test_list.append(developing_converter.extract_draw(name, text, choose_one))
  test_list.append(developing_converter.extract_damage(name, text, choose_one))
  test_list.append(developing_converter.extract_gain_life(name, text, choose_one))
  test_list.append(developing_converter.all_effect(name, text, choose_one))

  card_content = []
  for element in test_list:
    if element != 0:
      card_content.append(element)
  return card_content



def extract_content_choose(name, text):
  choose_one = 1
  test_list = []

  if "target" in text or "Target" in text:
     test_list.append(developing_converter.extract_targets(name, text, choose_one))

  test_list.append(developing_converter.extract_static_target_effect(name, text, choose_one))
  test_list.append(developing_converter.extract_damage(name, text,choose_one))
  test_list.append(developing_converter.extract_numeric_target_effect(name, text, choose_one))
  #test_list.append(converter2.all_effect(name, text, choose_one))
  test_list.append(developing_converter.extract_draw(name, text, choose_one))
  test_list.append(developing_converter.extract_gain_life(name, text, choose_one))
  

  card_content = []
  for element in test_list:
    if element != 0:
      card_content.append(element)
  return card_content



''' MAIN '''

if __name__ == "__main__":
  # open output file
  f_out = open("output2.txt", "w")

  # read in csv
  df = pd.read_csv('text_to_cost.csv')  # only has name/text columns

  # remove cards where name contains '//'
  df = df[df['name'].str.contains('//') == False]

  # for each row in the dataframe
  for index, row in df.iterrows():
    # grab info
    name = str(row['name'])
    text = str(row['text'])
    type = str(row['type'])


    
    ctext = ""
    for word in text.split():
      if word in num_dict:
        word = num_dict[word]
      ctext += word 
      ctext += " "
    text = ctext

    choose_statement = 0 

    '''
    regex = ".hoose (\d)"
    matches = re.search(re.compile(regex), text)
    
    if matches is not None:
      choose_statement = 1

    if choose_statement == 1:
      regex = ".hoose (\d)"
      matches = re.search(re.compile(regex), text)
      
      write_header(name)
      f_out.write('\n')
  
      f_out.write("\t\tPrompt:\n\t\t\t Choose " + matches.group(1) + ". Enter "None" if you don't wish to select option\n\n")
      regex = "\• [A-Za-z,;'\"\\s\d]+[.?!]"
      matches = re.findall(regex, text)
      #len(matches)
      for i in range(len(matches)):
        card_content = extract_content_choose(name, matches[i][2:])

        for i in range(len(card_content)):
          if(card_content[i] != 0):
            f_out.write(card_content[i])
  
   '''

  
    card_content = extract_content(name, text, choose_statement)

    # only cards that have found phrases will be outputted 
    if (type == "Instant" or type == "Sorcery") and len(card_content) > 1: # and 0 not in test_list: #is not None and extract_gain_life is not None:

      write_header(name)
      f_out.write('\n')

      for i in range(len(card_content)):
        if(card_content[i] != 0):
          f_out.write(card_content[i])
      f_out.write('\n\n')


  f_out.close()
