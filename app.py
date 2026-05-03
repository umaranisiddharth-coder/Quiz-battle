from werkzeug.security import check_password_hash, generate_password_hash
import os, csv, io
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room
import secrets
import random
import threading
import time
from datetime import date, datetime, timedelta
from database import (init_db, get_user, get_questions, save_game_result,
                      get_leaderboard, get_user_rank, get_weekly_leaderboard,
                      get_battle_stats, flag_question, get_flagged_questions,
                      update_question, get_achievements, unlock_achievement,
                      get_daily_completion, mark_daily_done)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'quiz-battle-dev-secret-key-change-in-prod')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

battle_rooms = {}
lobby_chat   = []          # global lobby chat messages (last 50)

BOT_PROFILES = {
    'easy':   {'name': '🤖 EasyBot',  'accuracy': 0.40, 'min_delay': 9,  'max_delay': 14},
    'medium': {'name': '🤖 MedBot',   'accuracy': 0.65, 'min_delay': 5,  'max_delay': 10},
    'hard':   {'name': '🤖 HardBot',  'accuracy': 0.88, 'min_delay': 2,  'max_delay': 6},
}

LEVELS = [
    {'name':'Rookie', 'emoji':'🌱','min':0,   'max':99},
    {'name':'Player', 'emoji':'🎮','min':100, 'max':299},
    {'name':'Pro',    'emoji':'⚡','min':300, 'max':599},
    {'name':'Expert', 'emoji':'🔥','min':600, 'max':999},
    {'name':'Legend', 'emoji':'👑','min':1000,'max':99999},
]

def get_level(score):
    for lv in LEVELS:
        if lv['min'] <= score <= lv['max']:
            return lv
    return LEVELS[-1]

# ─────────────────────────────────────────────
#  Page routes
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/battle')
def battle():
    if 'user_id' not in session:
        return render_template('index.html')
    return render_template('battle.html')

@app.route('/leaderboard')
def leaderboard():
    leaders       = get_leaderboard(20)
    weekly        = get_weekly_leaderboard(20)
    username      = session.get('username', '')
    emoji         = session.get('emoji', '🎮')
    rank, user_row = get_user_rank(username) if username else (None, None)
    return render_template('leaderboard.html',
                           leaders=leaders, weekly=weekly,
                           current_user=username, current_emoji=emoji,
                           current_rank=rank, current_row=user_row)

# ─────────────────────────────────────────────
#  Auth
# ─────────────────────────────────────────────

@app.route('/login', methods=['POST'])
def login():
    data     = request.json
    username = data.get('username', '').strip()
    emoji    = data.get('emoji', '🎮')
    if not username:
        return jsonify({'success': False, 'message': 'Username required'})

    user = get_user(username, emoji)
    session['user_id']  = user[0]
    session['username'] = user[1]
    session['emoji']    = emoji

    rank, _ = get_user_rank(username)
    battle_stats = get_battle_stats(user[0])

    return jsonify({
        'success': True,
        'user': {
            'id': user[0], 'name': user[1], 'emoji': emoji,
            'total_score': user[3], 'games_played': user[4],
            'rank': rank,
            'wins': battle_stats['wins'],
            'losses': battle_stats['losses'],
        }
    })

# ─────────────────────────────────────────────
#  Solo Quiz
# ─────────────────────────────────────────────

@app.route('/quiz/start', methods=['POST'])
def start_quiz():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    data          = request.json
    difficulty    = data.get('difficulty', None)
    category      = data.get('category', None)
    num_questions = int(data.get('num_questions', 10))
    timer_mode    = data.get('timer_mode', 'normal')   # blitz | normal | chill

    used_ids  = session.get('used_question_ids', [])
    questions = get_questions(limit=num_questions, difficulty=difficulty,
                              category=category, exclude_ids=used_ids)
    if len(questions) < num_questions:
        questions = get_questions(limit=num_questions, difficulty=difficulty, category=category)

    # Difficulty progression: sort easy→medium→hard when mixed
    if not difficulty:
        order = {'easy': 0, 'medium': 1, 'hard': 2}
        questions = sorted(questions, key=lambda q: order.get(q[7], 1))

    quiz_questions = []
    for q in questions:
        quiz_questions.append({
            'id': q[0], 'question': q[1],
            'options': [q[2], q[3], q[4], q[5]],
            # correct_answer intentionally omitted — validated server-side on submit
            'difficulty': q[7], 'category': q[8],
            'hint': q[9] if len(q) > 9 else ''
        })

    new_used = used_ids + [q[0] for q in questions]
    session['used_question_ids'] = new_used
    session['correct_answers']   = {str(q[0]): q[6] for q in questions}
    session['quiz_started']      = True
    session['quiz_category']     = category or 'mixed'
    session['timer_mode']        = timer_mode

    timer_seconds = {'blitz': 5, 'normal': 15, 'chill': 30}.get(timer_mode, 15)

    return jsonify({'success': True, 'questions': quiz_questions,
                    'timer_seconds': timer_seconds, 'timer_mode': timer_mode})

@app.route('/quiz/submit', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session or not session.get('quiz_started'):
        return jsonify({'success': False, 'message': 'Invalid session'})

    data            = request.json
    answers         = data.get('answers', {})
    time_bonuses    = data.get('time_bonuses', {})
    correct_answers = session.get('correct_answers', {})

    score = 0
    correct_count = 0
    results = []

    for q_id_str, user_answer in answers.items():
        correct_ans = correct_answers.get(str(q_id_str))
        is_correct  = (user_answer == correct_ans)
        if is_correct:
            correct_count += 1
            score += 10 + time_bonuses.get(q_id_str, 0)
        results.append({'question_id': q_id_str, 'correct': is_correct,
                        'user_answer': user_answer, 'correct_answer': correct_ans})

    save_game_result(session['user_id'], score, len(correct_answers), 'single',
                     correct_count=correct_count,
                     category=session.get('quiz_category', 'mixed'))
    session.pop('correct_answers', None)
    session.pop('quiz_started', None)
    session.pop('quiz_category', None)
    session.pop('timer_mode', None)

    return jsonify({'success': True, 'score': score,
                    'correct_count': correct_count,
                    'total_questions': len(correct_answers),
                    'results': results})  # results include correct_answer for post-quiz review

# ─────────────────────────────────────────────
#  Hint & Flag
# ─────────────────────────────────────────────

@app.route('/quiz/hint', methods=['POST'])
def get_hint():
    data = request.json
    q_id = data.get('question_id')
    import sqlite3
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('SELECT hint FROM questions WHERE id=?', (q_id,))
    row = c.fetchone()
    conn.close()
    hint = row[0] if row and row[0] else 'No hint available'
    return jsonify({'hint': hint})

@app.route('/quiz/flag', methods=['POST'])
def flag_q():
    if 'user_id' not in session:
        return jsonify({'success': False})
    data   = request.json
    q_id   = data.get('question_id')
    reason = data.get('reason', 'incorrect')
    flag_question(q_id, session['user_id'], reason)
    return jsonify({'success': True})

# ─────────────────────────────────────────────
#  Socket.IO – Human vs Human
# ─────────────────────────────────────────────

@socketio.on('create_room')
def handle_create_room(data):
    room_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
    used_ids  = session.get('used_question_ids', [])
    questions = get_questions(10, exclude_ids=used_ids)
    if len(questions) < 10:
        questions = get_questions(10)
    session['used_question_ids'] = used_ids + [q[0] for q in questions]
    battle_rooms[room_code] = {
        'players': [], 'questions': questions,
        'status': 'waiting', 'scores': {}, 'bot': False,
        'spectators': []
    }
    emit('room_created', {'room_code': room_code})

@socketio.on('join_battle')
def handle_join_battle(data):
    room_code = data.get('room_code')
    username  = session.get('username', 'Anonymous')
    user_id   = session.get('user_id')

    if room_code not in battle_rooms:
        emit('error', {'message': 'Room not found'}); return
    room = battle_rooms[room_code]

    # Spectator mode — room already playing
    if room['status'] == 'playing' or len(room['players']) >= 2:
        join_room(room_code)
        room['spectators'].append(username)
        emit('spectate_start', {
            'questions': _fmt(room['questions']),
            'players': room['players'],
            'scores': room['scores']
        })
        return

    room['players'].append({'username': username, 'user_id': user_id})
    room['scores'][username] = 0
    join_room(room_code)

    emit('player_joined', {'players': room['players'],
                           'player_count': len(room['players'])}, room=room_code)

    if len(room['players']) == 2:
        room['status'] = 'playing'
        emit('battle_start', {
            'questions': _fmt(room['questions']),
            'players': room['players']
        }, room=room_code)

@socketio.on('battle_answer')
def handle_battle_answer(data):
    room_code = data.get('room_code')
    if room_code not in battle_rooms: return
    room     = battle_rooms[room_code]
    username = session.get('username')
    correct  = _correct(room['questions'], data.get('question_id'))
    if data.get('answer') == correct:
        room['scores'][username] = room['scores'].get(username, 0) + 10
    emit('score_update', {'scores': room['scores']}, room=room_code)

@socketio.on('battle_complete')
def handle_battle_complete(data):
    room_code = data.get('room_code')
    if room_code not in battle_rooms: return
    room   = battle_rooms[room_code]
    scores = room['scores']
    winner = max(scores, key=scores.get)
    for p in room['players']:
        if p.get('user_id'):
            won = (p['username'] == winner)
            save_game_result(p['user_id'], scores[p['username']],
                             len(room['questions']), 'battle',
                             won=won)
    emit('battle_end', {'scores': scores, 'winner': winner}, room=room_code)

# ─────────────────────────────────────────────
#  Socket.IO – Human vs Computer (Bot)
# ─────────────────────────────────────────────

@socketio.on('start_bot_battle')
def handle_bot_battle(data):
    bot_level = data.get('bot_level', 'medium')
    category  = data.get('category', None)
    username  = session.get('username', 'Player')
    user_id   = session.get('user_id')

    bot      = BOT_PROFILES.get(bot_level, BOT_PROFILES['medium'])
    bot_name = bot['name']
    room_code = 'BOT_' + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))

    used_ids  = session.get('used_question_ids', [])
    questions = get_questions(10, category=category, exclude_ids=used_ids)
    if len(questions) < 10:
        questions = get_questions(10, category=category)
    session['used_question_ids'] = used_ids + [q[0] for q in questions]

    battle_rooms[room_code] = {
        'players': [
            {'username': username, 'user_id': user_id},
            {'username': bot_name, 'user_id': None, 'is_bot': True}
        ],
        'questions': questions, 'status': 'playing',
        'scores': {username: 0, bot_name: 0},
        'bot': True, 'bot_profile': bot, 'bot_name': bot_name,
        'player_done': False, 'bot_done': False,
        'spectators': []
    }

    join_room(room_code)
    emit('battle_start', {
        'questions': _fmt(questions),
        'players': battle_rooms[room_code]['players'],
        'room_code': room_code,
        'is_bot_battle': True,
        'bot_name': bot_name
    })

    threading.Thread(target=_bot_loop,
                     args=(room_code, questions, bot, bot_name),
                     daemon=True).start()

@socketio.on('bot_battle_answer')
def handle_bot_answer(data):
    room_code = data.get('room_code')
    if room_code not in battle_rooms: return
    room     = battle_rooms[room_code]
    username = session.get('username')
    correct  = _correct(room['questions'], data.get('question_id'))
    if data.get('answer') == correct:
        room['scores'][username] = room['scores'].get(username, 0) + 10
    socketio.emit('score_update', {'scores': room['scores']}, room=room_code)

@socketio.on('bot_battle_complete')
def handle_bot_battle_complete(data):
    room_code = data.get('room_code')
    if room_code not in battle_rooms: return
    battle_rooms[room_code]['player_done'] = True
    _check_end(room_code)

# ─────────────────────────────────────────────
#  Socket.IO – Lobby Chat
# ─────────────────────────────────────────────

@socketio.on('join_lobby')
def handle_join_lobby(data):
    join_room('lobby')
    emit('chat_history', {'messages': lobby_chat[-50:]})

@socketio.on('lobby_chat')
def handle_lobby_chat(data):
    username = session.get('username', 'Anonymous')
    emoji    = session.get('emoji', '🎮')
    msg = {
        'username': username,
        'emoji': emoji,
        'text': str(data.get('text', ''))[:200],
        'time': datetime.now().strftime('%H:%M')
    }
    lobby_chat.append(msg)
    if len(lobby_chat) > 50:
        lobby_chat.pop(0)
    emit('chat_message', msg, room='lobby')

# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _fmt(questions):
    return [{
        'id': q[0], 'question': q[1],
        'options': [q[2], q[3], q[4], q[5]],
        'correct_answer': q[6],
        'difficulty': q[7], 'category': q[8],
        'hint': q[9] if len(q) > 9 else ''
    } for q in questions]

def _correct(questions, question_id):
    for q in questions:
        if q[0] == question_id:
            return q[6]
    return None

def _bot_loop(room_code, questions, bot, bot_name):
    for q in questions:
        if room_code not in battle_rooms: return
        delay = random.uniform(bot['min_delay'], bot['max_delay'])
        time.sleep(delay)
        if room_code not in battle_rooms: return
        room = battle_rooms[room_code]
        chosen = q[6] if random.random() < bot['accuracy'] else \
                 random.choice([i for i in range(1, 5) if i != q[6]])
        if chosen == q[6]:
            room['scores'][bot_name] = room['scores'].get(bot_name, 0) + 10
        socketio.emit('score_update', {'scores': room['scores']}, room=room_code)
        socketio.emit('bot_answered', {
            'question_id': q[0], 'bot_name': bot_name,
            'correct': (chosen == q[6])
        }, room=room_code)
    if room_code in battle_rooms:
        battle_rooms[room_code]['bot_done'] = True
        _check_end(room_code)

def _check_end(room_code):
    if room_code not in battle_rooms: return
    room = battle_rooms[room_code]
    if room.get('player_done') and room.get('bot_done'):
        scores = room['scores']
        winner = max(scores, key=scores.get)
        for p in room['players']:
            if p.get('user_id'):
                won = (p['username'] == winner)
                save_game_result(p['user_id'], scores[p['username']],
                                 len(room['questions']), 'bot_battle', won=won)
        socketio.emit('battle_end', {
            'scores': scores, 'winner': winner, 'is_bot_battle': True
        }, room=room_code)
        battle_rooms.pop(room_code, None)

# ─────────────────────────────────────────────
#  Quiz History
# ─────────────────────────────────────────────

@app.route('/history')
def history():
    if 'user_id' not in session:
        return render_template('index.html')
    from database import get_game_history, get_category_stats
    games  = get_game_history(session['user_id'], 30)
    stats  = get_category_stats(session['user_id'])
    bstats = get_battle_stats(session['user_id'])
    _, user_row = get_user_rank(session['username'])
    level = get_level(user_row[2] if user_row else 0)
    return render_template('history.html',
                           games=games, stats=stats, bstats=bstats,
                           username=session.get('username',''),
                           emoji=session.get('emoji','🎮'),
                           level=level, user_row=user_row)

# ─────────────────────────────────────────────
#  Admin Panel
# ─────────────────────────────────────────────

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

def _check_admin_password(pw):
    """Accept plain-text env password or a werkzeug hash stored in env."""
    stored = ADMIN_PASSWORD
    if stored.startswith('pbkdf2:') or stored.startswith('scrypt:'):
        return check_password_hash(stored, pw)
    return pw == stored

@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method == 'POST' and _check_admin_password(request.form.get('password', '')):
        session['is_admin'] = True
    if not session.get('is_admin'):
        return render_template('admin_login.html')
    import sqlite3
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM game_results')
    total_games = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM questions')
    total_q = c.fetchone()[0]
    c.execute('SELECT category, COUNT(*) FROM questions GROUP BY category')
    cat_counts = c.fetchall()
    conn.close()
    flagged = get_flagged_questions()
    return render_template('admin.html',
                           total_users=total_users, total_games=total_games,
                           total_q=total_q, cat_counts=cat_counts,
                           flagged=flagged)

@app.route('/admin/add_question', methods=['POST'])
def admin_add_question():
    if not session.get('is_admin'):
        return jsonify({'success': False})
    data = request.json
    import sqlite3
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('''INSERT INTO questions
                 (question,option1,option2,option3,option4,correct_answer,difficulty,category,hint)
                 VALUES (?,?,?,?,?,?,?,?,?)''',
              (data['question'], data['option1'], data['option2'],
               data['option3'], data['option4'], int(data['correct_answer']),
               data['difficulty'], data['category'], data.get('hint','')))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return jsonify({'success': True, 'id': new_id})

@app.route('/admin/edit_question/<int:qid>', methods=['POST'])
def admin_edit_question(qid):
    if not session.get('is_admin'):
        return jsonify({'success': False})
    data = request.json
    update_question(qid, data)
    return jsonify({'success': True})

@app.route('/admin/delete_question/<int:qid>', methods=['POST'])
def admin_delete_question(qid):
    if not session.get('is_admin'):
        return jsonify({'success': False})
    import sqlite3
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('DELETE FROM questions WHERE id=?', (qid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/bulk_import', methods=['POST'])
def admin_bulk_import():
    if not session.get('is_admin'):
        return jsonify({'success': False})
    file = request.files.get('csv_file')
    if not file:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    try:
        content = file.read().decode('utf-8')
        reader  = csv.DictReader(io.StringIO(content))
        import sqlite3
        conn = sqlite3.connect('quiz.db')
        c = conn.cursor()
        count = 0
        for row in reader:
            c.execute('''INSERT INTO questions
                         (question,option1,option2,option3,option4,correct_answer,difficulty,category,hint)
                         VALUES (?,?,?,?,?,?,?,?,?)''',
                      (row.get('question',''), row.get('option1',''), row.get('option2',''),
                       row.get('option3',''), row.get('option4',''),
                       int(row.get('correct_answer', 1)),
                       row.get('difficulty','medium'), row.get('category','general'),
                       row.get('hint','')))
            count += 1
        conn.commit(); conn.close()
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/resolve_flag/<int:flag_id>', methods=['POST'])
def admin_resolve_flag(flag_id):
    if not session.get('is_admin'):
        return jsonify({'success': False})
    import sqlite3
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('UPDATE question_flags SET resolved=1 WHERE id=?', (flag_id,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

# ─────────────────────────────────────────────
#  Daily Challenge
# ─────────────────────────────────────────────

@app.route('/daily')
def daily():
    if 'user_id' not in session:
        return render_template('index.html')
    return render_template('daily.html')

@app.route('/daily/start', methods=['POST'])
def daily_start():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Login first'})
    today = str(date.today())

    # Check DB-persisted daily completion (not just session)
    from database import get_daily_completion, mark_daily_done
    if get_daily_completion(session['user_id'], today):
        return jsonify({'success': False, 'message': 'Already completed today!'})

    # Deterministic daily questions: fetch all IDs, seed with today, pick 10
    import sqlite3 as _sq
    conn = _sq.connect('quiz.db'); c = conn.cursor()
    c.execute('SELECT id FROM questions ORDER BY id')
    all_ids = [r[0] for r in c.fetchall()]; conn.close()

    rng = random.Random(today)
    chosen_ids = rng.sample(all_ids, min(10, len(all_ids)))

    questions = []
    conn = _sq.connect('quiz.db'); c = conn.cursor()
    for qid in chosen_ids:
        c.execute('SELECT * FROM questions WHERE id=?', (qid,))
        row = c.fetchone()
        if row: questions.append(row)
    conn.close()

    quiz_questions = [{'id': q[0], 'question': q[1],
                       'options': [q[2], q[3], q[4], q[5]],
                       'correct_answer': q[6], 'difficulty': q[7], 'category': q[8]}
                      for q in questions]
    session['daily_answers'] = {str(q[0]): q[6] for q in questions}
    return jsonify({'success': True, 'questions': quiz_questions, 'date': today})

@app.route('/daily/submit', methods=['POST'])
def daily_submit():
    if 'user_id' not in session:
        return jsonify({'success': False})
    data            = request.json
    answers         = data.get('answers', {})
    correct_answers = session.get('daily_answers', {})
    score = 0; correct_count = 0
    for q_id_str, user_answer in answers.items():
        if user_answer == correct_answers.get(str(q_id_str)):
            correct_count += 1; score += 15
    save_game_result(session['user_id'], score, len(correct_answers), 'daily')
    from database import mark_daily_done
    mark_daily_done(session['user_id'], str(date.today()))
    session.pop('daily_answers', None)
    return jsonify({'success': True, 'score': score,
                    'correct_count': correct_count,
                    'total_questions': len(correct_answers)})

# ─────────────────────────────────────────────
#  Achievements
# ─────────────────────────────────────────────

ACHIEVEMENTS = [
    {'id': 'first_game', 'name': 'First Blood',   'emoji': '🩸', 'desc': 'Play your first game'},
    {'id': 'perfect',    'name': 'Perfectionist', 'emoji': '💯', 'desc': 'Score 100% in a quiz'},
    {'id': 'streak5',    'name': 'On Fire',        'emoji': '🔥', 'desc': 'Get a 5-answer streak'},
    {'id': 'games10',    'name': 'Veteran',        'emoji': '🎖️', 'desc': 'Play 10 games'},
    {'id': 'score500',   'name': 'High Scorer',    'emoji': '🏆', 'desc': 'Reach 500 total score'},
    {'id': 'bot_win',    'name': 'Bot Slayer',     'emoji': '🤖', 'desc': 'Beat the computer'},
    {'id': 'battle_win', 'name': 'Gladiator',      'emoji': '⚔️', 'desc': 'Win a battle'},
    {'id': 'daily',      'name': 'Daily Warrior',  'emoji': '📅', 'desc': 'Complete daily challenge'},
    {'id': 'speed',      'name': 'Speed Demon',    'emoji': '⚡', 'desc': 'Answer in under 3 seconds'},
    {'id': 'games5',     'name': 'Regular',        'emoji': '🎮', 'desc': 'Play 5 games'},
]

@app.route('/achievements')
def achievements():
    if 'user_id' not in session:
        return render_template('index.html')
    from database import get_achievements, unlock_achievement
    unlocked = get_achievements(session['user_id'])
    _, user_row = get_user_rank(session.get('username', ''))
    games = user_row[3] if user_row else 0
    score = user_row[2] if user_row else 0
    bstats = get_battle_stats(session['user_id'])

    # Auto-unlock stat-based achievements
    to_check = [
        ('first_game', games >= 1),
        ('games5',     games >= 5),
        ('games10',    games >= 10),
        ('score500',   score >= 500),
        ('bot_win',    bstats['wins'] >= 1),
        ('battle_win', bstats['wins'] >= 1),
    ]
    for ach_id, condition in to_check:
        if condition and ach_id not in unlocked:
            unlock_achievement(session['user_id'], ach_id)
            unlocked.append(ach_id)

    return render_template('achievements.html',
                           achievements=ACHIEVEMENTS, unlocked=unlocked,
                           username=session.get('username',''),
                           emoji=session.get('emoji','🎮'))

if __name__ == '__main__':
    init_db()
    print("🚀 Starting Quiz Battle Game...")
    print("📍 Open http://localhost:5000 in your browser")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
