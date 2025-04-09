import sys
import os
import time
from flask import Flask, Response, render_template_string, stream_with_context
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
                clean = line.replace('\r', '').replace('\n', '')
                yield f"data: {clean}\n\n"

    def get(self):
        output = self.buffer[:]
        self.buffer.clear()
        return output

@app.route("/")
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ByzantineBrains</title>
        <style>
            body { background: #000; color: #0f0; font-family: monospace; padding: 2em; }
            button { font-size: 1.1em; padding: 0.5em 1em; margin-bottom: 1em; }
            #output { border: 1px solid #0f0; padding: 1em; max-height: 80vh; overflow-y: auto; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>ByzantineBrains Simulation</h1>
        <button onclick="start()">▶ Run Simulation</button>
        <div id="output"></div>
        <script>
            function start() {
                const out = document.getElementById("output");
                out.innerHTML = "";
                const source = new EventSource("/run");
                source.onmessage = function(event) {
                    out.innerHTML += event.data + "\\n";
                    out.scrollTop = out.scrollHeight;
                };
                source.onerror = function() {
                    source.close();
                };
            }
        </script>
    </body>
    </html>
    """)

@app.route("/run")
def run():
    @stream_with_context
    def generate():
        stream = RealTimeStream()
        original_stdout = sys.stdout
        sys.stdout = stream

        agents, agents_state, state = setup_game()

        try:
            for round_num in range(1, 6):
                print(f"--- Round {round_num} ---")
                yield from flush(stream)

                run_game_round(round_num - 1, state, agents, agents_state)
                yield from flush(stream)

                time.sleep(0.25)

            finalize_log()
            print("✔ Simulation complete.")
            yield from flush(stream)

        finally:
            sys.stdout = original_stdout

        yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')

def flush(stream):
    for line in stream.get():
        if line.strip():
            clean = line.replace('\r', '').replace('\n', '')
            yield f"data: {clean}\n\n"

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
