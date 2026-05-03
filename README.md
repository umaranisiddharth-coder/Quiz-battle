# 🎮 Quiz Battle Game

A real-time multiplayer quiz game built with Flask and Socket.IO. Challenge yourself in single-player mode or compete against friends in battle mode!

## ✨ Features

### 🧠 Single Player Mode
- 10 questions per quiz
- 15-second timer per question
- Multiple difficulty levels (Easy, Medium, Hard, Mixed)
- **Lifelines:**
  - 💡 50-50: Remove 2 wrong answers
  - ⏭ Skip: Skip current question
- **Streak Bonus:** 3+ correct answers in a row = bonus notification
- **Time Bonus:** Faster answers = more points (up to +5 pts)
- Score tracking and statistics

### ⚔️ Battle Mode
- Real-time 2-player competition
- Same questions for both players
- Live score updates
- Room code system for easy joining
- Winner announcement

### 🏆 Leaderboard
- Top 10 players ranking
- Total score tracking
- Games played statistics
- Average score calculation

### 🎨 UI Features
- Beautiful gradient design
- Smooth animations
- Responsive layout
- Progress bar
- Category and difficulty badges
- Visual feedback for correct/incorrect answers

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or download this project**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Initialize the database:**
```bash
python database.py
```

4. **Run the application:**
```bash
python app.py
```

5. **Open your browser:**
```
http://localhost:5000
```

## 📁 Project Structure

```
quiz-battle/
├── app.py                 # Main Flask application
├── database.py            # Database setup and operations
├── requirements.txt       # Python dependencies
├── quiz.db               # SQLite database (auto-generated)
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── quiz.html         # Quiz game page
├── templates/
│   ├── index.html        # Home page
│   ├── leaderboard.html  # Leaderboard page
│   └── battle.html       # Battle mode page
└── README.md
```

## 🗄️ Database Schema

### Users Table
- `id`: Primary key
- `name`: Username (unique)
- `total_score`: Cumulative score
- `games_played`: Number of games
- `created_at`: Registration timestamp

### Questions Table
- `id`: Primary key
- `question`: Question text
- `option1-4`: Answer options
- `correct_answer`: Correct option number (1-4)
- `difficulty`: easy/medium/hard
- `category`: Question category

### Game Results Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `score`: Game score
- `total_questions`: Number of questions
- `game_mode`: single/battle
- `date`: Game timestamp

## 🎯 How to Play

### Single Player
1. Enter your username
2. Choose "Single Player" mode
3. Select difficulty level
4. Answer 10 questions within 15 seconds each
5. Use lifelines strategically
6. View your final score and stats

### Battle Mode
1. Enter your username
2. Choose "Battle Mode"
3. **Create Room:** Generate a room code and share with friend
4. **Join Room:** Enter the room code your friend shared
5. Both players answer the same questions
6. Fastest and most accurate wins!

## 🎓 Scoring System

- **Base Points:** 10 points per correct answer
- **Time Bonus:** Up to +5 points for faster answers
- **Streak Bonus:** Visual notification at 3+ streak
- **Lifelines:** Use strategically (one-time use per game)

## 🔧 Customization

### Add More Questions
Edit `database.py` and add questions to the `sample_questions` list:

```python
("Your question?", "Option A", "Option B", "Option C", "Option D", 
 correct_answer_number, "difficulty", "category")
```

Then reinitialize the database:
```bash
python database.py
```

### Change Timer Duration
In `static/quiz.html` and `templates/battle.html`, modify:
```javascript
timeLeft = 15;  // Change to desired seconds
```

### Adjust Points
In `app.py`, modify the scoring logic in `submit_quiz()`:
```python
points = 10 + time_bonuses.get(q_id_str, 0)  # Change base points
```

## 🎨 Tech Stack

- **Backend:** Flask (Python web framework)
- **Real-time:** Flask-SocketIO (WebSocket support)
- **Database:** SQLite (lightweight SQL database)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Design:** Custom CSS with gradients and animations

## 📝 Viva Questions & Answers

### Technical Questions

**Q: Why did you choose Flask?**
A: Flask is lightweight, easy to learn, and perfect for small to medium projects. It has excellent documentation and a large community.

**Q: How does real-time communication work?**
A: We use Flask-SocketIO which implements WebSocket protocol. It allows bidirectional communication between server and clients for live score updates.

**Q: Why SQLite instead of MySQL/PostgreSQL?**
A: SQLite is serverless, requires zero configuration, and is perfect for development and small-scale applications. The entire database is a single file.

**Q: How do you prevent cheating in battle mode?**
A: The correct answers are stored server-side only. Clients never receive the correct answer until after submission. Timer is enforced on both client and server.

**Q: How is the time bonus calculated?**
A: `time_bonus = (time_remaining / total_time) * max_bonus`. Faster answers get proportionally more bonus points.

### Feature Questions

**Q: What makes your project unique?**
A: Real-time battle mode, lifelines system, streak tracking, time-based scoring, and beautiful UI with smooth animations.

**Q: How would you scale this for 1000+ users?**
A: Use Redis for session management, PostgreSQL for database, deploy on cloud (AWS/Heroku), implement caching, and use load balancers.

**Q: What security measures did you implement?**
A: Session management, server-side answer validation, SQL injection prevention (parameterized queries), and input sanitization.

## 🚀 Future Enhancements

- [ ] AI-generated questions using OpenAI API
- [ ] Voice-based quiz mode
- [ ] Mobile app (React Native)
- [ ] Tournament mode (4+ players)
- [ ] Question categories filter
- [ ] User profiles with avatars
- [ ] Achievement badges
- [ ] Social sharing
- [ ] Admin panel for question management
- [ ] Analytics dashboard

## 📄 License

This project is open source and available for educational purposes.

## 👨‍💻 Author

Built as a college project demonstrating full-stack web development skills.

---

**Enjoy the game! 🎮**
