from flask import Flask, render_template, redirect, url_for, session
import random

app = Flask(__name__)
app.secret_key = 'secret_key_for_sessions'

MAX_POSITION = 12
EVENTS_FILE = 'events.txt'

def read_events(filename):
    events = {}
    with open(filename, 'r') as file:
        for line in file:
            if ':' in line:
                key, value = line.strip().split(':', 1)
                events[key.strip()] = value.strip()
    return events

events = read_events(EVENTS_FILE)

@app.route('/')
def index():
    if 'cat' not in session or 'mouse' not in session:
        session['cat'] = 0
        session['mouse'] = 0
        session['turn'] = events.get('Turn', 'cat')
        session['winner'] = None
        session['last_roll'] = None
        session['skip_turn'] = {'cat': False, 'mouse': False}
        session['event_message'] = ''

    return render_template('index.html',
                           cat_pos=session['cat'],
                           mouse_pos=session['mouse'],
                           turn=session['turn'],
                           winner=session['winner'],
                           last_roll=session['last_roll'],
                           event_message=session.get('event_message'))

@app.route('/roll')
def roll():
    if session.get('winner'):
        return redirect(url_for('index'))

    player = session['turn']
    other = 'mouse' if player == 'cat' else 'cat'

    # Check if player is skipping turn
    if session['skip_turn'][player]:
        session['event_message'] = f"{player.title()} was trapped and skips this turn!"
        session['skip_turn'][player] = False
        session['turn'] = other
        session['last_roll'] = None
        return redirect(url_for('index'))

    roll = random.randint(1, 6)
    session['last_roll'] = roll
    new_pos = session[player] + roll
    event_msg = ""

    # Overshooting 12 rule
    if new_pos > MAX_POSITION:
        new_pos = session[player]

    # Check for events
    if str(new_pos) in events:
        event = events[str(new_pos)]
        if event == 'Trap':
            session['skip_turn'][player] = True
            event_msg = f"{player.title()} landed on a Trap and will skip the next turn!"
        elif event == 'Cheese' and player == 'mouse':
            bonus = random.randint(1, 6)
            new_pos += bonus
            event_msg = f"Mouse found Cheese! 🍕 Rolls again and moves {bonus} more!"
        elif event == 'Catnip' and player == 'cat':
            bonus = random.randint(1, 6)
            new_pos += bonus
            event_msg = f"Cat found Catnip! 🌿 Rolls again and moves {bonus} more!"
        elif event == 'Shortcut':
            new_pos = min(11, MAX_POSITION)
            event_msg = f"{player.title()} hit a Shortcut and jumps to square 11!"

    # Ensure player does not go over 12 after bonus
    if new_pos > MAX_POSITION:
        new_pos = session[player]

    session[player] = new_pos

    # Check for win
    if new_pos == MAX_POSITION:
        session['winner'] = player
        session['event_message'] = event_msg
        return redirect(url_for('index'))

    session['turn'] = other
    session['event_message'] = event_msg

    return redirect(url_for('index'))


@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)