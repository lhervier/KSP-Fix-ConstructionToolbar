# Checking the tracking station

Part of [Construction Toolbar Fix](../README.md). The tracking station shows the time too, with a
warp-to-morning button. In flight, that button sits in a drawer that slides out of the time display when the
pointer is over it, the drawer this mod changes; in the tracking station, it is always shown, right of the time
warp buttons, and has no drawer. Does it still warp to the morning? Played without this mod, then with it.

## The install

The same as for [the construction tools](checking-tools.md#the-install).

## The protocol

The save is [construction-toolbar.sfs](../diag/construction-toolbar.sfs), loaded into flight as for the other
protocols, then the tracking station entered from the flight.

1. Look at the warp-to-morning button, the sun at the top of the screen, nothing selected.
2. Click it.
3. Click the kerbal's row, *Bill Kerman*, in the list of tracked objects.
4. Click the warp-to-morning button again.
5. Let the warp end.

**Played by a script.** [run-tools.py](../diag/automation/run-tools.py) plays it with `--protocol station`, and
checks that the click on the button, the kerbal selected, warps to the morning. The capsule sometimes breaks up
on the launch pad as the save loads, with or without this mod; the station then shows the kerbal's row lit
though nothing is selected, and a click on it does nothing, a defect of the station of its own: the script then
loads the save again. The images below are the top left of the screen, zoomed to 640 pixels wide; the last one
is the whole screen.

## The results

Read off the screenshots below:

| Step | Stock | This mod |
|---|---|---|
| 1. Station open, nothing selected | the sun button grey | the sun button grey |
| 2. Click on the sun button | nothing happens | nothing happens |
| 3. Click on the kerbal's row | Bill selected, the sun button lit | Bill selected, the sun button lit |
| 4. Click on the sun button | time warping, six arrows lit | time warping, six arrows lit |
| 5. Warp over | *Warp ended* on screen | *Warp ended* on screen |

The same on stock and with this mod: the button greyed until a vessel is selected, then the warp to the morning.
In the log, at `Debug`, the mod writes no line in the tracking station: it finds no drawer there.

## On stock

<p class="thumbs"><a href="../imgs/checking-station/stock/0-station.jpg"><img src="../imgs/checking-station/stock/0-station.jpg" width="96"></a> <a href="../imgs/checking-station/stock/1-click-sunrise-nothing-selected.jpg"><img src="../imgs/checking-station/stock/1-click-sunrise-nothing-selected.jpg" width="96"></a> <a href="../imgs/checking-station/stock/2-kerbal-selected.jpg"><img src="../imgs/checking-station/stock/2-kerbal-selected.jpg" width="96"></a> <a href="../imgs/checking-station/stock/3-click-sunrise.jpg"><img src="../imgs/checking-station/stock/3-click-sunrise.jpg" width="96"></a> <a href="../imgs/checking-station/stock/4-morning.jpg"><img src="../imgs/checking-station/stock/4-morning.jpg" width="96"></a></p>

<details>
<summary>The five screenshots, on stock</summary>

The tracking station, nothing selected:

![The tracking station, nothing selected, on stock](../imgs/checking-station/stock/0-station.jpg)

After the click on the warp-to-morning button:

![After the click on the warp-to-morning button, on stock](../imgs/checking-station/stock/1-click-sunrise-nothing-selected.jpg)

After the click on the kerbal's row:

![After the click on the kerbal's row, on stock](../imgs/checking-station/stock/2-kerbal-selected.jpg)

After the click on the warp-to-morning button:

![After the click on the warp-to-morning button, on stock](../imgs/checking-station/stock/3-click-sunrise.jpg)

Once the warp is over, the whole screen:

![Once the warp is over, the whole screen, on stock](../imgs/checking-station/stock/4-morning.jpg)

</details>

## With this mod

<p class="thumbs"><a href="../imgs/checking-station/fix/0-station.jpg"><img src="../imgs/checking-station/fix/0-station.jpg" width="96"></a> <a href="../imgs/checking-station/fix/1-click-sunrise-nothing-selected.jpg"><img src="../imgs/checking-station/fix/1-click-sunrise-nothing-selected.jpg" width="96"></a> <a href="../imgs/checking-station/fix/2-kerbal-selected.jpg"><img src="../imgs/checking-station/fix/2-kerbal-selected.jpg" width="96"></a> <a href="../imgs/checking-station/fix/3-click-sunrise.jpg"><img src="../imgs/checking-station/fix/3-click-sunrise.jpg" width="96"></a> <a href="../imgs/checking-station/fix/4-morning.jpg"><img src="../imgs/checking-station/fix/4-morning.jpg" width="96"></a></p>

<details>
<summary>The five screenshots, with this mod</summary>

The tracking station, nothing selected:

![The tracking station, nothing selected, with this mod](../imgs/checking-station/fix/0-station.jpg)

After the click on the warp-to-morning button:

![After the click on the warp-to-morning button, with this mod](../imgs/checking-station/fix/1-click-sunrise-nothing-selected.jpg)

After the click on the kerbal's row:

![After the click on the kerbal's row, with this mod](../imgs/checking-station/fix/2-kerbal-selected.jpg)

After the click on the warp-to-morning button:

![After the click on the warp-to-morning button, with this mod](../imgs/checking-station/fix/3-click-sunrise.jpg)

Once the warp is over, the whole screen:

![Once the warp is over, the whole screen, with this mod](../imgs/checking-station/fix/4-morning.jpg)

</details>
