from collections import defaultdict
from enum import Enum
import re


manachr = ['W', 'U', 'B', 'R', 'G', 'C', '1']

class Mana(Enum):
    WHITE = 0
    BLUE = 1
    BLACK = 2
    RED = 3
    GREEN = 4
    COLORLESS = 5
    GENERIC = 6

def str_to_mana_dict(manacost):
    cost = defaultdict(lambda: 0)
    for c in manacost:
        if c in manachr:
            cost[chr_to_mana(c)] += 1
    num = re.match('\d+', manacost)  # find leading number
    if num:
        cost[Mana.GENERIC] = int(num.group(0))
    return cost

mana_char_to_enum = {
    'W': Mana.WHITE,
    'U': Mana.BLUE,
    'B': Mana.BLACK,
    'R': Mana.RED,
    'G': Mana.GREEN,
    'C': Mana.COLORLESS,
    '1': Mana.GENERIC
}

def chr_to_mana(c):
    if not c or c not in mana_char_to_enum:
        return None
    
    return mana_char_to_enum[c]

class ManaPool():

    def __init__(self, controller=None):
        self.pool = defaultdict(lambda: 0)
        self.controller = controller

    def add(self, mana, amount):
        
        # if len(mana) > 1:
        #     self.add_str(mana)
        # else:
        self.pool[chr_to_mana(mana)] += amount
    def canPay(self, cost_str):
        if not cost_str:
            return False

        cost = str_to_mana_dict(cost_str)
        if not cost:
            return False

        remaining_pool = self.pool.copy()

        # First, try to pay generic mana cost using any available mana
        generic_mana = cost[Mana.GENERIC]
        if generic_mana > 0:
            for mana_type in Mana:
                if mana_type != Mana.GENERIC:
                    available_mana = remaining_pool[mana_type]
                    paid_mana = min(available_mana, generic_mana)
                    remaining_pool[mana_type] -= paid_mana
                    generic_mana -= paid_mana
                    if generic_mana == 0:
                        break

            if generic_mana > 0:
                return False

        # Next, try to pay specific mana costs
        for mana_type, cost_amount in cost.items():
            if mana_type != Mana.GENERIC:
                remaining_pool[mana_type] -= cost_amount
                if remaining_pool[mana_type] < 0:
                    return False

        return True

    def is_empty(self):
        for c in manachr:
            if self.pool[chr_to_mana(c)] != 0:
                return False
        return True

    def determine_costs(self, manacost):
        """ Converts string mana costs to mana dict, resolving hybrid / additional costs"""
        cost = str_to_mana_dict(manacost)

        # hybrid mana costs
        # note the mana symbols will have already been scanned above, so we need to subtract the cost we're not paying
        hybrid = re.findall('\([WUBRGC2]/[WUBRGC]\)', manacost)
        for h in hybrid:
            if self.controller.autoPayMana:
                choice = '0'
            else:
                choice = self.controller.make_choice(
                    'How would you like to pay? 0 (default): {}\t 1: {}\n'.format(h[1], h[3]))

            if choice == '1':
                if h[1] != '2':
                    cost[chr_to_mana(h[1])] -= 1  # already scanned above
            else:  # default 0
                cost[chr_to_mana(h[3])] -= 1
                if h[1] == '2':
                    cost[Mana.GENERIC] += 2


        # TODO: define value of X
        return cost

    def canPay(self, manacost, convoke=False):
        """manacost here is a string, e.g. 2U, or a dict of Manas (e.g. {Mana.BLUE, 3})

        This returns False if not possible, or a cost dict of Mana(Enum)s
         that can be passed to self.pay for actual payment

        This determines generic mana and converts it to actual colored mana

        Note this DOES NOT pay any mana
        """
        if manacost is None:
            return True

        if isinstance(manacost, str):
            manacost = self.determine_costs(manacost)

        genericMana = manacost[Mana.GENERIC]

        if genericMana > 0:
                # Uncomment the user input logic
                if self.controller.autoPayMana:
                    choice = ''
                else:
                    choice = self.controller.make_choice(
                        'How would you like to pay {}? Enter blank for automatic payment, or enter a string of colored mana\n'.format(genericMana))

                if re.match('[WUBRGC]+', choice) and len(choice) == genericMana:
                    for c in choice:
                        manacost[chr_to_mana(c)] += 1
                    genericMana = 0
                else:  # default
                    # print("automatic payment...\n")
                    while genericMana > 0 and any(self.pool[mana] > manacost[mana] for mana in Mana):
                        for mana in Mana:
                            if genericMana == 0:
                                break
                            if self.pool[mana] > manacost[mana]:
                                available_mana = self.pool[mana] - manacost[mana]
                                amount = min(available_mana, genericMana)
                                manacost[mana] += amount
                                genericMana -= amount
                            print(f"Paying {amount} generic mana using {mana}")  # Debugging print statement

        manacost[Mana.GENERIC] = genericMana

        if genericMana > 0:
            print(f"Unpaid generic mana: {genericMana}")  # Debugging print statement
            return False

        for mana in Mana:
            if self.pool[mana] < manacost[mana]:
                print(f"Insufficient {mana}: Pool has {self.pool[mana]}, required {manacost[mana]}")
                return False

        return manacost

    def clear(self):
        self.pool.clear()

    def __repr__(self):
        return '  '.join([str(manatype) + ': ' + str(self.pool[manatype]) for manatype in Mana])
