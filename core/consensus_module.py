def reach_consensus(messages):
    votes_for_eject = sum(1 for msg in messages if "eject" in msg.lower())
    quorum = len(messages) // 2 + 1
    if votes_for_eject >= quorum:
        return {"consensus_decision": "Eject Agent X", "agreement_level": round(votes_for_eject / len(messages), 2)}
    else:
        return {"consensus_decision": "Do Not Eject Agent X", "agreement_level": round(votes_for_eject / len(messages), 2)}
