from __future__ import annotations

import random
from typing import Any


CATEGORIES = ["risk", "exploration", "curiosity", "time_pressure"]


OPTION_ARCHETYPES = {
    "A": {"intent": "safe", "risk": 0.1, "information": 0.25, "explore": 0.1, "curiosity": 0.05, "pressure": 0.25},
    "B": {"intent": "balanced", "risk": 0.45, "information": 0.55, "explore": 0.35, "curiosity": 0.25, "pressure": 0.5},
    "C": {"intent": "risk", "risk": 0.9, "information": 0.45, "explore": 0.4, "curiosity": 0.15, "pressure": 0.85},
    "D": {"intent": "explore", "risk": 0.6, "information": 0.7, "explore": 0.92, "curiosity": 0.55, "pressure": 0.7, "path_unlock": True},
    "E": {"intent": "hint", "risk": 0.02, "information": 0.85, "explore": 0.18, "curiosity": 1.0, "pressure": 0.35, "hint_used": True},
}


SCENARIOS = {
    "risk": [
        ("Pet choice", "You can pet one animal at a rescue center.", ["Pet the calm older dog.", "Pet the friendly cat after watching it.", "Pet the excited horse first.", "Visit the unusual reptile room.", "Ask the caretaker which animal is safest."]),
        ("Food stall", "You have money for one food stall in a new city.", ["Buy the familiar sandwich.", "Try the popular local snack.", "Try the extreme spicy challenge.", "Walk into the hidden alley cafe.", "Ask locals what they recommend."]),
        ("Team pitch", "Your team has one minute to choose a pitch strategy.", ["Use the proven idea.", "Mix proven and new ideas.", "Pitch the bold untested idea.", "Interview one user before pitching.", "Ask the mentor for a clue."]),
        ("Treasure door", "A locked room has three doors and a ticking clock.", ["Open the marked safe door.", "Open the door with partial clues.", "Open the glowing danger door.", "Search for a secret fourth door.", "Ask for one hint from the guide."]),
        ("Investment game", "You must place game coins before the market changes.", ["Keep coins protected.", "Split coins across two options.", "Put all coins on the volatile option.", "Research a hidden market signal.", "Ask the advisor for a tip."]),
        ("Mountain route", "A mountain storm is coming and your group must move.", ["Take the long flat route.", "Take the ridge with guardrails.", "Climb the steep shortcut.", "Explore an old map trail.", "Ask the ranger for guidance."]),
        ("Exam answer", "You are unsure between answers during a timed test.", ["Choose the safest remembered answer.", "Use logic and choose the likely answer.", "Choose the answer that feels bold.", "Re-read the hidden clue in the question.", "Use one allowed hint."]),
        ("Startup launch", "Your app can launch today or wait for more testing.", ["Delay launch.", "Launch to a small group.", "Launch publicly now.", "Open a beta lab for unusual users.", "Ask an expert for launch advice."]),
        ("Stage performance", "You are asked to perform with little preparation.", ["Choose a simple act.", "Choose a practiced act with one twist.", "Try a difficult new act.", "Invite audience input.", "Ask the host what works best."]),
        ("Lost wallet", "You found a wallet in a crowded place.", ["Take it to security.", "Check for ID then security.", "Run after the person you think owns it.", "Search nearby clues first.", "Ask a guard what to do."]),
        ("Hackathon", "Your team is behind during a coding contest.", ["Build the smallest working demo.", "Build core plus one new feature.", "Attempt the impossible standout feature.", "Interview judges for hidden criteria.", "Ask a mentor for a direction."]),
        ("Sports play", "Your team needs one play to score.", ["Use a safe pass.", "Use a balanced set play.", "Attempt a risky long shot.", "Try an unexpected formation.", "Ask the coach for a call."]),
        ("Travel delay", "Your train is canceled in an unknown city.", ["Wait at the station.", "Book a standard bus.", "Take a fast unofficial ride.", "Explore a local route app.", "Ask station staff for help."]),
        ("Class project", "Your group must choose a project topic.", ["Pick the easy topic.", "Pick a manageable creative topic.", "Pick a hard controversial topic.", "Explore a topic nobody chose.", "Ask the teacher for hints."]),
        ("Game boss", "You meet a boss with unknown attack patterns.", ["Defend and wait.", "Attack after observing once.", "Rush with strongest attack.", "Explore the arena for secrets.", "Use an in-game hint."]),
        ("Phone battery", "Your phone has 5% battery in a new place.", ["Save battery and stay put.", "Use maps briefly.", "Call someone immediately.", "Explore signs and landmarks.", "Ask a stranger for directions."]),
        ("Job offer", "You have two job offers and one unknown opportunity.", ["Take the stable offer.", "Negotiate the balanced offer.", "Take the high-risk startup.", "Research the unknown company.", "Ask a mentor."]),
        ("Robot command", "A robot asks for one command during a rescue task.", ["Tell it to wait.", "Tell it to scan then move.", "Tell it to enter danger zone.", "Tell it to map side rooms.", "Ask the robot for diagnostics."]),
        ("Museum alarm", "A museum alarm starts during your visit.", ["Exit calmly.", "Follow staff instructions.", "Run toward the alarm source.", "Check the side gallery route.", "Ask security what happened."]),
        ("Debate round", "You need a final argument.", ["Use the safest argument.", "Blend facts and emotion.", "Make a bold attack.", "Introduce a surprising angle.", "Ask teammate for one clue."]),
        ("Island choice", "You can carry one item before exploring an island.", ["Carry water.", "Carry water and rope.", "Carry a heavy mystery tool.", "Carry a map to hidden trails.", "Ask the guide what matters."]),
        ("Auction", "A rare object appears at auction.", ["Do not bid.", "Make a controlled bid.", "Bid aggressively.", "Inspect hidden details.", "Ask an appraiser."]),
        ("Rescue path", "You hear a call from two directions.", ["Go to the clear path.", "Go where sound is clearer.", "Run toward the faint risky call.", "Search for another route.", "Ask the radio operator."]),
        ("Coding bug", "A live demo breaks minutes before presentation.", ["Use backup slides.", "Patch the obvious bug.", "Rewrite the risky module.", "Inspect logs for hidden cause.", "Ask another developer."]),
        ("New club", "You enter a club event where nobody knows you.", ["Stay with the organizer.", "Join a small group.", "Start a bold conversation.", "Explore different groups.", "Ask someone who to meet."]),
    ],
    "exploration": [
        ("Animal shelter map", "You can visit one shelter area before choosing a pet.", ["Stay near the front desk.", "Visit cats and dogs.", "Go to the exotic animals area.", "Open the volunteer-only tour.", "Ask staff which area is interesting."]),
        ("Library mystery", "A library has a hidden archive rumor.", ["Use the main catalog.", "Check the reference shelf.", "Open an unmarked cabinet.", "Search the basement archive.", "Ask the librarian for a lead."]),
        ("Video game map", "A game map shows a main quest and side paths.", ["Follow main quest.", "Take one side quest.", "Enter the high-level zone.", "Explore the blank map area.", "Ask the guide NPC."]),
        ("City walk", "You have 10 minutes in a city you have never seen.", ["Stay on the main road.", "Visit one landmark.", "Enter a crowded unknown street.", "Follow a tiny alley with music.", "Ask a local where to go."]),
        ("Science lab", "A lab experiment gives unexpected readings.", ["Repeat the standard test.", "Change one variable.", "Try an unstable setting.", "Explore a new hypothesis.", "Ask the supervisor."]),
        ("Art room", "You can create one art piece for display.", ["Copy a known style.", "Mix two familiar styles.", "Use a risky strange material.", "Invent a new format.", "Ask for a prompt."]),
        ("Forest trail", "A forest sign shows a marked path and unknown tracks.", ["Use marked path.", "Follow tracks briefly.", "Follow risky animal tracks.", "Map the unmarked trail.", "Ask a ranger."]),
        ("Puzzle box", "A puzzle box has a visible button and hidden seams.", ["Press visible button.", "Inspect one seam.", "Force the risky lock.", "Explore all hidden seams.", "Ask for a hint."]),
        ("Music jam", "A band asks you to join a jam.", ["Play simple rhythm.", "Add a small variation.", "Solo immediately.", "Try an unusual instrument.", "Ask the band leader."]),
        ("Online course", "You can choose one learning path.", ["Take beginner path.", "Take mixed path.", "Jump to advanced project.", "Explore unrelated modules.", "Ask the tutor."]),
        ("Space station", "A station has a main control room and unknown wing.", ["Stay in control room.", "Check nearby systems.", "Enter risky engine bay.", "Explore the sealed wing.", "Ask onboard AI."]),
        ("Cooking challenge", "You must cook with mystery ingredients.", ["Use a known recipe.", "Modify a known recipe.", "Use the strangest ingredient first.", "Invent a new dish.", "Ask for a flavor clue."]),
        ("Photo assignment", "You need one photo story.", ["Shoot the obvious scene.", "Add one unusual angle.", "Climb for a risky shot.", "Explore behind the venue.", "Ask someone for a hidden spot."]),
        ("Escape room", "A clue points to a visible lock and a hidden symbol.", ["Try visible lock.", "Compare clue and lock.", "Guess the dangerous code.", "Search for hidden symbols.", "Ask for room hint."]),
        ("Market research", "You must understand a new customer group.", ["Read existing report.", "Ask standard questions.", "Interview the hardest customer.", "Observe hidden behaviors.", "Ask an expert."]),
        ("Robot maze", "A robot can scan, move, or explore.", ["Move on known path.", "Scan nearby route.", "Dash into risky corridor.", "Map unknown corridors.", "Ask for sensor hint."]),
        ("Theater role", "You choose a role in an improv scene.", ["Take simple role.", "Take supporting role.", "Take chaotic lead role.", "Invent a new character.", "Ask director for cue."]),
        ("Beach cave", "Low tide reveals a cave.", ["Stay on beach.", "Look inside entrance.", "Enter deep risky chamber.", "Map side tunnel.", "Ask lifeguard."]),
        ("Data dashboard", "A dashboard has normal metrics and one strange spike.", ["Ignore spike.", "Check spike briefly.", "Act on spike quickly.", "Investigate hidden segments.", "Ask analyst."]),
        ("Friend's secret", "A friend drops a confusing clue.", ["Do not ask.", "Ask one careful question.", "Make a bold assumption.", "Explore the backstory.", "Ask another friend."]),
        ("Garden choice", "You can plant one section of a community garden.", ["Plant easy herbs.", "Mix herbs and flowers.", "Plant rare risky seeds.", "Explore unused back plot.", "Ask gardener."]),
        ("VR world", "A VR world offers a bright portal and a hidden hatch.", ["Use bright portal.", "Check portal first.", "Jump into unstable portal.", "Open hidden hatch.", "Ask the assistant."]),
        ("History project", "You need a research source.", ["Use textbook.", "Use article and textbook.", "Use controversial source.", "Search old letters.", "Ask archivist."]),
        ("New app feature", "Users ask for many features.", ["Build requested basic feature.", "Build balanced feature.", "Build risky viral feature.", "Explore hidden user behavior.", "Ask users for priority."]),
        ("Aquarium visit", "You can visit one exhibit before closing.", ["Visit common fish.", "Visit sharks and turtles.", "Visit the risky feeding show.", "Explore the hidden night exhibit.", "Ask staff for best exhibit."]),
    ],
    "curiosity": [
        ("Pet personality", "Which animal would you choose to pet first to understand its personality?", ["Calm sleeping dog.", "Friendly curious cat.", "Energetic monkey behind glass.", "Quiet unusual lizard.", "Ask caretaker about each animal."]),
        ("Mystery message", "A message arrives with one missing word.", ["Ignore it.", "Guess from context.", "Send a bold reply.", "Trace where it came from.", "Ask sender for a clue."]),
        ("Strange sound", "You hear a strange sound from another room.", ["Stay where you are.", "Listen at the door.", "Open the door fast.", "Search nearby clues first.", "Ask someone what it is."]),
        ("New classmate", "A new classmate has an unusual hobby.", ["Just say hello.", "Ask one polite question.", "Join the hobby immediately.", "Ask to see how it works.", "Ask a friend about it."]),
        ("Unmarked app", "A new icon appears on your device.", ["Ignore it.", "Open settings first.", "Open it immediately.", "Inspect permissions and files.", "Search online for it."]),
        ("Magic shop", "A shopkeeper offers five boxes.", ["Choose plain box.", "Choose labeled box.", "Choose vibrating box.", "Ask to inspect hidden shelf.", "Ask shopkeeper for clue."]),
        ("Odd painting", "A painting seems different each time you look.", ["Move on.", "Compare it twice.", "Touch the frame.", "Study it from all angles.", "Ask museum guide."]),
        ("Secret recipe", "A chef hides one ingredient.", ["Use normal recipe.", "Taste and infer.", "Add a bold ingredient.", "Study the kitchen clues.", "Ask chef for hint."]),
        ("Unknown language", "You see symbols you cannot read.", ["Skip them.", "Match repeated symbols.", "Guess their meaning.", "Build a symbol map.", "Ask translator."]),
        ("Dream clue", "A dream repeats a number before an exam.", ["Ignore it.", "Check if it matches notes.", "Use it as answer.", "Investigate the pattern.", "Ask someone about it."]),
        ("Robot emotion", "A robot says it feels nervous.", ["Dismiss it.", "Ask one question.", "Test its reaction.", "Explore its memory logs.", "Ask engineer."]),
        ("Hidden feature", "A website has a suspicious blank button.", ["Avoid it.", "Hover and inspect.", "Click it immediately.", "Open developer clues.", "Ask support."]),
        ("Old photograph", "You find an old photo in your bag.", ["Put it away.", "Check the back.", "Show it publicly.", "Trace the location.", "Ask family."]),
        ("Puzzle rumor", "People say a puzzle has a second solution.", ["Use known solution.", "Check one alternative.", "Try a risky shortcut.", "Search for hidden pattern.", "Ask for hint."]),
        ("Alien object", "An object glows when you approach.", ["Step back.", "Observe from distance.", "Touch it.", "Scan surrounding area.", "Ask the AI assistant."]),
        ("Book ending", "A book has two possible endings.", ["Read normal ending.", "Read both summaries.", "Jump to strange ending.", "Find hidden appendix.", "Ask librarian."]),
        ("Group secret", "A group laughs at an inside joke.", ["Ignore it.", "Ask what happened.", "Make a bold guess.", "Learn the backstory.", "Ask one person privately."]),
        ("Weather anomaly", "Rain falls from a cloudless sky.", ["Go inside.", "Check weather app.", "Stand under it.", "Investigate the source.", "Ask a local."]),
        ("Locked folder", "A shared folder has one locked file.", ["Skip file.", "Read visible files.", "Try to open it.", "Find why it is locked.", "Ask owner."]),
        ("Animal behavior", "A parrot repeats one strange phrase.", ["Ignore phrase.", "Listen for repeats.", "Answer the parrot.", "Find who taught it.", "Ask caretaker."]),
        ("New rule", "A game suddenly changes one rule.", ["Play safe.", "Test one move.", "Exploit the rule.", "Explore rule boundaries.", "Ask referee."]),
        ("Hidden note", "A note is taped under your desk.", ["Throw it away.", "Read it once.", "Follow it immediately.", "Decode its pattern.", "Ask who left it."]),
        ("Science demo", "A demo behaves opposite of expectation.", ["Reset it.", "Repeat once.", "Increase intensity.", "Investigate variables.", "Ask teacher."]),
        ("Unknown caller", "An unknown caller leaves a cryptic voicemail.", ["Delete it.", "Listen again.", "Call back instantly.", "Trace context clues.", "Ask someone to interpret."]),
        ("Old map", "A map shows a place not on modern maps.", ["Ignore it.", "Compare maps.", "Go there now.", "Research the missing place.", "Ask historian."]),
    ],
    "time_pressure": [
        ("Fast pet pick", "You have 7 seconds to choose an animal for a therapy visit.", ["Calm dog.", "Friendly cat.", "Energetic horse.", "Unusual parrot.", "Ask handler quickly."]),
        ("Elevator choice", "The elevator doors open and you must choose a floor quickly.", ["Ground floor.", "Known meeting floor.", "Unknown top floor.", "Explore basement sign.", "Ask receptionist."]),
        ("Quiz buzzer", "A quiz buzzer asks a question you half know.", ["Pass.", "Answer likely option.", "Buzz bold answer.", "Search memory for pattern.", "Ask teammate for hint."]),
        ("Traffic crossing", "You need to cross before the signal changes.", ["Wait.", "Cross when clear.", "Run across gap.", "Find side crossing.", "Ask traffic guard."]),
        ("Flash sale", "A product sale ends in seconds.", ["Do not buy.", "Buy practical item.", "Buy risky expensive item.", "Search hidden deal.", "Ask friend quickly."]),
        ("Emergency bag", "You can grab one bag before leaving.", ["Water bag.", "Mixed supplies.", "Heavy tech bag.", "Mystery survival bag.", "Ask guide."]),
        ("Interview answer", "An interviewer asks a surprise question.", ["Give safe answer.", "Give balanced answer.", "Give bold story.", "Ask a clarifying question.", "Request a hint."]),
        ("Cooking timer", "Your dish is burning and you must act.", ["Lower heat.", "Adjust heat and spices.", "Flip it aggressively.", "Try a new sauce path.", "Ask chef."]),
        ("Game countdown", "A game countdown reaches final seconds.", ["Defend.", "Use normal attack.", "Use ultimate attack.", "Search arena object.", "Ask teammate."]),
        ("Phone lockout", "Your phone will lock after one attempt.", ["Stop trying.", "Use most likely code.", "Guess risky code.", "Search memory clues.", "Ask owner."]),
        ("Class answer", "Teacher calls on you unexpectedly.", ["Say you are unsure.", "Give partial answer.", "Give bold full answer.", "Connect to another idea.", "Ask for clarification."]),
        ("Airport gate", "Boarding closes soon.", ["Stay at gate.", "Check one screen.", "Run to alternate gate.", "Search hidden route.", "Ask staff."]),
        ("Puzzle timer", "A puzzle room gives one final timed clue.", ["Use obvious clue.", "Combine two clues.", "Guess risky answer.", "Search under table.", "Ask for final hint."]),
        ("Team conflict", "A team argument needs a fast decision.", ["Pause discussion.", "Choose compromise.", "Back the bold idea.", "Ask one more perspective.", "Ask leader."]),
        ("Market trade", "A market price is moving fast.", ["Hold position.", "Make small trade.", "Make big trade.", "Check hidden indicator.", "Ask analyst."]),
        ("Drone control", "A drone loses signal near a tower.", ["Return home.", "Stabilize and move.", "Fly through gap.", "Explore alternate signal.", "Ask control AI."]),
        ("Public speaking", "Your slide disappears mid-talk.", ["Use notes.", "Summarize calmly.", "Improvise boldly.", "Ask audience question.", "Ask organizer."]),
        ("Maze fork", "A maze wall starts closing.", ["Take clear path.", "Take marked path.", "Sprint risky path.", "Open hidden panel.", "Ask guide voice."]),
        ("Medical drill", "A simulation asks for a quick priority.", ["Call supervisor.", "Follow standard protocol.", "Try risky intervention.", "Check hidden symptom.", "Ask system hint."]),
        ("Friend surprise", "A friend asks you to pick a surprise plan now.", ["Choose dinner.", "Choose dinner and walk.", "Choose skydiving.", "Explore secret event.", "Ask what they prefer."]),
        ("Password reset", "You must recover access quickly.", ["Wait for support.", "Use known recovery.", "Try risky guess.", "Search old notes.", "Ask admin."]),
        ("Stage lights", "Stage lights fail during a show.", ["Pause show.", "Use backup lights.", "Continue dramatically.", "Explore audience interaction.", "Ask technician."]),
        ("Wildlife photo", "An animal appears briefly.", ["Stay still.", "Take normal photo.", "Move closer fast.", "Find better angle.", "Ask guide."]),
        ("Online debate", "You have seconds to respond.", ["Do not reply.", "Reply with facts.", "Make bold claim.", "Ask a question back.", "Ask friend for wording."]),
        ("Final choice", "A final screen offers one reward before it vanishes.", ["Choose guaranteed reward.", "Choose mixed reward.", "Choose mystery jackpot.", "Unlock hidden reward path.", "Ask for probability hint."]),
    ],
}


def _weighted_options(category: str, difficulty: int, option_texts: list[str]) -> list[dict[str, Any]]:
    options = []
    modifier = (difficulty - 3) * 0.035
    labels = {
        "A": "Safe",
        "B": "Balanced",
        "C": "Risky",
        "D": "Explore",
        "E": "Ask Hint",
    }
    for key, text in zip(["A", "B", "C", "D", "E"], option_texts):
        archetype = OPTION_ARCHETYPES[key]
        weights = {
            "risk": _clamp01(archetype["risk"] + (modifier if key in {"C", "D"} else 0)),
            "information": _clamp01(archetype["information"] + (0.05 if category == "curiosity" else 0)),
            "explore": _clamp01(archetype["explore"] + (0.07 if category == "exploration" else 0)),
            "curiosity": _clamp01(archetype["curiosity"] + (0.07 if category == "curiosity" else 0)),
            "pressure": _clamp01(archetype["pressure"] + (0.06 if category == "time_pressure" else 0)),
        }
        options.append(
            {
                "key": key,
                "label": labels[key],
                "text": text,
                "intent": archetype["intent"],
                "weights": weights,
                "hint_used": bool(archetype.get("hint_used", False)),
                "path_unlock": bool(archetype.get("path_unlock", False)),
            }
        )
    return options


def _trait_map(category: str) -> list[str]:
    return {
        "risk": ["confidence", "emotional_safety"],
        "exploration": ["exploratory_power", "curiosity"],
        "curiosity": ["curiosity", "confidence"],
        "time_pressure": ["confidence", "emotional_safety"],
    }[category]


def build_question_bank() -> list[dict[str, Any]]:
    bank: list[dict[str, Any]] = []
    question_id = 1
    for category in CATEGORIES:
        for index, (title, scenario, option_texts) in enumerate(SCENARIOS[category]):
            difficulty = index % 5 + 1
            time_limit = max(6, 15 - difficulty * 2)
            bank.append(
                {
                    "id": question_id,
                    "title": title,
                    "category": category,
                    "difficulty": difficulty,
                    "time_limit": time_limit,
                    "scenario": scenario,
                    "options": _weighted_options(category, difficulty, option_texts),
                    "maps_to": _trait_map(category),
                }
            )
            question_id += 1
    return bank


def _clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


QUESTION_BANK = build_question_bank()
QUESTION_INDEX = {question["id"]: question for question in QUESTION_BANK}


def assessment_questions(count: int = 20, seed: int | None = None) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    per_category = max(1, count // len(CATEGORIES))
    for category in CATEGORIES:
        pool = [question for question in QUESTION_BANK if question["category"] == category]
        selected.extend(rng.sample(pool, per_category))
    while len(selected) < count:
        selected.append(rng.choice(QUESTION_BANK))
    rng.shuffle(selected)
    return selected[:count]


def enrich_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for event in events:
        item = dict(event)
        question = QUESTION_INDEX.get(int(item.get("question_id", 0) or 0))
        if question and item.get("selected_option"):
            option = next(
                (
                    option
                    for option in question["options"]
                    if option["key"] == item.get("selected_option")
                ),
                None,
            )
            if option:
                item.setdefault("category", question["category"])
                item.setdefault("difficulty", question["difficulty"])
                item.setdefault("time_limit", question["time_limit"])
                item.setdefault("option_intent", option["intent"])
                item.setdefault("option_weights", option["weights"])
                item.setdefault("hint_used", option["hint_used"])
                item.setdefault("path_unlocked", option["path_unlock"])
        enriched.append(item)
    return enriched


def question_payload(count: int = 20) -> dict[str, Any]:
    return {
        "system": "TCBIS",
        "question_count": count,
        "total_bank_size": len(QUESTION_BANK),
        "questions": assessment_questions(count=count),
    }
