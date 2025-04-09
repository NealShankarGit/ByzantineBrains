import csv
import os
from datetime import datetime

db_dir = os.path.join(os.path.dirname(__file__), "database")
os.makedirs(db_dir, exist_ok=True)

def write_csv(filename, headers, row):
    path = os.path.join(db_dir, filename)
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not exists:
            writer.writeheader()
        writer.writerow(row)

def log_round_metadata(game_id, round_id, num_alive, num_killed):
    write_csv("dim_round.csv",
              ["game_id", "round_id", "timestamp", "num_alive", "num_killed"],
              {"game_id": game_id, "round_id": round_id, "timestamp": datetime.now().isoformat(), "num_alive": num_alive, "num_killed": num_killed})

def log_agent_metadata(game_id, agent_id, role, model_name, color):
    write_csv("dim_agent.csv",
              ["game_id", "agent_id", "role", "model_name", "color"],
              {"game_id": game_id, "agent_id": agent_id, "role": role, "model_name": model_name, "color": color})

def log_reflection(game_id, round_id, agent_id, reflection):
    write_csv("dim_reflection.csv",
              ["game_id", "round_id", "agent_id", "reflection"],
              {"game_id": game_id, "round_id": round_id, "agent_id": agent_id, "reflection": reflection})

def log_trust_change(game_id, round_id, agent_id, target_agent, trust_delta):
    write_csv("dim_trust.csv",
              ["game_id", "round_id", "agent_id", "target_agent", "trust_delta"],
              {"game_id": game_id, "round_id": round_id, "agent_id": agent_id, "target_agent": target_agent, "trust_delta": trust_delta})

def log_vote(game_id, round_id, agent_id, vote_target):
    write_csv("dim_vote.csv",
              ["game_id", "round_id", "agent_id", "vote_target"],
              {"game_id": game_id, "round_id": round_id, "agent_id": agent_id, "vote_target": vote_target})

def log_consensus(game_id, round_id, decision, agreement):
    write_csv("dim_consensus.csv",
              ["game_id", "round_id", "consensus_decision", "agreement_level"],
              {"game_id": game_id, "round_id": round_id, "consensus_decision": decision, "agreement_level": agreement})

def log_game_event(game_id, round_id, agent_id, room, was_killed, vote_cast, vote_target, ejected, vote_correct, trust_change, consensus_reached, agreement_level):
    write_csv("fact_game_events.csv",
              ["game_id", "round_id", "agent_id", "room", "was_killed", "vote_cast", "vote_target", "ejected", "vote_correct", "trust_change", "consensus_reached", "agreement_level"],
              {"game_id": game_id,
               "round_id": round_id,
               "agent_id": agent_id,
               "room": room,
               "was_killed": was_killed,
               "vote_cast": vote_cast,
               "vote_target": vote_target,
               "ejected": ejected,
               "vote_correct": vote_correct,
               "trust_change": trust_change,
               "consensus_reached": consensus_reached,
               "agreement_level": agreement_level})
