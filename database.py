import sqlite3, random
from datetime import date

DB = 'quiz.db'

def _conn(): return sqlite3.connect(DB)

def init_db():
    conn = _conn(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,
        emoji TEXT DEFAULT "x", total_score INTEGER DEFAULT 0,
        games_played INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT NOT NULL,
        option1 TEXT NOT NULL, option2 TEXT NOT NULL,
        option3 TEXT NOT NULL, option4 TEXT NOT NULL,
        correct_answer INTEGER NOT NULL, difficulty TEXT DEFAULT "medium",
        category TEXT DEFAULT "general", hint TEXT DEFAULT "")''')
    c.execute('''CREATE TABLE IF NOT EXISTS game_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        score INTEGER NOT NULL, total_questions INTEGER NOT NULL,
        correct_count INTEGER DEFAULT 0, game_mode TEXT DEFAULT "single",
        category TEXT DEFAULT "mixed", date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id))''')
    for sql in ["ALTER TABLE users ADD COLUMN emoji TEXT DEFAULT 'x'",
                "ALTER TABLE questions ADD COLUMN hint TEXT DEFAULT ''",
                "ALTER TABLE game_results ADD COLUMN correct_count INTEGER DEFAULT 0",
                "ALTER TABLE game_results ADD COLUMN category TEXT DEFAULT 'mixed'",
                "ALTER TABLE game_results ADD COLUMN won INTEGER DEFAULT NULL"]:
        try: c.execute(sql)
        except: pass
    # Question flags table
    c.execute('''CREATE TABLE IF NOT EXISTS question_flags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        reason TEXT DEFAULT 'incorrect',
        resolved INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(question_id, user_id),
        FOREIGN KEY (question_id) REFERENCES questions(id),
        FOREIGN KEY (user_id) REFERENCES users(id))''')
    # Only seed questions if the table is empty — never wipe admin-added questions
    c.execute('SELECT COUNT(*) FROM questions')
    if c.fetchone()[0] > 0:
        conn.commit(); conn.close()
        conn2 = _conn(); c2 = conn2.cursor()
        c2.execute('SELECT category, COUNT(*) FROM questions GROUP BY category')
        rows = c2.fetchall(); conn2.close()
        total = sum(r[1] for r in rows)
        print(f"Database ready: {total} questions (existing)")
        for r in rows: print(f"  {r[0]:12s} -> {r[1]}")
        return
    Q = [
        # GENERAL (50)
        ("Which planet is the Red Planet?","Venus","Mars","Jupiter","Saturn",2,"easy","general","4th from Sun"),
        ("Capital of France?","London","Berlin","Paris","Madrid",3,"easy","general","Eiffel Tower city"),
        ("Who painted Mona Lisa?","Van Gogh","Picasso","Da Vinci","Rembrandt",3,"easy","general","Italian genius"),
        ("Largest ocean on Earth?","Atlantic","Indian","Arctic","Pacific",4,"easy","general","Covers 30% of Earth"),
        ("Who wrote Romeo and Juliet?","Dickens","Shakespeare","Austen","Hemingway",2,"easy","general","Bard of Avon"),
        ("Speed of light?","300,000 km/s","150,000 km/s","450,000 km/s","600,000 km/s",1,"hard","general","Nothing faster"),
        ("World War II ended in?","1943","1944","1945","1946",3,"medium","general","Japan surrendered"),
        ("Smallest prime number?","0","1","2","3",3,"easy","general","Even and prime"),
        ("Symbol Au is for?","Silver","Gold","Copper","Iron",2,"medium","general","Latin: Aurum"),
        ("Theory of relativity by?","Newton","Einstein","Hawking","Curie",2,"hard","general","E=mc2"),
        ("Capital of Japan?","Seoul","Beijing","Tokyo","Bangkok",3,"easy","general","Rising Sun capital"),
        ("Longest river in world?","Amazon","Nile","Yangtze","Mississippi",2,"medium","general","Flows through Africa"),
        ("Chemical formula of water?","H2O","CO2","O2","H2O2",1,"easy","general","2 hydrogen 1 oxygen"),
        ("Kangaroo's home country?","New Zealand","Australia","South Africa","Brazil",2,"easy","general","Down Under"),
        ("Who painted Starry Night?","Monet","Van Gogh","Picasso","Dali",2,"medium","general","Dutch painter"),
        ("15 multiplied by 8?","120","125","115","130",1,"easy","general","Simple multiplication"),
        ("2 to the power of 10?","512","1024","2048","256",2,"medium","general","Binary 10000000000"),
        ("Gas plants absorb?","Oxygen","Nitrogen","Carbon Dioxide","Hydrogen",3,"easy","general","Photosynthesis"),
        ("Bones in adult human body?","196","206","216","226",2,"medium","general","206 bones"),
        ("Capital of Australia?","Sydney","Melbourne","Canberra","Brisbane",3,"medium","general","Not Sydney!"),
        ("Largest continent?","Africa","North America","Europe","Asia",4,"easy","general","44 million km2"),
        ("Who invented telephone?","Thomas Edison","Alexander Graham Bell","Nikola Tesla","James Watt",2,"medium","general","Patented 1876"),
        ("Currency of Japan?","Yuan","Won","Yen","Ringgit",3,"easy","general","Symbol yen"),
        ("Tallest mountain?","K2","Kangchenjunga","Mount Everest","Lhotse",3,"easy","general","In Himalayas"),
        ("Sides of a hexagon?","5","6","7","8",2,"easy","general","Hex means 6"),
        ("Powerhouse of the cell?","Nucleus","Ribosome","Mitochondria","Golgi Body",3,"medium","general","Produces ATP"),
        ("Boiling point of water?","90C","95C","100C","105C",3,"easy","general","At sea level"),
        ("Who wrote Harry Potter?","J.R.R. Tolkien","J.K. Rowling","C.S. Lewis","Roald Dahl",2,"easy","general","British author"),
        ("Planet closest to Sun?","Venus","Earth","Mercury","Mars",3,"easy","general","Smallest planet"),
        ("Square root of 144?","10","11","12","13",3,"easy","general","12 x 12"),
        ("Country with most lakes?","Russia","USA","Brazil","Canada",4,"hard","general","Northern America"),
        ("Hardest natural substance?","Gold","Iron","Diamond","Quartz",3,"easy","general","Carbon crystal"),
        ("Number of continents?","5","6","7","8",3,"easy","general","Africa Asia Europe..."),
        ("Organ that pumps blood?","Lungs","Liver","Heart","Kidney",3,"easy","general","100000 beats/day"),
        ("Largest planet?","Saturn","Neptune","Jupiter","Uranus",3,"easy","general","Great Red Spot"),
        ("Who invented light bulb?","Nikola Tesla","Thomas Edison","Alexander Bell","James Watt",2,"medium","general","Menlo Park"),
        ("Language of Brazil?","Spanish","French","Portuguese","English",3,"medium","general","South America"),
        ("Players in cricket team?","9","10","11","12",3,"easy","general","Same as football"),
        ("Full form of DNA?","Deoxyribonucleic Acid","Deoxyribose Nucleic Acid","Deoxyribonuclear Acid","Deoxyribose Nuclear Acid",1,"medium","general","Genetic info"),
        ("Smallest country?","Monaco","San Marino","Vatican City","Liechtenstein",3,"medium","general","Inside Rome"),
        ("Currency of UK?","Euro","Dollar","Pound Sterling","Franc",3,"easy","general","Symbol pound"),
        ("Adult human teeth?","28","30","32","34",3,"medium","general","With wisdom teeth"),
        ("Most abundant gas in air?","Oxygen","Carbon Dioxide","Nitrogen","Argon",3,"easy","general","About 78 percent"),
        ("Capital of Germany?","Munich","Hamburg","Frankfurt","Berlin",4,"easy","general","Reunified 1990"),
        ("Who wrote Hamlet?","Marlowe","Shakespeare","Jonson","Dryden",2,"medium","general","Prince of Denmark"),
        ("Largest desert?","Sahara","Arabian","Gobi","Antarctic",4,"hard","general","Cold desert"),
        ("Universal blood donor?","A","B","AB","O",4,"medium","general","Donates to all"),
        ("Strings on guitar?","4","5","6","7",3,"easy","general","EADGBE"),
        ("Capital of Canada?","Toronto","Vancouver","Ottawa","Montreal",3,"medium","general","Not Toronto"),
        ("Planet with most moons?","Jupiter","Saturn","Uranus","Neptune",2,"hard","general","Over 140 moons"),
        # INDIA (50)
        ("Father of Indian Constitution?","Mahatma Gandhi","B.R. Ambedkar","Jawaharlal Nehru","Sardar Patel",2,"easy","india","Architect of Constitution"),
        ("India independence year?","1945","1946","1947","1948",3,"easy","india","August 15th"),
        ("First PM of India?","Sardar Patel","B.R. Ambedkar","Jawaharlal Nehru","Lal Bahadur Shastri",3,"easy","india","Pandit ji"),
        ("First President of India?","Dr. Rajendra Prasad","Dr. S. Radhakrishnan","Jawaharlal Nehru","Sardar Patel",1,"easy","india","From Bihar"),
        ("National animal of India?","Lion","Elephant","Bengal Tiger","Leopard",3,"easy","india","Project Tiger"),
        ("National bird of India?","Sparrow","Peacock","Parrot","Eagle",2,"easy","india","Colorful feathers"),
        ("National flower of India?","Rose","Sunflower","Lotus","Jasmine",3,"easy","india","Grows in water"),
        ("Longest river in India?","Yamuna","Godavari","Ganga","Brahmaputra",3,"easy","india","Sacred river"),
        ("Capital of India?","Mumbai","Kolkata","New Delhi","Chennai",3,"easy","india","NCT"),
        ("States in India?","27","28","29","30",2,"medium","india","After 2019"),
        ("Largest state by area?","Maharashtra","Uttar Pradesh","Madhya Pradesh","Rajasthan",4,"medium","india","Desert state"),
        ("Minimum voting age?","16 years","18 years","21 years","25 years",2,"easy","india","Since 1989"),
        ("Highest civilian award?","Padma Vibhushan","Bharat Ratna","Padma Bhushan","Padma Shri",2,"easy","india","Jewel of India"),
        ("Father of the Nation?","Jawaharlal Nehru","Sardar Patel","Mahatma Gandhi","B.R. Ambedkar",3,"easy","india","Bapu"),
        ("Taj Mahal city?","Delhi","Jaipur","Agra","Lucknow",3,"easy","india","On Yamuna river"),
        ("Highest literacy state?","Tamil Nadu","Maharashtra","Kerala","Goa",3,"medium","india","Gods Own Country"),
        ("National sport of India?","Cricket","Football","Hockey","Kabaddi",3,"medium","india","Field sport"),
        ("First woman PM?","Sonia Gandhi","Indira Gandhi","Pratibha Patil","Sarojini Naidu",2,"medium","india","Iron Lady"),
        ("Article abolishing untouchability?","Article 14","Article 15","Article 17","Article 19",3,"medium","india","Fundamental Right"),
        ("Term of Lok Sabha?","4 years","5 years","6 years","7 years",2,"easy","india","Lower house"),
        ("Who built Red Fort?","Akbar","Humayun","Shah Jahan","Aurangzeb",3,"medium","india","Mughal emperor"),
        ("Missile Man of India?","C.V. Raman","Homi Bhabha","A.P.J. Abdul Kalam","Vikram Sarabhai",3,"easy","india","11th President"),
        ("Currency of India?","Taka","Rupee","Paisa","Anna",2,"easy","india","Symbol rupee"),
        ("Smallest state by area?","Sikkim","Tripura","Goa","Manipur",3,"medium","india","Beach state"),
        ("Constitution adopted in?","1947","1948","1949","1950",3,"medium","india","Jan 26 effect"),
        ("Who appoints Chief Justice?","Prime Minister","President","Parliament","Law Minister",2,"medium","india","Head of state"),
        ("Silicon Valley of India?","Mumbai","Hyderabad","Bengaluru","Pune",3,"easy","india","IT hub"),
        ("Full form of ISRO?","Indian Space Research Organisation","Indian Science Research Organisation","International Space Research Organisation","Indian Satellite Research Organisation",1,"easy","india","Chandrayaan"),
        ("Land of Five Rivers?","Haryana","Rajasthan","Punjab","Himachal Pradesh",3,"easy","india","Panj means five"),
        ("Largest High Court?","Bombay High Court","Delhi High Court","Allahabad High Court","Madras High Court",3,"hard","india","In Uttar Pradesh"),
        ("First Indian in space?","Kalpana Chawla","Rakesh Sharma","Sunita Williams","Ravish Malhotra",2,"medium","india","1984 Soyuz"),
        ("Pink City of India?","Jaipur","Jodhpur","Udaipur","Jaisalmer",1,"easy","india","Rajasthan capital"),
        ("National tree of India?","Neem","Peepal","Banyan","Mango",3,"easy","india","Ficus benghalensis"),
        ("Sorrow of Bihar?","Ganga","Yamuna","Kosi","Son",3,"medium","india","Floods often"),
        ("Founded Indian National Congress?","Mahatma Gandhi","A.O. Hume","Bal Gangadhar Tilak","Gopal Krishna Gokhale",2,"medium","india","British civil servant"),
        ("Largest dam in India?","Bhakra Nangal","Hirakud","Tehri","Sardar Sarovar",3,"hard","india","On Bhagirathi"),
        ("Full form of RBI?","Reserve Bank of India","Regulated Bank of India","Regional Bank of India","Rural Bank of India",1,"easy","india","Central bank"),
        ("Longest coastline state?","Kerala","Tamil Nadu","Gujarat","Andhra Pradesh",3,"medium","india","Western India"),
        ("Who wrote national anthem?","Bankim Chandra Chatterjee","Rabindranath Tagore","Sarojini Naidu","Subramania Bharati",2,"easy","india","Nobel laureate"),
        ("Highest peak in India?","Nanda Devi","Kangchenjunga","K2","Mount Everest",2,"medium","india","In Sikkim"),
        ("Full form of IIT?","Indian Institute of Technology","Indian International Technology","Indian Institute of Training","Indian Integrated Technology",1,"easy","india","Premier tech college"),
        ("City of Joy?","Mumbai","Delhi","Kolkata","Chennai",3,"easy","india","West Bengal capital"),
        ("First woman President?","Indira Gandhi","Sonia Gandhi","Pratibha Patil","Sarojini Naidu",3,"medium","india","2007-2012"),
        ("Largest tea producer?","Kerala","Assam","West Bengal","Tamil Nadu",2,"medium","india","Northeast India"),
        ("Full form of CBI?","Central Bureau of Investigation","Central Board of Investigation","Central Bureau of Intelligence","Central Board of Intelligence",1,"easy","india","Investigative agency"),
        ("Gateway of India is in?","Delhi","Mumbai","Kolkata","Chennai",2,"easy","india","Built 1924"),
        ("Union Territories in India?","7","8","9","10",2,"medium","india","After 2019"),
        ("Gods Own Country?","Goa","Kerala","Karnataka","Tamil Nadu",2,"easy","india","Backwaters"),
        ("Jai Hind slogan by?","Mahatma Gandhi","Subhas Chandra Bose","Jawaharlal Nehru","Bhagat Singh",2,"medium","india","Netaji"),
        ("Oldest mountain range?","Himalayas","Aravalli","Vindhya","Western Ghats",2,"hard","india","In Rajasthan"),
        # COMPUTER (80)
        ("CPU stands for?","Central Processing Unit","Computer Personal Unit","Central Program Utility","Computer Processing Utility",1,"easy","computer","Brain of computer"),
        ("RAM stands for?","Random Access Memory","Read Access Memory","Rapid Access Memory","Run Access Memory",1,"easy","computer","Temporary storage"),
        ("ROM stands for?","Read Only Memory","Random Only Memory","Run Only Memory","Read Output Memory",1,"easy","computer","Permanent storage"),
        ("Bits in 1 byte?","4","8","16","32",2,"easy","computer","8 bits = 1 byte"),
        ("USB stands for?","Universal Serial Bus","Universal System Bus","Unified Serial Bus","Universal Serial Board",1,"easy","computer","Common connector"),
        ("LAN stands for?","Local Area Network","Large Area Network","Long Area Network","Linked Area Network",1,"easy","computer","Home network"),
        ("WAN stands for?","Wide Area Network","Wireless Area Network","Web Area Network","Wired Area Network",1,"easy","computer","Internet is WAN"),
        ("GPS stands for?","Global Positioning System","General Positioning System","Global Pointing System","General Pointing System",1,"easy","computer","Uses satellites"),
        ("OS stands for?","Operating System","Output System","Open System","Optical System",1,"easy","computer","Windows Linux macOS"),
        ("VPN stands for?","Virtual Private Network","Virtual Public Network","Verified Private Network","Virtual Personal Network",1,"medium","computer","Hides your IP"),
        ("PDF stands for?","Portable Document Format","Printed Document Format","Personal Document Format","Public Document Format",1,"easy","computer","Adobe created it"),
        ("GUI stands for?","Graphical User Interface","General User Interface","Graphical Utility Interface","General Utility Interface",1,"medium","computer","Windows and icons"),
        ("IP stands for?","Internet Protocol","Internal Protocol","Internet Process","Internal Process",1,"easy","computer","Your online address"),
        ("DNS stands for?","Domain Name System","Digital Network System","Domain Network Service","Digital Name Service",1,"medium","computer","URL to IP"),
        ("SSD stands for?","Solid State Drive","Super Speed Drive","Static Storage Device","Solid Speed Disk",1,"easy","computer","Faster than HDD"),
        ("HDD stands for?","Hard Disk Drive","High Definition Drive","Hard Data Drive","High Density Disk",1,"easy","computer","Magnetic storage"),
        ("BIOS stands for?","Basic Input Output System","Binary Input Output System","Basic Internal Operating System","Binary Internal Output System",1,"hard","computer","First boot program"),
        ("API stands for?","Application Programming Interface","Automated Program Interface","Application Process Interface","Automated Programming Input",1,"medium","computer","Apps communicate"),
        ("SQL stands for?","Structured Query Language","Simple Query Language","Standard Query Language","Sequential Query Language",1,"medium","computer","Database language"),
        ("IoT stands for?","Internet of Things","Integration of Technology","Interface of Things","Internet of Technology",1,"medium","computer","Smart devices"),
        ("HTML stands for?","Hyper Text Markup Language","High Tech Modern Language","Home Tool Markup Language","Hyperlinks and Text Markup Language",1,"easy","computer","Web structure"),
        ("HTTP stands for?","HyperText Transfer Protocol","High Transfer Text Protocol","HyperText Transmission Protocol","High Text Transfer Protocol",1,"medium","computer","Web communication"),
        ("HTTPS stands for?","HyperText Transfer Protocol Secure","High Transfer Text Protocol Secure","HyperText Transmission Protocol Safe","High Text Transfer Protocol Safe",1,"medium","computer","Secure web"),
        ("URL stands for?","Uniform Resource Locator","Universal Resource Locator","Uniform Retrieval Locator","Universal Retrieval Locator",1,"medium","computer","Web address"),
        ("Wi-Fi stands for?","Wireless Fidelity","Wireless Frequency","Wide Fidelity","Wireless Fiber",1,"medium","computer","Wireless internet"),
        ("Who invented WWW?","Bill Gates","Tim Berners-Lee","Vint Cerf","Steve Jobs",2,"medium","computer","CERN scientist"),
        ("YouTube owned by?","Facebook","Google","Microsoft","Amazon",2,"easy","computer","Bought 2006"),
        ("Top search engine?","Bing","Yahoo","Google","DuckDuckGo",3,"easy","computer","90 percent share"),
        ("CSS stands for?","Cascading Style Sheets","Computer Style Sheets","Creative Style System","Cascading System Sheets",1,"easy","computer","Web styling"),
        ("FTP stands for?","File Transfer Protocol","Fast Transfer Protocol","File Transmission Process","Fast Transmission Protocol",1,"medium","computer","Transfer files"),
        ("Language for AI/ML?","Java","Python","C++","Ruby",2,"easy","computer","Snake language"),
        ("Language for Android?","Swift","Kotlin","Ruby","PHP",2,"medium","computer","Google preferred"),
        ("Language for iOS?","Kotlin","Java","Swift","Python",3,"medium","computer","Apple language"),
        ("First high-level language?","COBOL","FORTRAN","BASIC","Pascal",2,"hard","computer","1957 IBM"),
        ("Who developed Java?","Microsoft","Apple","Sun Microsystems","IBM",3,"medium","computer","Write once run anywhere"),
        ("Binary of decimal 10?","1010","1100","1001","1111",1,"hard","computer","8+2=10"),
        ("Binary of decimal 5?","0100","0101","0110","0111",2,"hard","computer","4+1=5"),
        ("Binary of decimal 8?","0111","1000","1001","1010",2,"hard","computer","2 to power 3"),
        ("Which is NOT a language?","Python","Java","HTML","C++",3,"medium","computer","Markup not programming"),
        ("Python comment symbol?","//","#","/*","--",2,"easy","computer","Hash symbol"),
        ("LIFO data structure?","Queue","Array","Stack","Linked List",3,"medium","computer","Last In First Out"),
        ("FIFO data structure?","Stack","Queue","Tree","Graph",2,"medium","computer","First In First Out"),
        ("OOP stands for?","Object Oriented Programming","Open Oriented Programming","Object Output Programming","Open Output Programming",1,"easy","computer","Classes and objects"),
        ("Language for web styling?","HTML","JavaScript","CSS","PHP",3,"easy","computer","Colors and fonts"),
        ("Language for interactivity?","HTML","CSS","JavaScript","XML",3,"easy","computer","Runs in browser"),
        ("Python file extension?",".pt",".py",".pyt",".python",2,"easy","computer","Short for Python"),
        ("Java file extension?",".jv",".jav",".java",".j",3,"easy","computer","Compile to class"),
        ("Python function keyword?","function","def","func","define",2,"easy","computer","def my_func():"),
        ("int means in programming?","Integer","Internal","Interface","Interrupt",1,"easy","computer","Whole number"),
        ("Python web framework?","Django","Laravel","Spring","Rails",1,"medium","computer","MTV pattern"),
        ("Father of computers?","Bill Gates","Steve Jobs","Charles Babbage","Alan Turing",3,"medium","computer","19th century"),
        ("Who developed Windows?","Apple","Microsoft","IBM","Google",2,"easy","computer","Bill Gates"),
        ("Who founded Apple?","Bill Gates","Steve Jobs","Mark Zuckerberg","Elon Musk",2,"medium","computer","Think Different"),
        ("Who founded Microsoft?","Steve Jobs","Bill Gates and Paul Allen","Mark Zuckerberg","Larry Page",2,"easy","computer","1975"),
        ("AI stands for?","Artificial Intelligence","Automated Intelligence","Advanced Intelligence","Artificial Information",1,"easy","computer","Machine thinking"),
        ("Fastest computer memory?","Hard Disk","RAM","Cache Memory","ROM",3,"hard","computer","L1 L2 L3 cache"),
        ("Brain of computer?","RAM","Hard Disk","CPU","Motherboard",3,"easy","computer","Processes all"),
        ("Function of compiler?","Runs program directly","Converts source code to machine code","Stores data","Manages memory",2,"medium","computer","gcc javac"),
        ("Cloud computing means?","Weather computing","Storing data over internet","Multiple monitors","Local computing",2,"medium","computer","AWS Azure GCP"),
        ("Who makes iPhone?","Samsung","Google","Apple","Sony",3,"easy","computer","Cupertino"),
        ("DVD stands for?","Digital Versatile Disc","Digital Video Disc","Data Versatile Disc","Digital Variable Disc",1,"easy","computer","Optical disc"),
        ("Firewall is used for?","Speed up internet","Block unauthorized access","Store passwords","Compress files",2,"medium","computer","Network security"),
        ("Phishing means?","A type of virus","Tricking users for info","A hacking tool","A network protocol",2,"medium","computer","Fake emails"),
        ("Malware means?","Malicious software","Mail software","Management software","Mobile software",1,"easy","computer","Harmful programs"),
        ("Encryption means?","Deleting data","Converting data to coded format","Copying data","Compressing data",2,"medium","computer","AES RSA"),
        ("Open source means?","Paid software","Publicly available source code","Business only","No updates",2,"easy","computer","Linux Python"),
        ("Android developed by?","Apple","Microsoft","Google","Samsung",3,"easy","computer","Mountain View"),
        ("GitHub is for?","Video editing","Version control and code hosting","Email","Cloud storage",2,"medium","computer","Git repository"),
        ("Debugging means?","Writing code","Finding and fixing errors","Deleting code","Running program",2,"easy","computer","Fix the bugs"),
        ("Algorithm is?","A virus","Step-by-step problem solution","A language","Hardware",2,"easy","computer","Recipe for solving"),
        ("NoSQL database?","MySQL","PostgreSQL","MongoDB","SQLite",3,"hard","computer","Document based"),
        ("Localhost refers to?","Remote server","Your own computer as server","Cloud service","Router",2,"medium","computer","127.0.0.1"),
        ("Default HTTP port?","21","443","80","8080",3,"medium","computer","Port 80"),
        ("Default HTTPS port?","80","443","8080","21",2,"medium","computer","Port 443"),
        ("Version control system?","Docker","Git","Linux","Apache",2,"medium","computer","Linus Torvalds"),
        ("RAM when power off?","Saves data","Loses all data","Transfers to ROM","Backs up",2,"medium","computer","Volatile memory"),
        ("JPEG stands for?","Joint Photographic Experts Group","Joint Photo Editing Group","Joint Picture Encoding Group","Joint Photographic Encoding Group",1,"medium","computer","Image format"),
        ("Language for DB queries?","Python","Java","SQL","C++",3,"easy","computer","SELECT FROM table"),
        ("Bandwidth refers to?","Processor speed","Data transferred per second","Disk size","Programs running",2,"medium","computer","Mbps Gbps"),
        ("Browser cookie is?","A virus","Small data stored by websites","A web element","A cache type",2,"medium","computer","Session info"),
        ("PNG stands for?","Portable Network Graphics","Picture Network Graphics","Portable New Graphics","Picture New Graphics",1,"easy","computer","Lossless image"),
    ]
    c.executemany('INSERT INTO questions (question,option1,option2,option3,option4,correct_answer,difficulty,category,hint) VALUES (?,?,?,?,?,?,?,?,?)', Q)
    conn.commit(); conn.close()
    conn2 = _conn(); c2 = conn2.cursor()
    c2.execute('SELECT category, COUNT(*) FROM questions GROUP BY category')
    rows = c2.fetchall(); conn2.close()
    total = sum(r[1] for r in rows)
    print(f"Database ready: {total} questions")
    for r in rows: print(f"  {r[0]:12s} -> {r[1]}")


def get_user(name, emoji='x'):
    conn = _conn(); c = conn.cursor()
    c.execute('SELECT * FROM users WHERE name=?', (name,))
    u = c.fetchone()
    if not u:
        c.execute('INSERT INTO users (name,emoji) VALUES (?,?)', (name, emoji))
        conn.commit(); uid = c.lastrowid; u = (uid, name, emoji, 0, 0)
    else:
        c.execute('UPDATE users SET emoji=? WHERE id=?', (emoji, u[0]))
        conn.commit()
        u = (u[0], u[1], emoji, u[3] if len(u)>3 else 0, u[4] if len(u)>4 else 0)
    conn.close(); return u


def get_questions(limit=10, difficulty=None, category=None, exclude_ids=None):
    conn = _conn(); c = conn.cursor()
    excl, ep = '', []
    if exclude_ids:
        ph = ','.join('?'*len(exclude_ids)); excl = f'AND id NOT IN ({ph})'; ep = list(exclude_ids)
    if difficulty and category:
        c.execute(f'SELECT * FROM questions WHERE difficulty=? AND category=? {excl} ORDER BY RANDOM() LIMIT ?', [difficulty,category]+ep+[limit])
    elif difficulty:
        c.execute(f'SELECT * FROM questions WHERE difficulty=? {excl} ORDER BY RANDOM() LIMIT ?', [difficulty]+ep+[limit])
    elif category:
        c.execute(f'SELECT * FROM questions WHERE category=? {excl} ORDER BY RANDOM() LIMIT ?', [category]+ep+[limit])
    else:
        c.execute(f'SELECT * FROM questions WHERE 1=1 {excl} ORDER BY RANDOM() LIMIT ?', ep+[limit])
    q = c.fetchall(); conn.close(); return q


def save_game_result(user_id, score, total_questions, game_mode='single', correct_count=0, category='mixed', won=None):
    conn = _conn(); c = conn.cursor()
    c.execute('INSERT INTO game_results (user_id,score,total_questions,game_mode,correct_count,category,won) VALUES (?,?,?,?,?,?,?)',
              (user_id, score, total_questions, game_mode, correct_count, category,
               1 if won is True else (0 if won is False else None)))
    c.execute('UPDATE users SET total_score=total_score+?, games_played=games_played+1 WHERE id=?', (score, user_id))
    conn.commit(); conn.close()


def get_leaderboard(limit=20):
    conn = _conn(); c = conn.cursor()
    c.execute('''SELECT name,emoji,total_score,games_played,
                 ROUND(CAST(total_score AS FLOAT)/games_played,1)
                 FROM users WHERE games_played>0 ORDER BY total_score DESC LIMIT ?''', (limit,))
    r = c.fetchall(); conn.close(); return r


def get_user_rank(username):
    conn = _conn(); c = conn.cursor()
    c.execute('SELECT COUNT(*)+1 FROM users WHERE total_score>(SELECT total_score FROM users WHERE name=?) AND games_played>0', (username,))
    rank = c.fetchone()[0]
    c.execute('SELECT name,emoji,total_score,games_played FROM users WHERE name=?', (username,))
    u = c.fetchone(); conn.close(); return rank, u


def get_game_history(user_id, limit=20):
    conn = _conn(); c = conn.cursor()
    c.execute('SELECT score,total_questions,correct_count,game_mode,category,date FROM game_results WHERE user_id=? ORDER BY date DESC LIMIT ?', (user_id, limit))
    r = c.fetchall(); conn.close(); return r


def get_category_stats(user_id):
    conn = _conn(); c = conn.cursor()
    c.execute('''SELECT category, COUNT(*), ROUND(AVG(CAST(correct_count AS FLOAT)/total_questions*100),1), SUM(score)
                 FROM game_results WHERE user_id=? AND total_questions>0 GROUP BY category''', (user_id,))
    r = c.fetchall(); conn.close(); return r


def get_weekly_leaderboard(limit=20):
    conn = _conn(); c = conn.cursor()
    week_ago = (date.today() - __import__('datetime').timedelta(days=7)).isoformat()
    c.execute('''SELECT u.name, u.emoji,
                 SUM(g.score) as weekly_score,
                 COUNT(g.id) as games
                 FROM game_results g
                 JOIN users u ON u.id = g.user_id
                 WHERE g.date >= ?
                 GROUP BY g.user_id
                 ORDER BY weekly_score DESC LIMIT ?''', (week_ago, limit))
    r = c.fetchall(); conn.close(); return r


def get_battle_stats(user_id):
    conn = _conn(); c = conn.cursor()
    c.execute('''SELECT
                 SUM(CASE WHEN won=1 THEN 1 ELSE 0 END),
                 SUM(CASE WHEN won=0 THEN 1 ELSE 0 END)
                 FROM game_results
                 WHERE user_id=? AND game_mode IN ('battle','bot_battle')''', (user_id,))
    row = c.fetchone(); conn.close()
    return {'wins': row[0] or 0, 'losses': row[1] or 0}


def flag_question(question_id, user_id, reason='incorrect'):
    conn = _conn(); c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO question_flags (question_id, user_id, reason)
                 VALUES (?,?,?)''', (question_id, user_id, reason))
    conn.commit(); conn.close()


def get_flagged_questions():
    conn = _conn(); c = conn.cursor()
    c.execute('''SELECT f.id, f.question_id, q.question, f.reason, u.name, f.created_at
                 FROM question_flags f
                 JOIN questions q ON q.id = f.question_id
                 JOIN users u ON u.id = f.user_id
                 WHERE f.resolved = 0
                 ORDER BY f.created_at DESC''')
    r = c.fetchall(); conn.close(); return r


def update_question(qid, data):
    conn = _conn(); c = conn.cursor()
    c.execute('''UPDATE questions SET
                 question=?, option1=?, option2=?, option3=?, option4=?,
                 correct_answer=?, difficulty=?, category=?, hint=?
                 WHERE id=?''',
              (data['question'], data['option1'], data['option2'],
               data['option3'], data['option4'], int(data['correct_answer']),
               data['difficulty'], data['category'], data.get('hint',''), qid))
    conn.commit(); conn.close()


# ─────────────────────────────────────────────
#  Daily challenge persistence
# ─────────────────────────────────────────────

def get_daily_completion(user_id, today):
    """Returns True if user already completed today's daily challenge."""
    conn = _conn(); c = conn.cursor()
    c.execute('''SELECT 1 FROM game_results
                 WHERE user_id=? AND game_mode='daily'
                 AND date(date)=?''', (user_id, today))
    row = c.fetchone(); conn.close()
    return row is not None

def mark_daily_done(user_id, today):
    """No-op — save_game_result already inserts the row; this is kept for clarity."""
    pass


# ─────────────────────────────────────────────
#  Achievements persistence
# ─────────────────────────────────────────────

def _ensure_achievements_table(c):
    c.execute('''CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        achievement_id TEXT NOT NULL,
        unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, achievement_id),
        FOREIGN KEY (user_id) REFERENCES users(id))''')

def get_achievements(user_id):
    conn = _conn(); c = conn.cursor()
    _ensure_achievements_table(c); conn.commit()
    c.execute('SELECT achievement_id FROM achievements WHERE user_id=?', (user_id,))
    rows = c.fetchall(); conn.close()
    return [r[0] for r in rows]

def unlock_achievement(user_id, achievement_id):
    conn = _conn(); c = conn.cursor()
    _ensure_achievements_table(c)
    c.execute('INSERT OR IGNORE INTO achievements (user_id, achievement_id) VALUES (?,?)',
              (user_id, achievement_id))
    conn.commit(); conn.close()


if __name__ == '__main__':
    init_db()
