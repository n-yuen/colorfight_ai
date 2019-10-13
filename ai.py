from colorfight import Colorfight, Position
import time
import math
import random
from colorfight.constants import BLD_GOLD_MINE, BLD_ENERGY_WELL, BLD_FORTRESS, BUILDING_COST

LOBBY_NAME = 'official_final'
USERNAME = 'xD'

class Agent:
    def __init__(self):
        self.bdw = 1.35
        self.upg = 100.0
        self.dfw = 100
        self.l3u = 0.8
        self.cdw = -1.0
        self.bcdw = -50
        self.cgw = 1.0
        self.dpw = 500.0
        self.oew = 1.0
        self.ogw = 1.0
        self.huw = 120.0
        self.twb = -4.0
        self.twa = -140.0
        self.str = 500.0
        self.shu = 0.7
        self.e_threshold0 = 0

    def e_weight(self):
        if game.turn > 300:
            return 400 - game.turn/2
        return 450 - game.turn

    def g_weight(self):
        if game.turn < 100:
            return 170 + game.turn
        elif game.turn < 200:
            return 130 + game.turn * 2.4
        else:
            return game.turn*3.4

    def g_threshold(self):
        if game.turn < 320:
            return 0
        return (game.turn - 320) * 3700

    def e_threshold(self):
        return 0

    def tax_value(self, cell):
        me = self.game.me
        return me.tax_amount/(me.gold+me.energy)

    def cell_danger(self, cell):
        cell_danger = 0
        for dx in range(-5, 5):
            for dy in range(-5, 5):
                if (abs(dx) + abs(dy) != 0) and cell.position.x + dx > 0 and cell.position.y + dy > 0 \
                    and cell.position.x + dx < self.game.width and cell.position.y + dy < self.game.width:
                    owner = self.game.game_map[cell.position + Position(dx, dy)].owner
                    if owner != self.game.me.uid and owner != 0:
                        cell_danger += 1.0 / (abs(dx) + abs(dy))

      
        return cell_danger

    def home_dist(self, cell):
        return 0
        #for h in self.game.home



    def cell_gain(self, cell):
        return max(cell.gold * self.g_weight(), cell.energy * self.e_weight())

    def delta_perim(self, cell):
        rtn = 0
        for pos in cell.position.get_surrounding_cardinals():
            c = self.game.game_map[pos]
            if c.owner == game.uid:
                rtn += 1

        return rtn

    def opp_value(self, cell):
        if cell.owner != game.uid:
            if cell.building == BLD_GOLD_MINE:
                return self.ogw * cell.building.level
            if cell.building == BLD_ENERGY_WELL:
                return self.oew * cell.building.level

        return 0

    # def build_weight(self, cell):
    #     return (cell.gold * self.g_weight(), cell.energy * self.e_weight())

    def build_weight(self, cell):
      flatX = self.bcdw * self.cell_danger(cell) + self.twb * self.tax_value(cell)

      str_weight = self.cell_danger(cell) * self.str

      return (self.bdw* (cell.gold * self.g_weight() + flatX), self.bdw* (cell.energy * self.e_weight() + flatX), self.bdw* str_weight)

    def upg_desire(self,cell):
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
            build_list = []
            # update_turn() is required to get the latest information from the
            # server. This will halt the program until it receives the updated
            # information.
            # After update_turn(), game object will be updated.
            # update_turn() returns a Boolean value indicating if it's still
            # the same game. If it's not, break out
            if not self.game.update_turn():
                break

            # Check if you exist in the game. If not, wait for the next round.
            # You may not appear immediately after you join. But you should be
            # in the game after one round.
            if self.game.me == None:
                continue

            me = self.game.me

            

            # game.me.cells is a dict, where the keys are Position and the values
            # are MapCell. Get all my cells.

            homeWeight = 0
            homeCoords = None
            for cell in game.me.cells.values():
                # Check the surrounding position
                
                for pos in cell.position.get_surrounding_cardinals():
                    # Get the MapCell object of that position
                    c = game.game_map[pos]
                    # Attack if the cost is less than what I have, and the owner
                    # is not mine, and I have not attacked it in this round already
                    # We also try to keep our cell number under 100 to avoid tax
                    mult = 1.0
                    if c.owner != 0 and c.owner != game.uid:
                        attack_list.append( (self.dfw, cell, 1))
                        mult = 1.7
                    if c.owner != game.uid:
                        weight = self.atk_desire(cell)
                        weight *= 0.9
                        cost = c.attack_cost
                        if c.is_home and (cost < 2000 or cost/me.energy < 0.1):
                            weight *= 1.5
                            cost *= 1.2
                        cost *= mult
                        #print("here", (weight, c, cost))
                        attack_list.append( (weight, c, int(cost)) )
                    
                    
                # If we can upgrade the building, upgrade it.
                # Notice can_update only checks for upper bound. You need to check
                # tech_level by yourself.

                if cell.building.can_upgrade:
                    if cell.building.is_home:
                        homeCoords = cell

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

                if cell.owner == me.uid and cell.building.is_empty and me.gold >= BUILDING_COST[0]:

                    # Find the more preferable between gold mine and energy well
                    weights = self.build_weight(cell)
                    pref_building = BLD_ENERGY_WELL
                    pref_weight = weights[1]

                    tot = math.floor(weights[2] + weights[1] + weights[0])

                    if tot <= 0:
                        pref_building = BLD_FORTRESS
                        pref_weight = weights[2]
                    else:
                        #print(tot)
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
                
            def sortAttacks(a):
                if a[2] == 1:
                    return 100000000
                return a[0]

            attack_list.sort(key=sortAttacks, reverse=True)


            
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
