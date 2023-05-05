import re
import json

# dict to convert spelled out numbers to ints
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

def all_effect(card_name, card_text, choose_one):


  with open('all_effect.json') as j:
    target_effect = json.load(j)


  regex = '('
  for p in target_effect:
    regex = regex + p +  '|'
  regex = regex[:-1] + ')'

  # extract target effect phrases 
  found_effect_phrases = re.findall(re.compile(regex), card_text)


  # return effect phrase if found, else return 0 
  if len(found_effect_phrases) != 0 and choose_one != 1:
    #return 0
    return target_effect[found_effect_phrases[0]] 
  
  elif len(found_effect_phrases) != 0 and choose_one == 1:
    return target_effect[found_effect_phrases[0]] 

  else:
      return 0






''' TARGET FUNCTIONS '''

# return the type card targets
def extract_targets(card_name, card_text, choose_one):
  # card name is not currently used in this function but I'm keeping it passed any way just in case

  # import phrases dict from target_phrases.json
  # json structure:
  # phrase to look for : target specification to write
  with open('target_type_phrases.json') as j:
    target_type_phrases = json.load(j)

  # make regex string with phrases to look for target type
  regex = '('
  for p in target_type_phrases:
    regex = regex + p + '|'
  regex = regex[:-1] + ')'

  # extract target type phrases
  found_phrases = re.findall(regex, card_text)


  # return extracted target type if any, else return 0
  if len(found_phrases) != 0 and choose_one != 1:
    return ('\tTargets:\n\t\t\t' + target_type_phrases[found_phrases[0]] + '\n\n')
  
  elif len(found_phrases) != 0 and choose_one == 1:
    return ('\t\tTargets:\n\t\t\t' + target_type_phrases[found_phrases[0]] + '\n\n')   
  else:
    return 0



# return the effect on target type (non-numeric effects)
def extract_static_target_effect(card_name, card_text, choose_one):
  # card name is not currently used in this function but I'm keeping it passed any way just in case


  # import phrases dict from target_effect.json
  # json structure:
  # phrase to look for : target specification to write
  with open('target_effect.json') as j:
    target_effect = json.load(j)

  # make regex string with phrases to look for target effect 
  # this is will only pick up phrases that end with '.' to ensure no conditionals are included 
  # add $ to make sure regex ends with '\.' or else other interestecting phrases will be picked up
  regex = '('
  for p in target_effect:
    regex = regex + p[:-1] + "\." + '|'
  regex = regex[:-1] + ')'

  # extract target effect phrases 
  found_effect_phrases = re.findall(re.compile(regex), card_text)


  # return effect phrase if found, else return 0 
  if len(found_effect_phrases) != 0 and choose_one != 1:
   
   return "\t" + target_effect[found_effect_phrases[0]] + "\n"
  
  elif len(found_effect_phrases) != 0 and choose_one == 1:

    return "\t\t\tPrompt:\n\t\t\t\t" + card_text + '\\n\n\t\t' + target_effect[found_effect_phrases[0]] + ''' if self.controller.make_choice(\n''' + 7*"\t" +'''"Would you like to select this option?")\n'''+ 15*"\t" + '''else None''' +"\n"

  else:
      return 0



# return the numeric effect on target type
def extract_numeric_target_effect(card_name, card_text, choose_one):
  # card name is not currently used in this function but I'm keeping it passed any way just in case

    # make list of numeric based effects
    # cannot use json due to varying numeric values found in each card text
    numeric_effects =  ["Target creature gets (\+*-*\d)/(\+*-*\d) until end of turn\."]#, "Creatures you control get (\+*-*\d)/(\+*-*\d) until end of turn.$"]

    # make regex string with phrases to look for target numeric effects
    regex = '('
    for p in numeric_effects:
      regex = regex + p + '|'
    regex = regex[:-1] + ')'

    # extract target numerics effect phrases
    found_effect_phrases = re.findall(re.compile(regex), card_text)
    
    # return numeric effect phrase if found, else return 0
    if len(found_effect_phrases) != 0 and choose_one != 1:
      text = "\ttargets[0].add_effect('modifyPT', (" + found_effect_phrases[0][1] + ", "  + found_effect_phrases[0][2] + "), self, self.game.eot_time)" + '\n'
      return text.replace("+", "")
    
    elif len(found_effect_phrases) != 0 and choose_one == 1:

      text = "\t\t\tPrompt:\n\t\t\t\t" + card_text + '\\n\n\t\t\t' + "targets[0].add_effect('modifyPT', (" + found_effect_phrases[0][1] + ", "  + found_effect_phrases[0][2] + "), self, self.game.eot_time)" + ''' if self.controller.make_choice(\n''' + 7*"\t" +'''"Would you like to select this option?")\n'''+ 15*"\t" + '''else None''' +"\n"
      return text.replace("+", "")
    
    else:
        return 0
    


def extract_damage(card_name, card_text, choose_one):

  #regex = '^{0} deals (\d*) damage ' + target_match + '.$'
  regex = '{0} deals (\d*) damage to'
  regex = regex.format(card_name)

  matches = None
  try:
    matches = re.search(re.compile(regex), card_text)
  except:
    pass  # +2 Mace is the only card that triggers this except
    # regex hates the + at the start of the string
  if matches is not None and choose_one != 1:
    return '\ttargets[0].take_damage(self, ' + str(matches[1]) + ')\n'
  
  elif matches is not None and choose_one == 1:
    return "\t\t\tPrompt:\n\t\t\t\t" + card_text + '\\n\n\t\t\t' + "targets[0].take_damage(self, ' + str(matches[1]) + ')" + ''' if self.controller.make_choice(\n''' + 7*"\t" +'''"Would you like to select this option?")\n'''+ 15*"\t" + '''else None''' +"\n"
  else:
    return 0


''' CARD EFFECT FUNCTIONS '''

# convert any phrase that requires the use of the create_token function
def extract_token(card_name, card_text):
  # card name is not currently used in this function but I'm keeping it passed any way just in case  
 
  regex = 'Create (.*?) (\d\/\d [A-Za-z]+ [A-Za-z]+) creature tokens with ([A-Za-z]+)'
  matches = re.search(re.compile(regex), card_text)

  if matches is not None:
    return '\t\tself.controller.create_token(\'' + matches.group(2) + '\', ' +num_dict[matches.group(1)] + ', \'' +matches.group(3) + '\')\n'
  else:
    return 0



def extract_gain_life(card_name, card_text, choose_one):
  regex = '.ou gain (\d) life\.'
  matches = re.search(re.compile(regex), card_text)

  if matches is not None and choose_one != 1:
    return '\tself.controller.gain_life(' + matches.group(1) + ')\n'
  
  elif matches is not None and choose_one == 1:
    return "\tPrompt:\n\t\t\t" + card_text + '\\n\n\t\t' + 'self.controller.gain_life(' + matches.group(1) + ')' + ''' if self.controller.make_choice(\n''' + 6*"\t" +'''"Would you like to select this option?")\n'''+ 14*"\t" + '''else None''' +"\n"

  else:
    return 0





# return that amount of draw cards if any
def extract_draw(card_name, card_text, choose_one):
  # card name is not currently used in this function but I'm keeping it passed any way just in case
  if "Cycling" in card_text:
    return 0
  ctext = ""
  for word in card_text.split():
    if word in num_dict:
      word = num_dict[word]
    ctext += word 
    ctext += " "
  card_text = ctext
  
  text = ''
  regex = 'Draw (\d) cards?(, then discard (\d) cards?)?\.'
  #regex = "Draw (.*?) cards\."
  matches = re.search(re.compile(regex), card_text)

  if matches is not None and choose_one != 1:
    if matches.group(1) is not None:
      text += ('\tself.controller.draw(' + matches.group(1) + ')\n')
    if matches.group(2) is not None:
      text +=('\tself.controller.discard(' + matches.group(3) + ')\n')

  if matches is not None and choose_one == 1:
    if matches.group(1) is not None:
      text += ('self.controller.draw(' + matches.group(1) + ')')
    if matches.group(2) is not None:
      text +=(' and self.controller.discard(' + matches.group(3) + ')')


  if len(text) != 0 and choose_one != 1:
    return text
  elif len(text) != 0 and choose_one == 1:
    return "\tPrompt:\n\t\t\t" + card_text + '\\n\n\t\t' + text + ''' if self.controller.make_choice(\n''' + 6*"\t" +'''"Would you like to select this option?")\n'''+ 14*"\t" + '''else None''' +"\n"


  else:
    return 0
