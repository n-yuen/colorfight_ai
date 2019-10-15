from colorfight import Colorfight, Position
import time
import math
import random
from colorfight.constants import BLD_GOLD_MINE, BLD_ENERGY_WELL, BLD_FORTRESS, BUILDING_COST

LOBBY_NAME = 'official_final'
USERNAME = 'xD'

class Agent:
    def __init__(self):     # Constants to be used in desirability functions. Sorry for the terrible names; I was under time pressure.
        self.bdw = 1.35     # Building weight - how much the AI 'wants' to build buidlings
        self.upg = 100.0    # Upgrade weight - how much the AI 'wants' to upgrade buildings
        self.dfw = 100      # Unused constant
        self.l3u = 0.8      # Unused constant
        self.cdw = -1.0     # Cell Danger weight - how much the AI takes into account cell danger, or the number of nearby enemy cells
        self.bcdw = -50     # Building Cell Danger weight - how much the AI avoids building resource buildings when there is high cell danger
        self.cgw = 1.0      # Cell gain weight - how much the AI takes into account income gain from a cell
        self.dpw = 500.0    # Delta perim weight - how much the AI values a contiguous area
        self.oew = 1.0      # Enemy energy weight - how much the AI values taking out enemy energy wells
        self.ogw = 1.0      # Enemy gold weight - how much the AI values taking out enemy gold mines
        self.huw = 120.0    # Home upgrade weight - how much the AI values upgrading the home
        self.twb = -4.0     # Building tax weight - how much the AI values the tax amount from buildings
        self.twa = -140.0   # Attacking tax weight - how much the AI values the tax amount from new cells
        self.str = 500.0    # Fortress (stronghold) weight - how much the AI likes building fortresses
        self.shu = 0.7      # Fortress upgrade weight - how much the AI likes upgrading fortresses
        self.e_threshold0 = 0   # Minimum energy

    def e_weight(self):     # Formula for energy value. It is a piecewise function with linear components. In the early game, energy is worth more.
        if game.turn > 300:
            return 400 - game.turn/2
        return 450 - game.turn

    def g_weight(self):     # Formula for gold value. It is also a piecewise function with linear components. In the late game, gold is worth more.
        if game.turn < 100:
            return 170 + game.turn
        elif game.turn < 200:
            return 130 + game.turn * 2.4
        else:
            return game.turn*3.4

    def g_threshold(self):  # Floor for gold. The AI will not spend gold so that total gold drops below the floor.
                            # Though there are more elegant solutions, this was a very consistent way to make the AI save up gold to win the game.
        if game.turn < 320:
            return 0
        return (game.turn - 320) * 3700

    def e_threshold(self):  # Floor for energy, always zero.
        return 0

    def tax_value(self, cell):  # Tax formula, very basic and didn't have time to do the actual calculations.
        me = self.game.me
        return me.tax_amount/(me.gold+me.energy)

    def cell_danger(self, cell):    # Cell danger - look in a 5x5 box around each cell and count the number of enemy cells and multiply by proximity.
        cell_danger = 0
        for dx in range(-5, 5):
            for dy in range(-5, 5):
                if (abs(dx) + abs(dy) != 0) and cell.position.x + dx > 0 and cell.position.y + dy > 0 \
                    and cell.position.x + dx < self.game.width and cell.position.y + dy < self.game.width:
                    owner = self.game.game_map[cell.position + Position(dx, dy)].owner
                    if owner != self.game.me.uid and owner != 0:
                        cell_danger += 1.0 / (abs(dx) + abs(dy))

      
        return cell_danger

    def home_dist(self, cell):  # Unused
        return 0
        #for h in self.game.home



    def cell_gain(self, cell):  # Looks to see what we could get from a cell, if gold or energy is more advantageous.
        return max(cell.gold * self.g_weight(), cell.energy * self.e_weight())

    def delta_perim(self, cell):    # Looks around a potential cell to see if attacking it would make territory more contiguous
        rtn = 0
        for pos in cell.position.get_surrounding_cardinals():
            c = self.game.game_map[pos]
            if c.owner == game.uid:
                rtn += 1

        return rtn

    def opp_value(self, cell):  # Increase cell value if opponent has a resource building on it.
        if cell.owner != game.uid:
            if cell.building == BLD_GOLD_MINE:
                return self.ogw * cell.building.level
            if cell.building == BLD_ENERGY_WELL:
                return self.oew * cell.building.level

        return 0

    # def build_weight(self, cell):
    #     return (cell.gold * self.g_weight(), cell.energy * self.e_weight())

    def build_weight(self, cell):

      # Weight for resource buildings. It takes into account cell danger and tax (both negative).
      flatX = self.bcdw * self.cell_danger(cell) + self.twb * self.tax_value(cell)

      # Weight for strongholds. It only takes into account cell danger (positive).
      str_weight = self.cell_danger(cell) * self.str

      # Returns a tuple with these weights for further evaluation
      return (self.bdw* (cell.gold * self.g_weight() + flatX), self.bdw* (cell.energy * self.e_weight() + flatX), self.bdw* str_weight)

    def upg_desire(self,cell):

      # Takes in the relevant variables to upgrade a building.
      cell_danger = self.cdw * self.cell_danger(cell)
      cell_gain = self.cgw * self.cell_gain(cell)
      delta_perim = self.dpw * self.delta_perim(cell)
      opp_value = self.opp_value(cell)

      #home_dist, hdw = self.home_dist(cell), 

      # print(cell_danger + cell_gain +  delta_perim  + opp_value)
      rtn = self.upg(cell_danger + cell_gain +  delta_perim  + opp_value)
      if cell.building.name == 'fortress':
          rtn *= self.shu
      return rtn

    def atk_desire(self, cell):
      # Takes in the relevant variables to attack a cell.
      cell_danger = self.cdw * self.cell_danger(cell)
      cell_gain = self.cgw * self.cell_gain(cell)
      delta_perim = self.dpw * self.delta_perim(cell)
      opp_value = self.opp_value(cell)
      tax_weight = self.twa * self.tax_value(cell)

      #home_dist, hdw = self.home_dist(cell), 

      # print(cell_danger + cell_gain +  delta_perim  + opp_value)
      return cell_danger + cell_gain +  delta_perim  + opp_value

    def play_game(self, game, room=LOBBY_NAME, username=USERNAME, password='abcde'):
        self.game = game
        game.connect(room = room)
        if not game.register(username = username, \
                password = password):
            print("Failed registration? ????")
            return
        while True:

            # The command list we will send to the server
            cmd_list = []
            # The list of cells that we want to attack
            attack_list = []
            # The list of cells that we want to build/upgrade on
            build_list = []
            if not self.game.update_turn():
                break

            # Check if you exist in the game. If not, wait for the next round.
            # You may not appear immediately after you join. But you should be
            # in the game after one round.
            if self.game.me == None:
                continue

            me = self.game.me

            

            homeWeight = 0
            homeCoords = None
            for cell in game.me.cells.values():


                # The AI will consider all possible attacks and then rank them by their weight.
                
                for pos in cell.position.get_surrounding_cardinals():
                    # Get the MapCell object of that position
                    c = game.game_map[pos]

                    mult = 1.0
                    if c.owner != 0 and c.owner != game.uid:
                        # Here I try a cheese strat of attacking my own cells each by 1 energy each if they are adjacent to an opp cell.
                        # The goal of this cheese strat was to lock out AIs who only attacked with exactly the energy cost.
                        attack_list.append( (self.dfw, cell, 1))
                        # In addition, I would attack enemy cells with 1.7x the minimum energy to play for forcefields.
                        mult = 1.7
                    if c.owner != game.uid:
                        weight = self.atk_desire(cell)
                        weight *= 0.9
                        cost = c.attack_cost

                        # I would try to go for homes more, but in practice my AI didn't really destroy any homes.
                        if c.is_home and (cost < 2000 or cost/me.energy < 0.1):
                            weight *= 1.5
                            cost *= 1.2
                        cost *= mult
                        attack_list.append( (weight, c, int(cost)) )
                    
                    
                # The AI will consider all possible construction and then rank them by their weight.

                # This if block deals with upgrades.
                if cell.building.can_upgrade:
                    if cell.building.is_home:
                        homeCoords = cell

                    # Special way to deal with upgrading the home. The AI will want to upgrade home more when other buildings reach the tech level.
                    if cell.building.level == me.tech_level:
                        homeWeight += 1
                        

                    elif cell.building.level < me.tech_level:
                      
                        weight = 0
                      
                        if cell.building.name == 'energy_well':
                          
                            weight = self.g_weight() * cell.natural_energy
                        elif cell.building.name == 'gold_mine':
                            weight = self.e_weight() * cell.natural_gold
                          

                        # if cell.building.level == 2:
                        #     weight *= self.l3u
                            
                        weight *= self.upg

                        build_list.append((None, 1, weight, cell))        

                # This if block deals with building.
                if cell.owner == me.uid and cell.building.is_empty and me.gold >= BUILDING_COST[0]:

                    # Find the more preferable between gold mine and energy well
                    weights = self.build_weight(cell)
                    pref_building = BLD_ENERGY_WELL
                    pref_weight = weights[1]

                    # Sum the total weights of gold, energy, and fortress
                    tot = math.floor(weights[2] + weights[1] + weights[0])

                    # Defaults to fortress, since total weight is only negative with heavy enemy prescence.
                    if tot <= 0:
                        pref_building = BLD_FORTRESS
                        pref_weight = weights[2]
                    else:
                        #print(tot)

                        # Randomly generate a number. Building with higher weight = higher chance to be selected.
                        rand = random.randrange(tot)

                        if rand > weights[0] + weights[1]:
                            pref_building = BLD_FORTRESS
                            pref_weight = weights[2]
                        elif rand > weights[0]: 
                            pref_building = BLD_ENERGY_WELL
                            pref_weight = weights[1]
                        else:
                            pref_building = BLD_GOLD_MINE
                            pref_weight = weights[0]
                    

                    build_list.append((pref_building, 0, pref_weight, cell))

            
            build_list.append((None, 1, self.huw * homeWeight, homeCoords))     
                
            # The defensive cheese strat of attacking my own cells for 1 takes top priority.
            def sortAttacks(a):
                if a[2] == 1:
                    return 100000000
                return a[0]



            attack_list.sort(key=sortAttacks, reverse=True)

            # After sorting all the attacks by desirability weight, attempt to execute them all starting from most desirable to least desirable.
            for i in attack_list:
              
                c = i[1]
                temp_e = me.energy - i[2]
                if temp_e >= self.e_threshold0:
                  
                    cmd_list.append(game.attack(c.position, i[2]))
                    me.energy = temp_e
                    print("We are attacking ({}, {}) with {} energy".format(
                        pos.x, pos.y, i[2]))
                else:
                    break


            sortBuildOps = lambda buildOp: buildOp[2]

            build_list.sort(key = sortBuildOps, reverse=True)
            
            # After sorting all the attacks by desirability weight, attempt to execute them all starting from most desirable to least desirable.

            for i in build_list:
                #print(self.g_threshold())
                if me.gold < self.g_threshold() or me.energy < self.e_threshold():
                    break

                

                cell = i[3]
                if i[1]:
                    if cell == None:
                        continue
                    cmd_list.append(game.upgrade(cell.position))
                    temp_g = me.gold - i[3].building.upgrade_gold
                    temp_e = me.energy - i[3].building.upgrade_energy
                    if temp_g >= self.g_threshold():
                        me.gold = temp_g
                    else:
                        break
                    if temp_e >= self.e_threshold():
                        me.energy = temp_e
                    else:
                        break



                    print("We upgraded ({}, {}), with desirability weight of {}".format(
                        i[3].position.x, i[3].position.y, i[2]))
                else:
                    
                    temp_g = me.gold - 100
                    if temp_g >= self.g_threshold():
                        me.gold = temp_g
                    cmd_list.append(game.build(i[3].position, i[0]))
                    me.gold -= 100
                    print("We build {} on ({}, {}), with a desirability weight of {}".format(
                        i[0], cell.position.x, cell.position.y, i[2]))

            # Send the command list to the server
            result = game.send_cmd(cmd_list)
            

if __name__ == '__main__':
    # Create a Colorfight Instance. This will be the object that you interact
    # with.
    game = Colorfight()

    # ================== Find a random non-full rank room ==================
    #room_list = game.get_gameroom_list()
    #rank_room = [room for room in room_list if room["rank"] and room["player_number"] < room["max_player"]]
    #room = random.choice(rank_room)["name"]
    # ======================================================================
    room = LOBBY_NAME  # Delete this line if you have a room from above

    # ==========================  Play game once ===========================
    a = Agent()
    a.play_game(
        game
    )
    # ======================================================================

    # ========================= Run my bot forever =========================
    # while True:
    #    try:
    #        play_game(
    #            game     = game, \
    #            room     = room, \
    #            username = 'ExampleAI' + str(random.randint(1, 100)), \
    #            password = str(int(time.time()))
    #        )
    #    except Exception as e:
    #        print(e)
    #        time.sleep(2)
