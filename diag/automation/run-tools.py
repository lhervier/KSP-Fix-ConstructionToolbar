"""Plays the protocols of Construction Toolbar Fix: the tools of the EVA construction mode, the warp-to-morning
drawer of the time display, the construction mode with the next alarm showing, and the warp-to-morning button of
the tracking station.

It drives KSP through KSP-Util-MCPServer, a mod that answers HTTP requests on 127.0.0.1, and needs nothing but
Python 3: no AI, no package to install. Start KSP with KSP-Util-MCPServer installed, copy construction-toolbar.sfs
into a sandbox game, then run:

    python run-tools.py --folder <your sandbox game> --out out

construction-toolbar.sfs holds a small capsule on the launch pad at night, its engineer on EVA on its ladder, the
active vessel: only an engineer opens the construction mode. Each protocol loads it first, from the space centre:
the game is opened there first when KSP is at its main menu. The game remembers whether the next alarm shows above
the time display: each protocol hides it first.

The script plays the game as it stands: the mods installed, the size of the window and the interface scales are
set before KSP starts. It clicks with the server's mouse tools, mouse_move and mouse_click, which move the game's
pointer and press its buttons as a mouse does. It opens the construction mode as the construction button of the
toolbar does, and reads the tool in use, with the server's construction_tool, and warps time with set_warp, as the
. and , keys do. It finds what it clicks by moving the pointer over the screen first and reading which interface objects
lie under it, the topmost first and the ones beneath too, so the same script plays any window size and interface
scale:

- the Place, Move and Rotate tools: for each, the rectangle over which it lies under the pointer, whatever lies
  over it. The top of the Place tool is the middle of its row a quarter of the way down;
- the header of the first container of the construction mode's list of parts, the kerbal's inventory: the
  rectangle over which it lies under the pointer;
- the alarm clock button, left of the time display: the rectangle over which it is the topmost object;
- the date of the time display and the sunrise button of its drawer: measured while time warps at 5x, which holds
  the drawer open; time is then set back to normal and the drawer left to close. The date is then put back on
  the first row where it shows, the drawer closed;
- in the tracking station, its warp-to-morning button, always shown at the top: the rectangle over which it is the
  topmost object; the kerbal's row of the list, as the server's read_tracking_station gives it.

Between two steps, the pointer rests in the middle of the screen, and the game settles for two seconds: long
enough for the drawer to close.

The tools (--protocol tools), in construction mode: click the middle of the Move tool; rest the pointer on the
top of the Place tool, coming from the middle of the screen, then click there; let a warp end, and open the
construction mode again if it closed, as a time warp may do; click the middle of the Rotate tool, then the middle
of the Place tool.

The drawer (--protocol drawer), out of construction mode: rest the pointer below the time display, on the middle
of the sunrise button's rectangle, the drawer closed; rest it on the date, which opens the drawer; move it from the
date to the middle of the sunrise button in eight steps, as a hand does, and click; let the warp end.

The alarm (--protocol alarm), in construction mode: click the alarm clock button, which shows the next alarm and
slides the time display down; find the tools and the list again; click the middle of the Move tool, then the top
of the Place tool; rest the pointer on the middle of the first header of the list; click the alarm clock button
again, which hides the next alarm; click the middle of the Move tool, then the top of the Place tool.

The tracking station (--protocol station), entered from the flight as its scene: click the
warp-to-morning button, no vessel selected; click the kerbal's row, which selects it; click the button again; let
the warp end. When the capsule broke up as the save loaded, the station shows the kerbal's row lit with nothing
selected, and a click on it does nothing: the save is then loaded again, four times at most.

A screenshot is taken at the start and after every step, as a PNG the size of the window; while the pointer rests
on a point, the pointer is drawn on it where it was, screenshots leaving it out. With Pillow installed, each is
also cropped as the pages show it, 640 pixels wide, as a JPEG: the top left of the screen, the time display and
the tools. The script prints each point it clicks with the object under it, and writes them to runs.json, with
the game's time and warp rate after each step, and the selected tool after each click in construction mode, as
the server reads them.

At the end, the script checks what the fix promises and prints PASS or FAIL for each check, then exits with 0
when all pass, 1 otherwise. Without the mod, the checks marked (fix) fail: they are the bugs.

- tools: the middle of the Move tool selects it; the top of the Place tool then takes the click, selects the
  tool, and time does not warp (fix); the middle of the Rotate tool selects it; the middle of the Place tool
  then selects it (fix). A tool counts as selected by a click when another one was selected before it.
- drawer: the pointer below the time display, the drawer closed, does not bring the sunrise button under it
  (fix); from the date, the pointer reaches the sunrise button, the drawer open, and its click warps to the
  morning.
- alarm: the next alarm showing, the top of the Place tool takes the click and selects it, the Move tool clicked
  before it, and the first header of the list shows under the pointer (fix); the next alarm hidden
  again, the middle of the Move tool selects it, and the top of the Place tool then selects it (fix).
- station: the kerbal selected, the click on the warp-to-morning button warps to the morning.

KSP is left running at the end.
"""
import argparse
import json
import os
import sys
import time
import urllib.request

URL = None

# The interface objects the script looks for.
TOOLS = {"place": "ToolPlace", "move": "ToolMove", "rotate": "ToolRotate"}
DATE = "TextTime"
SUNRISE = "WarpToSunriseButton"
ALARM = "alarmButton"
# The tracking station's warp-to-morning button, always shown, and the vessel whose row is clicked: the kerbal on EVA,
# the active vessel (the capsule may not survive the load: it sometimes breaks up on the launch pad, with or without
# this mod).
STATION_SUNRISE = "WarpToMorning"
STATION_VESSEL = "Bill Kerman"
# The header of each container of the construction mode's list of parts, the kerbal's inventory first.
PART_HEADER = "Header Image"

# How long the drawer takes to slide, a click to take effect, in seconds.
SETTLE = 2.0

# The time warp that holds the drawer open while the script measures the sunrise button: 5x on rails.
HOLD_WARP = 1


def call(tool, **args):
    """Calls one tool of KSP-Util-MCPServer and returns its answer, decoded from JSON when it is JSON."""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args}}).encode()
    request = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=900) as response:
        result = json.loads(response.read())["result"]
    text = result["content"][0].get("text", "") if result["content"] else ""
    if result.get("isError"):
        raise RuntimeError(tool + ": " + text)
    try:
        return json.loads(text)
    except ValueError:
        return text


def log(*parts):
    print(time.strftime("%H:%M:%S"), *parts, flush=True)


class Screen:
    """The game's window: its size, where the pointer rests between steps, and what lies under a point."""

    def __init__(self):
        answer = self.move(0, 100)
        self.width, self.height = answer["window"]["width"], answer["window"]["height"]
        # Empty space in flight: the middle of the screen, below the kerbal.
        self.rest = (self.width // 2, round(self.height * 0.55))

    @staticmethod
    def move(x, y):
        # The game may miss a move now and then while it loads something: tried again.
        for attempt in range(5):
            try:
                return call("mouse_move", x=x, y=y)
            except RuntimeError as e:
                if attempt == 4:
                    raise
                log("mouse_move failed, trying again:", e)
                time.sleep(0.5)

    def under(self, x, y):
        """The interface objects under x, y, the topmost first, each with the object a click on it reaches."""
        return self.move(x, y)["ui"]

    def lies_under(self, x, y, name):
        """Whether the object named lies under x, y, on top or beneath something else."""
        return any(name in (item["name"], item.get("clickHandler")) for item in self.under(x, y))

    def topmost(self, x, y):
        """The interface object a click at x, y reaches, or the topmost one when none takes clicks there, or
        None."""
        objects = self.under(x, y)
        return (objects[0].get("clickHandler") or objects[0]["name"]) if objects else None

    def topmost_name(self, x, y):
        """The name of the topmost interface object under x, y, or None."""
        objects = self.under(x, y)
        return objects[0]["name"] if objects else None

    def park(self, seconds=SETTLE):
        """Rests the pointer on empty space, and lets the interface settle."""
        self.move(*self.rest)
        time.sleep(seconds)

    def run_along_row(self, y, test, x_from, x_to, step=1):
        """The first and last x of the first run of pixels of row y, between x_from and x_to, for which test
        holds at x, y, or None."""
        first = last = None
        for x in range(x_from, x_to, step):
            if test(x, y):
                if first is None:
                    first = x
                last = x
            elif first is not None:
                break
        return (first, last) if first is not None else None

    def extend(self, test, x, y, horizontal):
        """The first and last pixel of the run through x, y, along its row or down its column, for which test
        holds."""
        limit = self.width if horizontal else self.height
        start = x if horizontal else y
        at = (lambda v: test(v, y)) if horizontal else (lambda v: test(x, v))
        low = start
        while low - 1 >= 0 and at(low - 1):
            low -= 1
        high = start
        while high + 1 < limit and at(high + 1):
            high += 1
        return low, high

    def measure(self, point, test):
        """The rectangle around point over which test holds: along the row of that point, then down the column
        through the middle of that run, then along the middle row."""
        x, y = point
        row = self.extend(test, x, y, horizontal=True)
        x = (row[0] + row[1]) // 2
        column = self.extend(test, x, y, horizontal=False)
        y = (column[0] + column[1]) // 2
        row = self.extend(test, x, y, horizontal=True)
        return Rect(row[0], column[0], row[1], column[1])


class Rect:
    """A rectangle of the screen, in pixels from the top left corner of the window, edges included."""

    def __init__(self, left, top, right, bottom):
        self.left, self.top, self.right, self.bottom = left, top, right, bottom

    def middle(self):
        return (self.left + self.right) // 2, (self.top + self.bottom) // 2

    def top_quarter(self):
        """The middle of the row a quarter of the way down."""
        return (self.left + self.right) // 2, round(self.top + (self.bottom - self.top) * 0.25)

    def as_dict(self):
        return {"left": self.left, "top": self.top, "right": self.right, "bottom": self.bottom}


class Run:
    """One protocol played: its screenshots, the points it clicked and the game's time after each step."""

    def __init__(self, screen, out):
        self.screen = screen
        self.out = out
        self.steps = []
        self.found = {}
        self.construction = False
        self.checks = []

    def check(self, label, passed):
        """Records one check of what the fix promises."""
        self.checks.append({"check": label, "passed": bool(passed)})
        log("PASS" if passed else "FAIL", label)

    def shot(self, name, crop, pointer=None):
        """Takes a screenshot named after the step and crops it as the pages show it. With pointer, the pointer
        stays where it is and is drawn there; otherwise it rests first."""
        if pointer is None:
            self.screen.park()
        path = os.path.abspath(os.path.join(self.out, name + ".png"))
        call("screenshot", path=path, return_image=False)
        state = call("get_state")
        self.steps.append({"step": name, "screenshot": name + ".png", "scene": state["scene"], "ut": state["ut"],
                           "warpRate": state["warpRate"]})
        log(name, "ut %.0f, warp %s" % (state["ut"], state["warpRate"]))
        crop_image(path, os.path.join(self.out, "cropped", name + ".jpg"), crop, pointer)

    def click(self, x, y, what=""):
        """Clicks at x, y, and records the point, the object that takes the click there and, in construction
        mode, the tool selected after it. Returns that record."""
        # The pointer goes there first: what lies under it before the click, the click itself changing it.
        under = self.screen.topmost(x, y)
        before = call("get_state")["ut"]
        call("mouse_click", x=x, y=y)
        time.sleep(0.5)
        step = {"click": what, "x": x, "y": y, "under": under, "utBefore": before}
        if self.construction:
            step["tool"] = call("construction_tool")["tool"]
        self.steps.append(step)
        log("click at %d, %d (%s), over %s%s" % (x, y, what, under,
                                                 ", tool %s" % step["tool"] if "tool" in step else ""))
        return step

    def step(self, key, name):
        """The record of the step whose key (click, pointer, step) is name."""
        return next(s for s in self.steps if s.get(key) == name)

    def rest_on(self, name, point, crop, came_from=None, steps=1):
        """Moves the pointer onto point, from came_from in that many steps when given, lets it rest, records what
        lies under it, and takes a screenshot with the pointer drawn."""
        if came_from is not None:
            for i in range(1, steps + 1):
                self.screen.move(came_from[0] + (point[0] - came_from[0]) * i // steps,
                                 came_from[1] + (point[1] - came_from[1]) * i // steps)
        else:
            self.screen.move(*point)
        time.sleep(SETTLE)
        under = self.screen.topmost(*point)
        self.steps.append({"pointer": name, "x": point[0], "y": point[1], "under": under,
                           "topmost": self.screen.topmost_name(*point)})
        log("pointer at %d, %d (%s), over %s" % (point[0], point[1], name, under))
        self.shot(name, crop, pointer=point)

    def wait_warp_end(self):
        """Waits until time runs at its normal rate again, a warp to the morning lasting a few seconds."""
        for _ in range(120):
            if call("get_state")["warpRate"] == 1:
                break
            time.sleep(0.5)
        time.sleep(1)

    def find_tools(self):
        """Finds the Place, Move and Rotate tools of the construction mode. Fails when one is not found."""
        screen = self.screen
        place = TOOLS["place"]
        # Rows a few pixels apart, over the left half of the screen, down from below the time display, until one
        # crosses the Place tool.
        hit = None
        for y in range(round(screen.height / 24), screen.height // 3, 4):
            run = screen.run_along_row(y, lambda x, row: screen.lies_under(x, row, place), 0, screen.width // 2, 4)
            if run is not None:
                hit = (run[0] + run[1]) // 2, y
                break
        if hit is None:
            raise RuntimeError("the Place tool is not in the top third of the screen")
        self.found["place"] = screen.measure(hit, lambda x, y: screen.lies_under(x, y, place))
        # The Move and Rotate tools follow it on its right, on the same row.
        x, y = self.found["place"].right + 1, self.found["place"].middle()[1]
        for tool in ("move", "rotate"):
            name = TOOLS[tool]
            while x < screen.width and not screen.lies_under(x, y, name):
                x += 1
            if x >= screen.width:
                raise RuntimeError("no %s tool right of the Place tool" % tool)
            self.found[tool] = screen.measure((x, y), lambda px, py, n=name: screen.lies_under(px, py, n))
            x = self.found[tool].right + 1
        self.log_found()

    def find_drawer(self):
        """Finds the date of the time display, then the sunrise button of its drawer, held open by a time warp.
        Fails when one is not found."""
        screen = self.screen
        # The first row that crosses the date, the drawer closed. The pointer on the date opens the drawer, which
        # slides the date down: the date is measured once the drawer is held open, then put back on that row.
        top = None
        for y in range(2, round(screen.height / 12), 3):
            run = screen.run_along_row(y, lambda x, row: screen.topmost_name(x, row) == DATE, 0, screen.width // 2, 4)
            if run is not None:
                top = run[0], y
                break
        if top is None:
            raise RuntimeError("no date at the top of the screen")
        screen.park()
        # While time warps, the time display keeps its drawer open, whatever the pointer does.
        call("set_warp", rate_index=HOLD_WARP)
        try:
            time.sleep(SETTLE)
            hit = None
            for y in range(top[1], round(screen.height / 6)):
                if screen.topmost_name(top[0] + 2, y) == DATE:
                    hit = top[0] + 2, y
                    break
            if hit is None:
                raise RuntimeError("no date in the time display, the drawer open")
            date = screen.measure(hit, lambda x, y: screen.topmost_name(x, y) == DATE)
            self.found["date"] = Rect(date.left, top[1], date.right, top[1] + date.bottom - date.top)
            hit = None
            for y in range(date.bottom, round(screen.height / 6), 3):
                run = screen.run_along_row(y, lambda x, row: screen.topmost(x, row) == SUNRISE, 0, screen.width // 2, 4)
                if run is not None:
                    hit = (run[0] + run[1]) // 2, y
                    break
            if hit is None:
                raise RuntimeError("no sunrise button below the time display, the drawer open")
            self.found["sunrise"] = screen.measure(hit, lambda x, y: screen.topmost(x, y) == SUNRISE)
        finally:
            call("set_warp", rate_index=0)
        screen.park()
        self.log_found()

    def find_alarm(self):
        """Finds the alarm clock button, left of the time display. Fails when it is not found."""
        screen = self.screen
        for y in range(2, round(screen.height / 6), 3):
            run = screen.run_along_row(y, lambda x, row: screen.topmost(x, row) == ALARM, 0, screen.width // 4, 3)
            if run is not None:
                self.found["alarm"] = screen.measure(((run[0] + run[1]) // 2, y),
                                                     lambda x, row: screen.topmost(x, row) == ALARM)
                self.log_found()
                return
        raise RuntimeError("no alarm clock button at the top left of the screen")

    def find_part_header(self):
        """Finds the header of the first container of the construction mode's list of parts: the rectangle over
        which it lies under the pointer, down a column through the left of the list. Fails when it is not found."""
        screen = self.screen
        x = self.found["place"].left // 3
        for y in range(round(screen.height / 48), screen.height // 3, 2):
            if screen.lies_under(x, y, PART_HEADER):
                self.found["header"] = screen.measure((x, y), lambda px, py: screen.lies_under(px, py, PART_HEADER))
                self.log_found()
                return
        raise RuntimeError("no header of a container in the construction mode's list of parts")

    def log_found(self):
        self.steps.append({"found": {name: rect.as_dict() for name, rect in self.found.items()}})
        for name, rect in self.found.items():
            log("%s from %d, %d to %d, %d" % (name, rect.left, rect.top, rect.right, rect.bottom))

    def tools_crop(self):
        """The top left of the screen, down to a tool's height below the tools, right to a tool's width right of
        the Rotate tool: the time display and the three tools."""
        place, rotate = self.found["place"], self.found["rotate"]
        width, height = place.right - place.left, place.bottom - place.top
        return 0, 0, rotate.right + width, place.bottom + height

    def drawer_crop(self):
        """The top left of the screen, down to twice the sunrise button's height below it, right to three of its
        widths right of it: the time display and its drawer."""
        sunrise = self.found["sunrise"]
        width, height = sunrise.right - sunrise.left, sunrise.bottom - sunrise.top
        return 0, 0, sunrise.right + 3 * width, sunrise.bottom + 2 * height


def crop_image(source, target, box, pointer):
    """Crops a screenshot to box (left, top, right, bottom; None for the whole image), draws the pointer at
    pointer if given, and saves it 640 pixels wide as a JPEG. Does nothing without Pillow."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return
    image = Image.open(source).convert("RGB")
    if pointer is not None:
        # An arrow pointer, its tip on the point, the size of the system's at 100 %.
        x, y = pointer
        shape = [(0, 0), (0, 17), (4, 13), (7, 20), (10, 19), (7, 12), (12, 12)]
        ImageDraw.Draw(image).polygon([(x + dx, y + dy) for dx, dy in shape], fill=(255, 255, 255),
                                      outline=(0, 0, 0))
    if box is not None:
        image = image.crop(box)
    image = image.resize((640, round(image.height * 640 / image.width)), Image.LANCZOS)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    image.save(target, quality=88)


def start(options):
    """Loads the save into flight, from the space centre, and rests the pointer. Returns the game's window."""
    scene = call("get_state")["scene"]
    if scene == "MAINMENU":
        call("open_game", folder=options.folder)
    elif scene not in ("SPACECENTER", "FLIGHT"):
        call("go_to_scene", scene="SPACECENTER")
    # Right after the game opens, the server may not take the load yet: try again a few seconds later.
    for attempt in range(3):
        try:
            call("load_save", folder=options.folder, save=options.save)
            break
        except Exception as e:
            if attempt == 2:
                raise
            log("load_save failed, trying again:", e)
            time.sleep(5)
    screen = Screen()
    screen.park(3)
    # The game remembers whether the next alarm shows: each protocol starts with it hidden.
    if call("get_state")["nextAlarmShowing"]:
        run = Run(screen, None)
        run.find_alarm()
        call("mouse_click", x=run.found["alarm"].middle()[0], y=run.found["alarm"].middle()[1])
        screen.park()
    return screen


def open_construction_mode(screen):
    """Opens the EVA construction mode, as its button in the toolbar does."""
    call("construction_tool", panel="open")
    screen.park()


def construction_mode_open():
    """Whether the EVA construction mode is open."""
    return call("construction_tool")["panelOpen"]


# A warp to the morning moves the clock by hours; a step of the protocol, by seconds.
WARPED = 600


def selects(run, before, click, tool):
    """Whether the click selects the tool: the tool selected after it, and, when before names the click that
    precedes it, another tool selected after that one, so that the click is the one that changed it."""
    if before is not None and run.step("click", before)["tool"] == tool:
        return False
    return run.step("click", click)["tool"] == tool


def warped(run, click, shot):
    """Whether time warps at the screenshot after the click, or has jumped since the click."""
    after = run.step("step", shot)
    return after["warpRate"] > 1 or after["ut"] - run.step("click", click)["utBefore"] > WARPED


def tools(options, out):
    run = Run(start(options), out)
    open_construction_mode(run.screen)
    run.construction = True
    run.find_tools()
    run.screen.park()
    crop = run.tools_crop()
    place, move, rotate = run.found["place"], run.found["move"], run.found["rotate"]
    run.shot("0-construction-mode", crop)
    run.click(*move.middle(), what="middle of the Move tool")
    run.shot("1-click-move", crop)
    # From the middle of the screen, where the pointer rests, onto the top of the Place tool, as a hand does.
    run.rest_on("2-pointer-place-top", place.top_quarter(), crop, came_from=run.screen.rest, steps=8)
    top = run.click(*place.top_quarter(), what="top of the Place tool")
    run.shot("3-click-place-top", crop)
    run.wait_warp_end()
    # A time warp may close the construction mode: opened again, so that the rest of the protocol plays in it.
    still_open = construction_mode_open()
    run.steps.append({"constructionModeOpen": still_open})
    if not still_open:
        log("the construction mode closed: opened again")
        open_construction_mode(run.screen)
    run.click(*rotate.middle(), what="middle of the Rotate tool")
    run.shot("4-click-rotate", crop)
    run.click(*place.middle(), what="middle of the Place tool")
    run.shot("5-click-place-middle", crop)

    run.check("the click on the middle of the Move tool selects it",
              selects(run, None, "middle of the Move tool", "Move"))
    run.check("(fix) the top of the Place tool takes the click", top["under"] == TOOLS["place"])
    run.check("(fix) the click on the top of the Place tool selects it",
              selects(run, "middle of the Move tool", "top of the Place tool", "Place"))
    run.check("(fix) the click on the top of the Place tool does not warp time",
              not warped(run, "top of the Place tool", "3-click-place-top"))
    run.check("the click on the middle of the Rotate tool selects it",
              selects(run, "top of the Place tool", "middle of the Rotate tool", "Rotate"))
    run.check("(fix) the click on the middle of the Place tool selects it",
              selects(run, "middle of the Rotate tool", "middle of the Place tool", "Place"))
    return run


def drawer(options, out):
    run = Run(start(options), out)
    run.find_drawer()
    crop = run.drawer_crop()
    date, sunrise = run.found["date"], run.found["sunrise"]
    run.shot("0-flight", crop)
    # Below the time display, where the sunrise button shows once the drawer is open.
    run.rest_on("1-pointer-below-time", sunrise.middle(), crop)
    run.screen.park()
    run.rest_on("2-pointer-date", date.middle(), crop)
    run.rest_on("3-pointer-sunrise", sunrise.middle(), crop, came_from=date.middle(), steps=8)
    run.click(*sunrise.middle(), what="middle of the sunrise button")
    run.shot("4-click-sunrise", crop)
    run.wait_warp_end()
    run.shot("5-morning", None)

    run.check("(fix) the pointer below the time display does not bring the sunrise button under it",
              run.step("pointer", "1-pointer-below-time")["under"] != SUNRISE)
    run.check("from the date, the pointer reaches the sunrise button",
              run.step("pointer", "3-pointer-sunrise")["under"] == SUNRISE)
    run.check("the click on the sunrise button warps to the morning",
              warped(run, "middle of the sunrise button", "5-morning"))
    return run


def alarm(options, out):
    run = Run(start(options), out)
    open_construction_mode(run.screen)
    run.construction = True
    run.find_alarm()
    run.find_tools()
    run.find_part_header()
    run.screen.park()
    crop = run.tools_crop()
    run.shot("0-construction-mode", crop)
    run.click(*run.found["alarm"].middle(), what="alarm clock button")
    run.shot("1-click-alarm", crop)
    # The alarm clock button, the tools and the list where they are now, the next alarm showing: the button goes
    # down with the time display.
    run.find_alarm()
    run.find_tools()
    run.find_part_header()
    place, move, header = run.found["place"], run.found["move"], run.found["header"]
    run.click(*move.middle(), what="middle of the Move tool")
    run.shot("2-click-move", crop)
    top = run.click(*place.top_quarter(), what="top of the Place tool")
    run.shot("3-click-place-top", crop)
    run.wait_warp_end()
    run.rest_on("4-pointer-first-header", header.middle(), crop)
    run.click(*run.found["alarm"].middle(), what="alarm clock button, again")
    run.shot("5-click-alarm-again", crop)
    run.find_tools()
    run.click(*run.found["move"].middle(), what="middle of the Move tool, the alarm hidden again")
    run.click(*run.found["place"].top_quarter(), what="top of the Place tool, the alarm hidden again")
    run.shot("6-click-place-top-alarm-hidden", crop)

    run.check("(fix) the next alarm showing, the top of the Place tool takes the click", top["under"] == TOOLS["place"])
    run.check("(fix) the next alarm showing, the click on the top of the Place tool selects it",
              selects(run, "middle of the Move tool", "top of the Place tool", "Place"))
    run.check("(fix) the next alarm showing, the header of the first container of the list shows under the pointer",
              run.step("pointer", "4-pointer-first-header")["topmost"] == PART_HEADER)
    run.check("the next alarm hidden again, the click on the middle of the Move tool selects it",
              selects(run, None, "middle of the Move tool, the alarm hidden again", "Move"))
    run.check("(fix) the next alarm hidden again, the click on the top of the Place tool selects it",
              selects(run, "middle of the Move tool, the alarm hidden again",
                      "top of the Place tool, the alarm hidden again", "Place"))
    return run


def enter_station(options):
    """Loads the save, goes to the tracking station, and returns the window and the kerbal's row once a single
    click selects it. The capsule sometimes breaks up on the launch pad as the save loads, with or without this
    mod; the station then rebuilds its list and shows the top row, the kerbal's, lit with nothing selected, and a
    click on a lit row does nothing (a stock defect of the station's own). The save is then loaded again."""
    for attempt in range(4):
        screen = start(options)
        call("go_to_scene", scene="TRACKSTATION")
        screen.park()
        station_state = call("read_tracking_station")
        rows = [r for r in station_state["rows"] if r["vessel"] == STATION_VESSEL]
        if not rows:
            raise RuntimeError("no row of %s in the tracking station" % STATION_VESSEL)
        if not rows[0]["lit"] or station_state["selected"] == STATION_VESSEL:
            return screen, rows[0]
        log("the kerbal's row lit with nothing selected, the capsule lost: loading the save again")
    raise RuntimeError("the kerbal's row stayed lit with nothing selected")


def station(options, out):
    screen, row = enter_station(options)
    run = Run(screen, out)
    hit = None
    for y in range(2, round(screen.height / 12), 3):
        found = screen.run_along_row(y, lambda x, r: screen.topmost(x, r) == STATION_SUNRISE, 0, screen.width // 2, 3)
        if found is not None:
            hit = (found[0] + found[1]) // 2, y
            break
    if hit is None:
        raise RuntimeError("no warp-to-morning button at the top of the tracking station")
    run.found["sunrise"] = screen.measure(hit, lambda x, y: screen.topmost(x, y) == STATION_SUNRISE)
    run.log_found()
    screen.park()
    sunrise = run.found["sunrise"]
    # The top left of the screen: the time display, its button, and the first rows of the list.
    crop = 0, 0, sunrise.right + 6 * (sunrise.right - sunrise.left), row["top"] + 2 * row["height"]
    run.shot("0-station", crop)
    run.click(*sunrise.middle(), what="warp-to-morning button, no vessel selected")
    run.shot("1-click-sunrise-nothing-selected", crop)
    run.click(row["x"], row["y"], what="row of the kerbal")
    run.shot("2-kerbal-selected", crop)
    run.click(*sunrise.middle(), what="warp-to-morning button, the kerbal selected")
    run.shot("3-click-sunrise", crop)
    run.wait_warp_end()
    run.shot("4-morning", None)

    run.check("the kerbal selected, the click on the tracking station's warp-to-morning button warps to the morning",
              warped(run, "warp-to-morning button, the kerbal selected", "4-morning"))
    return run


PROTOCOLS = {"tools": tools, "drawer": drawer, "alarm": alarm, "station": station}


def main():
    global URL
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--folder", required=True, help="the sandbox game under saves/ the save was copied into")
    parser.add_argument("--save", default="construction-toolbar", help="the save, without .sfs")
    parser.add_argument("--protocol", choices=list(PROTOCOLS) + ["all"], default="all")
    parser.add_argument("--out", required=True, help="the folder for runs.json and the screenshots")
    parser.add_argument("--port", type=int, default=8770, help="the port of KSP-Util-MCPServer")
    options = parser.parse_args()
    URL = "http://127.0.0.1:%d/mcp/" % options.port

    names = list(PROTOCOLS) if options.protocol == "all" else [options.protocol]
    runs = {}
    for name in names:
        out = os.path.join(options.out, name)
        os.makedirs(out, exist_ok=True)
        log("protocol", name)
        run = PROTOCOLS[name](options, out)
        runs[name] = {"steps": run.steps, "checks": run.checks}
    with open(os.path.join(options.out, "runs.json"), "w", newline="\n") as f:
        json.dump(runs, f, indent=1)

    failed = [(name, c["check"]) for name, run in runs.items() for c in run["checks"] if not c["passed"]]
    total = sum(len(run["checks"]) for run in runs.values())
    print()
    for name, run in runs.items():
        for c in run["checks"]:
            print("%-4s %-7s %s" % ("PASS" if c["passed"] else "FAIL", name, c["check"]))
    print("%d of %d checks passed" % (total - len(failed), total))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
