import sys
import os
import time
from uuid import uuid4
from flask import Flask, Response, render_template, stream_with_context
from core.simulation import setup_game
from game.game_loop import run_game_round, finalize_log

app = Flask(__name__)

class RealTimeStream:
    def __init__(self):
        self.buffer = []

    def write(self, text):
        lines = text.splitlines()
        self.buffer.extend(lines)

    def flush(stream):
        for line in stream.get():
            if line.strip():
                yield f"data: {line.strip()}\n\n"

    def get(self):
        output = self.buffer[:]
        self.buffer.clear()
        return output

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run")
def run():
    @stream_with_context
    def generate():
        stream = RealTimeStream()
        original_stdout = sys.stdout
        sys.stdout = stream

        game_id = str(uuid4())
        agents, agents_state, state = setup_game(game_id)

        try:
            for round_num in range(1, 6):
                print(f"--- Round {round_num} ---")
                yield from flush(stream)

                run_game_round(game_id, round_num, state, agents, agents_state)
                yield from flush(stream)

                time.sleep(0.25)

            finalize_log()
            print(f"✔ Simulation complete for game_id: {game_id}")
            yield from flush(stream)

        finally:
            sys.stdout = original_stdout

        yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')

def flush(stream):
    for line in stream.get():
        if line.strip():
            yield f"data: {line.strip()}\n\n"

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
