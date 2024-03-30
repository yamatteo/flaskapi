from pyscript import document, fetch, when, display, window
import js
from engine import Game, Rufus
from attr import asdict
from pyodide.ffi import create_proxy, to_js
import json


active_game = None

# from jinja2 import Environment, BaseLoader, TemplateNotFound

# class URLLoader(BaseLoader):
#     async def get_source(self, environment, template):
#         url = f"/templates/{template}"
#         response = await fetch(url)
#         if not response.ok:
#             raise TemplateNotFound(template)
#         source = await response.text()
#         return source, None, lambda: True


# env = Environment()


# async def trigger(event):
#     print("Click", event)
#     print(window.trigger_url)
#     response = await fetch(window.trigger_url, method="POST").text()
#     print(response)

# @when("pusherupdate", "#pyscript_output")
# def test_run_from_js(event):
#     print("RUN", event.detail.to_py())

@when("game_update", "#pyscript_output")
async def game_update(event=None):
    global active_game
    response = await fetch(window.game_data_url, method="GET").json()
    active_game = Game.loads(response['active_game'])
    window.active_game = active_game
    # window.active_game = js.JSON.parse(game_data)

    if (window.automate and active_game.expected.name == window.user.pseudo):
        action = Rufus(window.user.pseudo).decide(active_game)
        print("we want to sent:", str(asdict(action)))
        js.postJSON(window.post_action_url, json.dumps(asdict(action)))

    # template_string = await fetch("/templates/active_game_subpart.html")
    # html = env.get_template_("active_game_subpart.html").render_async(
    #         user=window.user,
    #         active_game = active_game,
    #     )
    # print(html)
    output_div = document.querySelector("#pyscript_output")
    output_div.innerHTML = response['active_game_content']
    new_scripts = output_div.getElementsByTagName('script')
    for element in new_scripts:
        js.eval(element.innerHTML)

# await game_update()