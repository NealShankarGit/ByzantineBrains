import sys
import os
import time
from uuid import uuid4
from flask import Flask, Response, render_template, stream_with_context, jsonify
from core.simulation import setup_game, get_current_state
from game.game_loop import run_game_round, finalize_log, generate_map_html, generate_agent_status_html

app = Flask(__name__)
active_game_id = None

class RealTimeStream:
    def __init__(self):
        self.buffer = []

    def write(self, text):
        lines = text.splitlines()
        self.buffer.extend(lines)

    def flush(self):
        for line in self.get():
            if line.strip():
                yield f"data: {line.strip()}\n\n"

    def get(self):
        output = self.buffer[:]
        self.buffer.clear()
        return output

@app.route("/")
def index():
    initial_map = generate_map_html()
    return render_template("index.html", map_html=initial_map)

@app.route("/run")
def run():
    @stream_with_context
    def generate():
        global active_game_id
        stream = RealTimeStream()
        original_stdout = sys.stdout
        sys.stdout = stream

        game_id = str(uuid4())
        active_game_id = game_id
        agents, agents_state, state = setup_game(game_id)

        try:
            for round_num in range(1, 6):
                print(f"--- Round {round_num} ---")
                yield from stream.flush()

                yield from run_game_round(game_id, round_num, state, agents, agents_state, stream)

                time.sleep(0.25)

            finalize_log()
            print(f"✔ Simulation complete for game_id: {game_id}")
            yield from stream.flush()

        finally:
            sys.stdout = original_stdout

        yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route("/map")
def map_endpoint():
    agents, state = get_current_state()
    return jsonify(
        map_html=generate_map_html(state, agents),
        agent_status=generate_agent_status_html(state, agents)
    )

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
