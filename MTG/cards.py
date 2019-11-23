import sys
import pickle
import math
import re
from collections import namedtuple

from MTG.parsedcards import *
from MTG.exceptions import *
from MTG import abilities
from MTG import triggers
from MTG import mana
from MTG import utils
from MTG import permanent


SETPREFIX = ['M15', 'sm_set', 'cube']
name_to_id_dict = {}
id_to_name_dict = {}

# compile all the dictionaries from different parsed sets
for pre in SETPREFIX:
    try:
        with open('data/%s_name_to_id_dict.pkl' % pre, 'rb') as f:
            name_to_id_dict.update(pickle.load(f))
    except:
        print("%s name_to_id_dict not found\n" % pre)


id_to_name_dict = {value: key for key, value in name_to_id_dict.items()}


def id_to_name(ID):
    return id_to_name_dict.get(ID, None)


def name_to_id(name):
    return name_to_id_dict.get(name, None)


def str_to_class(str):
    return getattr(sys.modules[__name__], str)


def card_from_name(name, get_instance=True):
    ID = name_to_id(name)
    if ID is not None:
        if get_instance:  # gets instance of class
            # default card class generated by parse_cards.py
            return str_to_class(ID)()
        else:
            return str_to_class(ID)
    else:
        raise CardNotImplementedException


def read_deck(filename):
    """File format:
    NUM CARDNAME

    e.g.
    10 Plains
    10 Oreskos Swiftclaw

    """
    with open(filename, 'r') as f:
        file = f.read().split("\n")
        deck = []
        for line in file:
            try:
                i = line.index(" ")
                num = int(line[:i])
                for j in range(num):  # add NUM copies of CARDNAME
                    card = card_from_name(line[i + 1:])
                    if card:
                        deck.append(card)
                        # print(deck[-1].name)
                    else:
                        pass
                        # print("card {} does not exist\n".format(line[i+1:]))
            except:
                raise DecklistFormatException

    return deck


def add_activated_ability(cardname, cost, effect, target_criterias=None, prompts=None):
    if not name_to_id(cardname):
        return
    card = card_from_name(cardname, get_instance=False)
    is_mana_ability = 'mana.add' in effect

    costs = utils.parse_ability_costs(cost)

    if not card.activated_abilities:  # hasn't been initiated yet
        card.activated_abilities = []

    if target_criterias:
        target_criterias = utils.parse_targets(target_criterias)
    else:
        target_criterias = None

    # same signature as abilities.ActivatedAbilities.init
    card.activated_abilities.append((costs, effect, target_criterias, prompts, is_mana_ability))


def add_targets(cardname, criterias=[lambda self, p: True], prompts=None):
    if not name_to_id(cardname):
        return
    card = card_from_name(cardname, get_instance=False)
    if not prompts:
        prompts = ["Choose a target\n"] * len(criterias)

    criterias = utils.parse_targets(criterias)

    card.target_criterias = criterias
    card.target_prompts = prompts


'''
@outcome: function which takes in [CARD], targets, is_legal_target
'''
def add_play_func_with_targets(cardname, outcome=lambda self, t, l: True):
    if not name_to_id(cardname):
        return
    card = card_from_name(cardname, get_instance=False)

    def play_func(self):
        legality = self.target_legality()
        if any(legality):
            outcome(self, self.targets_chosen, legality)
            if not self.is_aura:
                self.controller.graveyard.add(self)

            return True
        else:
            # no valid target on a spell that requires target
            self.controller.graveyard.add(self)
            return False

    card.play_func = play_func


def add_play_func_no_target(cardname, outcome=lambda self: True):
    if not name_to_id(cardname):
        return
    card = card_from_name(cardname, get_instance=False)

    card.play_func = outcome


def add_aura_effect(cardname, effects, target_criterias=['creature']):
    add_targets(cardname, target_criterias)
    add_play_func_with_targets(cardname, lambda self, targets, l: permanent.make_aura(self, targets[0]))

    # add aura enchant effects
    card = card_from_name(cardname, get_instance=False)
    card.continuous_effects = effects

def add_trigger(cardname, condition, effect, requirements=None,
                target_criterias=None, target_prompts=None, intervening_if=None):
    """
    Each effect is a function of the form
        lambda self: do_something

    It will be passed into the stack as
        play.Play(lambda: effect(self))

    where self is the source of the trigger (the permanent)
    """
    if not name_to_id(cardname):
        return
    card = card_from_name(cardname, get_instance=False)

    if not requirements:
        requirements = lambda self: True

    # make it a variable specific to card rather than a card.Card class var
    # normally, trigger_listeners is defined in card.Card,
    # and our parsed card classes just inherit that
    if card.triggers == {}:
        card.triggers = {}

    if condition not in card.triggers:
        card.triggers[condition] = []


    if target_criterias:
        target_criterias = utils.parse_targets(target_criterias)
        if not target_prompts:
            target_prompts = ["Choose a target\n"] * len(target_criterias)
    else:
        target_criterias = None

    # each element in the dict is a list of triggers, since there could be multiple abilities
    # that trigger from the same effect, e.g. tap AND draw a card on etb
    # each of them will go into a separate play.Play object and be put onto the stack
    card.triggers[condition].append((effect, requirements,
                                     target_criterias, target_prompts, intervening_if))

def add_static_effect(cardname, apply_to, name, value, toggle_func=lambda eff: False):
    if not name_to_id(cardname):
        return
    card = card_from_name(cardname, get_instance=False)


    if card.static_effects == []:
        card.static_effects = []

    card.static_effects.append((apply_to, name, value, toggle_func))



def indentation_lv(s):
    """ Must be tab indented """
    lv = 0
    for i in s:
        if i == '\t':
            lv += 1
        else:
            break
    return lv



def parse_card_from_lines(lines, log=None):
    """ Lines are formatted according to 'data/cards.txt'
    
    Each set of lines correspond to all abilities/effects of a single card
    """
    stage = 'new card'
    substage = ''
    name = ''

    effects = []
    abilities = []
    targets = []
    target_prompts = []
    _triggers = []  # _ since we import MTG.triggers

    aura_targets = []
    aura_effects = []

    static_effects = []


    prev_ind_lv = 0
    prev_line = ''
    lines.append('')


    # we actually only parse a line until we're certain there's nothing following it
    # so everytime we read a new line,
    #   we parse the last line and store our new line in prev_line
    for line in lines:
        ind_lv = indentation_lv(line)
        line = line.lstrip()

        if line and line[0] == '#':
            continue

        if not prev_line:
            prev_line = line
            prev_ind_lv = ind_lv
            continue

        if ind_lv > 1 + prev_ind_lv:  # line continuation
            prev_line += ' ' + line
            continue  # wait to parse until we've read in
                      # the entire multi-line statement


        # ok now we're ready to parse the previous line
        # swap the two vars so we're processing line = prev_line
        line, prev_line = prev_line, line
        ind_lv, prev_ind_lv = prev_ind_lv, ind_lv

        if stage == 'new card':  # read in card name
            name = line
            stage = 'effects'
            continue

        if ind_lv == 1:
            if line == 'Abilities:':
                stage = 'abilities'
                continue
            elif line == 'Targets:':
                stage = 'targets'
                continue
            elif line == 'Triggers:':
                stage = 'triggers'
                continue
            elif line == 'Aura:':
                stage = 'aura'
                continue
            elif line == 'StaticEffects:':
                stage = 'static'
                continue
            else:
                stage = 'effects'


        if stage == 'effects':  # read in card effects
            effects.append(line)

        elif stage == 'abilities':
            if ind_lv == 2:
                # split ability by 'cost: effect'
                index = line.index(":")
                abilities.append((line[:index], line[index+2:], []))

            elif ind_lv == 4:  # prev line is targets
                if line[0] != "'":
                    line = 'lambda self, p: ' + line
                abilities[-1][-1].append(line)

        elif stage == 'targets':
            if ind_lv == 2:
                # shortcut targets, like 'creature', are surrounded in quotes and will be kept intact
                # otherwise, we should prefix it with the correct lambda signature for add_target()
                if line[0] != "'":
                    line = 'lambda self, p: ' + line
                targets.append(line)

            elif ind_lv == 4:  # previous line should be 'Prompt:'
                target_prompts.append(bytes(line, "utf-8").decode("unicode_escape"))  # remove quotes, convert to string

        elif stage == 'triggers':
            if ind_lv == 2:  # new trigger
                # [condition, [list of effects](, optional trigger requirements, targets, intervening-if's)]
                _triggers.append([line, [], None, [], None])
            elif ind_lv == 3:
                    _triggers[-1][1].append(line)  # trigger effect
            elif ind_lv == 4:
                if line == 'Conditioned On:':  # whenever ...
                    substage = 'requirements'
                elif line == 'If:':  # ... if ...  -- MUST COME AFTER 'Conditioned On' if both present
                    substage = 'intervening if'
                elif line == 'Targets:':
                    substage = 'targets'

            elif ind_lv == 5:
                if substage == 'requirements':  # optional trigger requirements
                    _triggers[-1][2] = "lambda self: " + line

                if substage == 'intervening if':
                    _triggers[-1][4] = "lambda self: " + line  # intervening-if


                elif substage == 'targets':
                    if line[0] != "'":
                        line = 'lambda self, p: ' + line
                    _triggers[-1][3].append(line)



        elif stage == 'aura':
            if ind_lv == 2:
                if line == 'Targets:':
                    pass
                else:
                    aura_effects.append(line)

            if ind_lv == 3:   # prev line == 'Targets:':
                if line[0] != "'":
                    line = 'lambda self, p: ' + line
                aura_targets.append(line)

        elif stage == 'static':
            if ind_lv == 2:
                static_effects.append([line])  # apply_to
            elif ind_lv == 3:
                static_effects[-1].append(line)  # effect_name, effect_value, toggle_func


    # print(name, targets, abilities, _triggers, effects)
    str_to_exe = ""

    name = '"' + name + '"'

    if abilities:
        for cost, effect, ability_targets in abilities:
            ability_targets = '[' + ', '.join(ability_targets) + ']'
            str_to_exe += "add_activated_ability(%s, %r, %r, %s)\n" % (name, cost, effect, ability_targets)


    if targets:
        targets = '[' + ', '.join(targets) + ']'
        str_to_exe += "add_targets(%s, %s, prompts=%r)\n" % (
                    name, targets, target_prompts)


    # we need to use awkward '[' + ', '.join(..) + ']' for two reasons:
    #   - converting list to str for exec()
    #   - removing the quotation marks from the inner elements of the list,
    #     turning them from strings into statements

    if _triggers:
        for trig in _triggers:
            trig[1] = '[' + ', '.join(trig[1]) + ']'
            trig[3] = '[' + ', '.join(trig[3]) + ']'
     
            # todo: also parse target prompts
            str_to_exe += "add_trigger(%s, triggers.triggerConditions[%r], %r, %s, %s, intervening_if=%s)\n" % (
                                    name, *trig)


    if effects:
        if not targets:
            effects = 'lambda self: [' + ', '.join(effects) + ']'
            str_to_exe += "add_play_func_no_target(%s, %s)\n" % (name, effects)

        else:
            effects = ("lambda self, targets, is_legal_target: ["
                      + ', '.join(effects) + ']')
            str_to_exe += "add_play_func_with_targets(%s, %s)\n" % (
                                name, effects)

    if aura_effects:
        aura_effects = '[' + ', '.join(aura_effects) + ']'
        aura_targets = '[' + ', '.join(aura_targets) + ']'
        str_to_exe += "add_aura_effect(%s, %r, %s)\n" % (name, aura_effects, aura_targets)

    if static_effects:
        for eff in static_effects:
            str_to_exe += "add_static_effect({}, {}, {}, {}, {})\n".format(name,
                                            *eff)

    if log and str_to_exe:
        log.write(str_to_exe + "\n")

    exec(str_to_exe)


def setup_cards(FILES=['data/m15_cards.txt', 'data/cube_cards.txt']):
    """
    Read in cards information from data/cards.txt

    Logs in setup_cards.log

    """

    f_log = open('setup_cards.log', 'w')

    for name in FILES:
        with open(name, 'r') as f:
            lines = []  # buffer

            for line in f:
                line = line.rstrip()
                if not line:
                    continue

                if line[:3] == '###':  # end of a card
                    parse_card_from_lines(lines, f_log)
                    lines = []
                else:  # wait to parse cards until we've read in all information about a card
                    lines.append(line)