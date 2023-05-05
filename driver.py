# This driver calls the function from the converter to extract the code related to the card text
# It does not attempt to account for cards with choose one statements (the developing one does)



import pandas as pd
import converter

def write_header(name):
  f_out.write("#" * 30)
  f_out.write("\n")
  f_out.write(name)
  f_out.write("\n")


''' MAIN '''

if __name__ == "__main__":
  # open output file
  f_out = open("output.txt", "w")

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

    # create list of all the found phrases
    # make sure to append found phrases in correct order

    test_list = []
    test_list.append(converter.extract_targets(name, text))
    test_list.append(converter.extract_static_target_effect(name, text))
    test_list.append(converter.extract_numeric_target_effect(name, text))
    test_list.append(converter.extract_token(name, text))
    test_list.append(converter.extract_draw(name, text))
    test_list.append(converter.extract_damage(name, text))
    test_list.append(converter.extract_gain_life(name, text))

    # create new list with only found phrases in test_list
    card_content = []
    for element in test_list:
      if element != 0:
        card_content.append(element)

    # only cards that have found phrases will be outputted  (only interested in Instant/Sorcery)
    if (type == "Instant" or type == "Sorcery") and len(card_content) > 1: # and 0 not in test_list: #is not None and extract_gain_life is not None:

      write_header(name)
      f_out.write('\n')

      for i in range(len(test_list)):
        if(test_list[i] != 0):
          f_out.write(test_list[i])
      f_out.write('\n')
  

  f_out.close()
