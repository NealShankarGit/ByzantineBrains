import sys
import os
import time
import io
import contextlib
from flask import Flask, Response, stream_with_context

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.simulation import setup_game, finalize_log
from game.game_loop import run_game_round

app = Flask(__name__)


@app.route("/")
def home():
    @stream_with_context
    def generate():
        yield "<html><body style='background:#000;color:#0f0;font-family:monospace;'>"

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            agents, agents_state, state = setup_game()
            NUM_ROUNDS = 5

            for round_num in range(1, NUM_ROUNDS + 1):
                print(f"\n--- Round {round_num} ---")
                run_game_round(round_num - 1, state, agents, agents_state)
                time.sleep(0.1)
                yield from flush_buffer(buffer)

            finalize_log()
            print("Simulation complete.")
            yield from flush_buffer(buffer)

        yield "</body></html>"

    return Response(generate(), mimetype='text/html')


def flush_buffer(buffer):
    buffer.seek(0)
    lines = buffer.read().splitlines()
    buffer.truncate(0)
    buffer.seek(0)
    for line in lines:
        if line.strip():
            yield f"{line}<br/>\n"


if __name__ == "__main__":
    app.run(debug=True)
