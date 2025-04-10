import random
import config
from agents.agent_setup import create_agents
import json
from datetime import datetime
import os
import platform
from data.database import (
    log_game_event, log_reflection, log_trust_change, log_vote,
    log_consensus, log_round_metadata
)

def clear_terminal():
    os.system("cls" if platform.system() == "Windows" else "clear")

rooms = {
    "Cafeteria": ["Weapons", "Navigation", "Storage", "Admin", "MedBay", "Upper Engine"],
    "Weapons": ["Cafeteria", "O2"],
    "Navigation": ["O2", "Shields"],
    "O2": ["Weapons", "Navigation", "Cafeteria"],
    "Shields": ["Navigation", "Communications", "Storage"],
    "Communications": ["Shields"],
    "Admin": ["Cafeteria", "Storage"],
    "Storage": ["Admin", "Shields", "Electrical", "Lower Engine", "Cafeteria"],
    "Electrical": ["Storage", "Lower Engine"],
    "Lower Engine": ["Storage", "Electrical", "Security", "Reactor"],
    "Security": ["Lower Engine", "Upper Engine", "Reactor"],
    "Reactor": ["Security", "Upper Engine", "Lower Engine"],
    "Upper Engine": ["Reactor", "Security", "MedBay", "Cafeteria"],
    "MedBay": ["Upper Engine", "Cafeteria"]
}

log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_path = os.path.join(log_dir, f"simulation_log_{timestamp}.json")
log_data = {
    "start_time": timestamp,
    "events": []
}

def show_ship_map(state, agents):
    clear_terminal()
    mapping = {room: [] for room in rooms}
    bodies = {room: [] for room in rooms}
    for agent, info in state.items():
        if not info.get("killed", False):
            agent_obj = next((a for a in agents if a.name == agent), None)
            mapping[info["room"]].append(f"{agent_obj.color}{agent}" if agent_obj else agent)
        elif info.get("room_body"):
            agent_obj = next((a for a in agents if a.name == agent), None)
            color = agent_obj.color if agent_obj else ""
            bodies[info["room_body"]].append(f"💀{color}{agent}")

    def fmt(room):
        entries = mapping.get(room, []) + bodies.get(room, [])
        return f"[{room}]" if not entries else f"[{room}: {' '.join(entries)}]"

    print("\n--- Ship Map ---\n")
    print(f"{fmt('Upper Engine')}               {fmt('Cafeteria')}              {fmt('Weapons')}")
    print("")
    print(f"{fmt('Reactor')}        {fmt('Security')}       {fmt('MedBay')}        {fmt('O2')}      {fmt('Navigation')}")
    print("")
    print(f"{fmt('Lower Engine')}   {fmt('Electrical')}     {fmt('Storage')}       {fmt('Admin')}   {fmt('Shields')}")
    print("")
    print(f"{' ' * 55}{fmt('Communications')}")

    print("\nPlayer Locations:")
    for room, occupants in mapping.items():
        if occupants:
            print(f"{room}: {' '.join(occupants)}")

def movement_phase(state, agents, agents_state):
    for agent in agents:
        if state[agent.name]["killed"]:
            continue
        current = state[agent.name]["room"]
        adj = rooms[current]
        dest = agent.choose_room(current, adj, state)

        if dest.startswith("Kill "):
            target_name = dest.split(" ")[1]
            if target_name in state and state[target_name]["room"] == current and not state[target_name]["killed"]:
                state[target_name]["killed"] = True
                state[target_name]["room_body"] = current
                print(f"{agent.name} killed {target_name} in {current}")
            move_dest = agent.choose_room(current, rooms[current], state)
            if move_dest in rooms[current]:
                state[agent.name]["room"] = move_dest
                print(f"{agent.name} moved from {current} to {move_dest}")
            else:
                print(f"{agent.name} stayed in {current}")
        else:
            state[agent.name]["room"] = dest
            if dest == current:
                print(f"{agent.name} stayed in {current}")
            else:
                print(f"{agent.name} moved from {current} to {dest}")

        seen = [a for a in state if state[a]["room"] == dest and a != agent.name and not state[a]["killed"]]
        room = state[agent.name]["room"]
        seen_bodies = [a for a in state if state[a].get("killed") and state[a].get("room_body") == room]
        state[agent.name]["perception"].append({
            "room": room,
            "agents_seen": seen,
            "bodies_seen": seen_bodies
        })

        if seen_bodies and not state[agent.name]["killed"]:
            if agent.__class__.__name__ == "HonestAgent":
                agent_msg = f"I just found the body of {seen_bodies[0]} in {room}! Reporting it now!"
                print(f"{agent.name} reports: {agent_msg}")
                agents_state[agent.name]["messages"].append(agent_msg)

        if agent.__class__.__name__ == "HonestAgent":
            if not state[agent.name]["task_done"]:
                if state[agent.name]["room"] == state[agent.name]["task_room"]:
                    if state[agent.name]["doing_task"]:
                        state[agent.name]["task_done"] = True
                        print(f"{agent.name} completed their task in {state[agent.name]['room']}.")
                    else:
                        state[agent.name]["doing_task"] = True
                        print(f"{agent.name} started task in {state[agent.name]['room']}.")
                else:
                    state[agent.name]["doing_task"] = False

import sys

def run_game_round(game_id, step, state, agents, agents_state):
    movement_phase(state, agents, agents_state)
    show_ship_map(state, agents)
    sys.stdout.flush()

    alive = sum(1 for a in state.values() if not a["killed"])
    dead = sum(1 for a in state.values() if a["killed"])
    log_round_metadata(game_id, step, alive, dead)

    messages = {}

    any_body_seen = any(
        agent_state["perception"]
        and len(agent_state["perception"][-1].get("bodies_seen", [])) > 0
        for agent_state in state.values()
        if not agent_state["killed"]
    )

    if any_body_seen:
        print(f"\n--- DISCUSSION (Round {step}) ---")
        sys.stdout.flush()
        messages = {}
        for agent in agents:
            if state[agent.name]["killed"]:
                continue
            history = state[agent.name].get("perception", [])
            message = agent.simulate_message(history)
            sys.stdout.flush()
            if message:
                messages[agent.name] = message
                log_reflection(game_id, step, agent.name, message)

        for agent in agents:
            if state[agent.name]["killed"]:
                continue
            response = agent.respond_to_message(messages, state[agent.name].get("perception", []))
            sys.stdout.flush()
            if response:
                log_reflection(game_id, step, agent.name, response)

        print(f"\n--- VOTING (Round {step}) ---")
        sys.stdout.flush()
        votes = {}
        for agent in agents:
            if state[agent.name]["killed"]:
                continue
            voter, target = agent.vote_for_ejection()
            votes[voter] = target
            log_vote(game_id, step, voter, target)
            print(f"{voter} voted to eject {target}")
            sys.stdout.flush()

        vote_counts = {}
        for target in votes.values():
            vote_counts[target] = vote_counts.get(target, 0) + 1

        ejected = max(vote_counts, key=vote_counts.get)
        agreement_level = vote_counts[ejected] / len(votes)

        if ejected in agents_state:
            correct = (not state[ejected]["killed"] and agents_state[ejected]["role"] == "byzantine")
            print(f"\nEjected: {ejected}")
            print(f"Vote {'correct' if correct else 'incorrect'} — Role was: {agents_state[ejected]['role']}")
            print(f"Consensus Agreement Level: {agreement_level:.2f}")
            sys.stdout.flush()
            state[ejected]["killed"] = True
        else:
            correct = False
            print(f"\nNo one was ejected.")
            print(f"Consensus Agreement Level: {agreement_level:.2f}")
            sys.stdout.flush()

        log_consensus(game_id, step, f"Eject {ejected}", agreement_level)

        for agent in agents:
            if agent.name in votes:
                voted_correctly = (votes[agent.name] == ejected and correct)
                agent.update_trust(ejected, voted_correctly)
                delta = 20 if voted_correctly else -20
                log_trust_change(game_id, step, agent.name, ejected, delta)

        for agent in agents:
            if state[agent.name]["killed"]:
                continue
            log_game_event(game_id, step, agent.name, state[agent.name]["room"],
                           state[agent.name]["killed"], True, votes[agent.name],
                           ejected, votes[agent.name] == ejected, 0, True, agreement_level)

def finalize_log():
    with open(log_file_path, "w") as f:
        json.dump(log_data, f, indent=2)
    print(f"Simulation results saved to {log_file_path}")
