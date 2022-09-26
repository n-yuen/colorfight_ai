# Introduction

This is my AI that won ACM [AI]nvasion's second prize and the Green Hills Software Prize. I competed by myself under 'Team xD'. The code here is untouched from the day of the competition; as a result, there are many possible areas of improvement if I wanted to improve the AI further.

My algorithm tries to grab energy early in the game. When another player's territory is nearby, it tends to build fortresses. Later in the game, it will prefer building gold mines over energy, and after a certain number of turns it sets aside a specified amount of money to stockpile to try to win the game.

My AI determines the best use of energy and the best use of gold by assigning each actionn a unique weight based on how desirable the action is deemed to be. Desirability is a function of several variables.

For desirability of a tile to be attacked, the algorithm takes into account the following:

* Energy and Gold on the tile (more resources = more desirable)
* How contiguous friendly territory will be after the action (more contiguous = more desirable)
* How dangerous the tile is, i.e. how many enemy tiles are nearby (more danger = less desirable)
* The current tax amount (more tax = less desirable)
* Opponent's value of the cell - the algorithm will find it more desirable to take opponent's high level energy and gold buildings.

One factor that I should have taken into account, but did not, is the cost of attacking the tile.

For desirability of a tile to be developed (build/upgrade), the algorithm takes into account the following:

* Energy and Gold on the tile (more resources = more desirable)
* How contiguous friendly territory will be after the action (more contiguous = more desirable)
* How dangerous the tile is, i.e. how many enemy tiles are nearby. More danger means the algorithm will tend to build fortresses, whereas less danger means that the cell will tend to build resource gathering buildings.
* The current tax amount (more tax = less desirable)

My AI also has a special algorithm to determine when to upgrade the Home, based on how many 'max level' buildings are owned. One particular strength of my algorithm is that it tends to perform very well in the mid-game, because it upgrades the home early and upgrades other buildings very soon afterward. This allows it to outscale many other AIs despite less total 'owned territory' because the tiles that are owned produce much more, and tax is overall lower. Therefore, its economy remains strong throughout the mid- and late-game, allowing the AI to take back territory that it was not able to gain in the early-game.

My AI did not have an algorithm for building a new home, but its generally strong defensive capabilities meant that my home was never destroyed, so I was never punished for this.

Overall, I think that my AI is quite strong, but was crippled early-game because I did not take into account the cost of attacking tiles.

# Requirements

You need >= python3.6 to run this script. The websocket part uses async/await
syntax.

You need ```websockets```. You can do ```pip3 install -r requirements.txt``` to
install all the python package requirements.

# Run the bot

```python3 example_ai.py```
