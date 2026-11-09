import streamlit as st
import streamlit.components.v1 as components
import sqlite3, re, hashlib, io, textwrap, os, json, uuid
from pathlib import Path
from datetime import datetime
from interview_bot import InterviewEngine, ClaudeLLM, BotUnavailable, DEFAULT_MODEL

APP_DIR = Path(__file__).parent
DB = APP_DIR / "interviewmate.db"

st.set_page_config(page_title="InterviewMate", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

# ---------------- THEME ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {
  --bg:#090d1d; --card:#11182d; --line:rgba(163,177,255,.16);
  --accent:#9a8cff; --accent2:#53e0c1; --text:#f5f6ff; --muted:#a6b0cc;
}
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:radial-gradient(ellipse at 5% 0%,rgba(91,75,190,.24),transparent 36%),radial-gradient(ellipse at 95% 10%,rgba(37,192,169,.12),transparent 28%),linear-gradient(145deg,#090d1d 0%,#0b1022 52%,#080d19 100%); color:var(--text); }
.block-container { padding-top:1.7rem; padding-bottom:3rem; max-width:1320px; }
[data-testid="stHeader"] { background:rgba(9,13,29,.78); }
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#0e1428 0%,#0a1020 100%); border-right:1px solid var(--line); }
section[data-testid="stSidebar"] > div { padding-top:1.3rem; }
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { font-family:'Manrope',sans-serif; letter-spacing:-.4px; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label { border-radius:12px; padding:5px 9px; transition:background .18s ease, transform .18s ease; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:rgba(154,140,255,.12); transform:translateX(2px); }
.hero { position:relative; overflow:hidden; padding:clamp(25px,4vw,42px); border:1px solid rgba(169,157,255,.24); border-radius:28px; background:linear-gradient(120deg,rgba(72,61,151,.48),rgba(17,28,54,.92) 58%,rgba(17,85,82,.38)); box-shadow:0 18px 55px rgba(0,0,0,.20); margin-bottom:24px; }
.hero:after { content:'✦'; position:absolute; right:6%; top:-38px; font-size:180px; line-height:1; color:rgba(255,255,255,.055); transform:rotate(12deg); pointer-events:none; }
.hero h1 { position:relative; z-index:1; font-family:'Manrope',sans-serif; font-size:clamp(30px,4vw,46px); line-height:1.12; font-weight:800; margin:12px 0 8px; letter-spacing:-1.7px; color:#fff; }
.hero p { position:relative; z-index:1; color:#c3cce6; font-size:16px; line-height:1.7; margin:8px 0 0; max-width:850px; }
.card { padding:21px; border:1px solid var(--line); border-radius:20px; background:linear-gradient(145deg,rgba(21,29,54,.92),rgba(14,22,42,.88)); box-shadow:0 10px 28px rgba(0,0,0,.12); margin-bottom:16px; transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease; }
.card:hover { transform:translateY(-2px); border-color:rgba(154,140,255,.38); box-shadow:0 16px 32px rgba(0,0,0,.2); }
.badge { display:inline-block; padding:6px 11px; border-radius:999px; background:rgba(154,140,255,.15); border:1px solid rgba(154,140,255,.22); color:#c9c0ff; font-size:11px; letter-spacing:.65px; text-transform:uppercase; font-weight:800; margin-right:6px; margin-bottom:4px; }
.small { color:var(--muted); font-size:13px; line-height:1.6; }
.feature-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:13px; margin:16px 0 24px; }
.feature-tile { min-height:130px; padding:19px; border:1px solid var(--line); border-radius:19px; background:linear-gradient(145deg,rgba(22,31,58,.92),rgba(13,21,40,.9)); transition:transform .18s ease,border-color .18s ease; }
.feature-tile:hover { transform:translateY(-3px); border-color:rgba(83,224,193,.48); }
.feature-icon { font-size:25px; margin-bottom:11px; }
.feature-title { color:#f7f7ff; font-weight:800; font-size:15px; margin-bottom:5px; }
.feature-desc { color:#a6b0cc; font-size:12px; line-height:1.5; }
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3 { font-family:'Manrope',sans-serif; letter-spacing:-.6px; }
.stMarkdown h2 { margin-top:1.3rem; }
.stButton > button { border-radius:13px; border:1px solid rgba(154,140,255,.30); font-weight:700; min-height:2.75rem; transition:transform .15s ease,box-shadow .15s ease,filter .15s ease; }
.stButton > button[kind="primary"] { background:linear-gradient(105deg,#8876ff,#6b62e8 55%,#3bcab2); color:#fff; border:0; box-shadow:0 8px 22px rgba(111,98,232,.22); }
.stButton > button:hover { transform:translateY(-1px); box-shadow:0 9px 20px rgba(0,0,0,.18); filter:brightness(1.08); }
.stTextInput input,.stTextArea textarea,.stNumberInput input,.stSelectbox [data-baseweb="select"],.stMultiSelect [data-baseweb="select"] { background:rgba(10,16,32,.86); border-color:rgba(163,177,255,.22); border-radius:12px; }
.stTextInput input:focus,.stTextArea textarea:focus { border-color:#9a8cff; box-shadow:0 0 0 1px #9a8cff; }
.stProgress > div > div > div > div { background:linear-gradient(90deg,#9a8cff,#53e0c1); border-radius:99px; }
[data-testid="stMetric"] { background:linear-gradient(145deg,rgba(25,34,64,.9),rgba(15,23,44,.9)); border:1px solid var(--line); padding:17px 19px; border-radius:18px; }
[data-testid="stMetricLabel"] { color:#aeb8d4; }
[data-testid="stMetricValue"] { font-family:'Manrope',sans-serif; font-weight:800; }
[data-testid="stExpander"] { border:1px solid var(--line); border-radius:14px; background:rgba(15,23,44,.55); }
[data-testid="stAlert"] { border-radius:14px; }
hr { border-color:var(--line); }
@media(max-width:900px) { .feature-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .hero:after { right:-15px; font-size:130px; } }
@media(max-width:520px) { .feature-grid { grid-template-columns:1fr; } .hero { padding:23px; border-radius:21px; } .block-container { padding-left: .8rem; padding-right: .8rem; } [data-testid="stHorizontalBlock"] { gap: .75rem; flex-wrap:wrap !important; } [data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width:100% !important; flex:1 1 100% !important; width:100% !important; } }

/* Accessibility contrast patch: keep labels, placeholders and validation text readable */
.stApp, .stApp p, .stApp span, .stApp label, .stApp small,
[data-testid="stWidgetLabel"], [data-testid="stMarkdownContainer"] p {
  color: #eef2ff;
}
.stApp label, [data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
  color: #cbd5f5 !important;
  font-weight: 600 !important;
}
.stTextInput input, .stTextArea textarea, .stNumberInput input {
  background: #f8faff !important;
  color: #172033 !important;
  -webkit-text-fill-color: #172033 !important;
  border: 1px solid #aab6d3 !important;
  caret-color: #4f46e5 !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder,
.stNumberInput input::placeholder {
  color: #667085 !important;
  -webkit-text-fill-color: #667085 !important;
  opacity: 1 !important;
}
.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
  border-color: #8b7cff !important;
  box-shadow: 0 0 0 2px rgba(139,124,255,.22) !important;
}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
  color: #b8c3df !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
def db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT UNIQUE,
        password_hash TEXT NOT NULL,
        name TEXT,
        created_at TEXT
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS profiles(
        user_id INTEGER PRIMARY KEY,
        name TEXT, target_role TEXT, company TEXT, resume_text TEXT, jd_text TEXT,
        readiness REAL DEFAULT 0, tailored_resume TEXT DEFAULT '', updated_at TEXT
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS progress(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, round_name TEXT, score REAL, created_at TEXT
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS interviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, session_id TEXT, kind TEXT, mode TEXT, status TEXT,
        overall REAL, reason TEXT, transcript TEXT, created_at TEXT
    )""")
    con.commit(); return con

def hash_pw(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def create_user(identifier, password, name):
    con=db()
    try:
        cur=con.execute("INSERT INTO users(identifier,password_hash,name,created_at) VALUES(?,?,?,?)",
                        (identifier.strip().lower(),hash_pw(password),name.strip(),datetime.now().isoformat(timespec="seconds")))
        uid=cur.lastrowid; con.commit(); return uid, None
    except sqlite3.IntegrityError:
        return None, "An account with this email/phone/username already exists."
    finally: con.close()

def login_user(identifier,password):
    con=db(); row=con.execute("SELECT id,name FROM users WHERE identifier=? AND password_hash=?",
                              (identifier.strip().lower(),hash_pw(password))).fetchone(); con.close(); return row

def get_profile(uid):
    con=db(); row=con.execute("SELECT name,target_role,company,resume_text,jd_text,readiness,tailored_resume FROM profiles WHERE user_id=?",(uid,)).fetchone(); con.close(); return row

def save_profile(uid,name,role,company,resume,jd,readiness=0,tailored=""):
    con=db(); con.execute("""INSERT OR REPLACE INTO profiles
        (user_id,name,target_role,company,resume_text,jd_text,readiness,tailored_resume,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?)""",(uid,name,role,company,resume,jd,readiness,tailored,datetime.now().isoformat(timespec="seconds"))); con.commit(); con.close()

def save_score(uid,round_name,score):
    con=db(); con.execute("INSERT INTO progress(user_id,round_name,score,created_at) VALUES(?,?,?,?)",(uid,round_name,score,datetime.now().isoformat(timespec="seconds"))); con.commit(); con.close()

def get_scores(uid):
    con=db(); rows=con.execute("SELECT round_name,score,created_at FROM progress WHERE user_id=? ORDER BY id DESC",(uid,)).fetchall(); con.close(); return rows

def save_interview(uid,session_id,kind,mode,status,overall,reason,transcript):
    con=db(); con.execute("INSERT INTO interviews(user_id,session_id,kind,mode,status,overall,reason,transcript,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
        (uid,session_id,kind,mode,status,overall,reason,transcript,datetime.now().isoformat(timespec="seconds"))); con.commit(); con.close()

def get_interviews(uid,limit=8):
    con=db(); rows=con.execute("SELECT created_at,kind,mode,status,overall,reason FROM interviews WHERE user_id=? ORDER BY id DESC LIMIT ?",(uid,limit)).fetchall(); con.close(); return rows

# ---------------- TEXT / VALIDATION ----------------
SKILLS=["python","java","c","c++","sql","mysql","postgresql","mongodb","html","css","javascript","react","node","flask","django","streamlit","machine learning","deep learning","nlp","tensorflow","pytorch","scikit-learn","pandas","numpy","git","github","aws","azure","docker","kubernetes","linux","data structures","dsa","oop","computer networks","operating systems","dbms","power bi","excel","generative ai","genai","llm","rest api","api","cloud computing","computer vision","natural language processing","data analysis","statistics","tableau","spring boot","fastapi"]
RESUME_MARKERS=["education","skills","project","experience","certification","objective","summary","internship","technical skills","career objective","curriculum vitae","work experience","academic"]
JD_MARKERS=["job description","responsibilities","requirements","qualifications","skills required","role","about the role","what you’ll do","what you'll do","eligibility","preferred skills","experience required","key responsibilities"]
BAD_MARKERS=["invoice","receipt","prescription","bank statement","restaurant menu","admit card","train ticket","marks memo","timetable","purchase order","quotation"]

def extract_text(uploaded):
    if not uploaded: return ""
    raw=uploaded.getvalue(); name=uploaded.name.lower()
    try:
        if name.endswith('.txt'): return raw.decode('utf-8',errors='ignore')
        if name.endswith('.pdf'):
            from pypdf import PdfReader
            reader=PdfReader(io.BytesIO(raw)); return "\n".join((p.extract_text() or "") for p in reader.pages)
        if name.endswith('.docx'):
            from docx import Document
            doc=Document(io.BytesIO(raw)); return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e: return ""
    return ""

def validate_document(text, kind):
    t=(text or "").lower()
    if len(re.sub(r"\s+","",t))<120: return False,"The file does not contain enough readable text."
    if any(x in t for x in BAD_MARKERS): return False,"This looks like an unrelated document, not a resume or job description."
    markers=RESUME_MARKERS if kind=='resume' else JD_MARKERS
    marker_hits=sum(1 for m in markers if m in t)
    skills=len(skill_hits(text))
    if kind=='resume': ok=marker_hits>=2 and (skills>=1 or 'education' in t or 'experience' in t)
    else: ok=marker_hits>=2 and (skills>=1 or 'responsibilities' in t or 'requirements' in t)
    if not ok: return False,f"The uploaded file could not be verified as a valid {kind}."
    return True,f"Valid {kind} detected."

def skill_hits(text):
    t=(text or '').lower(); found=[]
    for s in SKILLS:
        pattern=r'(?<![a-z0-9])'+re.escape(s.lower())+r'(?![a-z0-9])'
        if re.search(pattern,t): found.append(s)
    return sorted(set(found))

def jd_match(resume,jd):
    rs=set(skill_hits(resume)); js=set(skill_hits(jd)); matched=rs&js; missing=js-rs
    score=round(len(matched)/len(js)*100) if js else 0
    return score,sorted(matched),sorted(missing)

def readiness(resume,jd,diagnostic=None):
    match,_,missing=jd_match(resume,jd); resume_score=min(100,40+min(60,len(skill_hits(resume))*4)); diag=sum(diagnostic)/len(diagnostic) if diagnostic else 50
    return round(max(0,min(100,.45*match+.25*resume_score+.30*diag-min(25,len(missing)*4))))

# ---------------- RESUME TAILORING ENGINE ----------------
def clean_line(s): return re.sub(r'\s+',' ',s.strip())

def sections_from_resume(text):
    lines=[clean_line(x) for x in (text or '').splitlines() if clean_line(x)]
    sections={"header":[],"summary":[],"skills":[],"education":[],"experience":[],"projects":[],"certifications":[],"other":[]}
    current='header'
    headings={
        'summary':'summary','objective':'summary','profile':'summary','professional summary':'summary','career objective':'summary',
        'skills':'skills','technical skills':'skills','technical skill':'skills',
        'education':'education','academic':'education','academic qualifications':'education',
        'experience':'experience','work experience':'experience','internship':'experience',
        'projects':'projects','project':'projects','academic projects':'projects',
        'certifications':'certifications','certificates':'certifications','achievements':'certifications'
    }
    for line in lines:
        key=line.lower().strip(':- ')
        if key in headings: current=headings[key]; continue
        sections[current].append(line)
    return sections

def sentence_case_skill(s): return s.title() if s not in {'c','c++','sql','aws','api','dsa','llm','nlp'} else s.upper()

def tailor_resume(resume,jd,role,company):
    sec=sections_from_resume(resume)
    match,matched,missing=jd_match(resume,jd)
    original_skills=skill_hits(resume)
    # Never invent experience. Only re-order/rewrite content that exists and flag gaps separately.
    name=sec['header'][0] if sec['header'] else 'Candidate Name'
    contact=sec['header'][1:] if len(sec['header'])>1 else []
    summary=(f"Final-year B.Tech CSE (AI&ML) student targeting the {role} role at {company or 'the company'}. "
             f"Brings hands-on exposure to {', '.join(sentence_case_skill(s) for s in matched[:6]) or 'Python-based projects and technical fundamentals'}. "
             "Focused on building practical solutions, learning quickly, and contributing effectively in a team.")
    if sec['summary']:
        # Preserve factual content while putting role keywords first.
        existing=' '.join(sec['summary'])
        summary += " Existing profile: " + existing
    skill_order=matched + [s for s in original_skills if s not in matched]
    out=[]
    out.append(name)
    out.extend(contact)
    out.append('')
    out.append('PROFESSIONAL SUMMARY')
    out.append(summary)
    out.append('')
    out.append('TARGET ROLE')
    out.append(f"{role} | {company or 'Target Company'}")
    out.append('')
    out.append('TECHNICAL SKILLS')
    out.append(', '.join(sentence_case_skill(s) for s in skill_order) if skill_order else 'Use the skills already present in the original resume.')
    for title,key in [('PROJECTS','projects'),('EXPERIENCE','experience'),('EDUCATION','education'),('CERTIFICATIONS & ACHIEVEMENTS','certifications'),('ADDITIONAL INFORMATION','other')]:
        if sec[key]:
            out += ['',title]
            # Reorder bullet lines containing matched keywords first, but do not create unsupported facts.
            lines=sec[key]
            lines=sorted(lines,key=lambda x: (sum(1 for s in matched if s.lower() in x.lower()), len(x)),reverse=True)
            out.extend(lines)
    out += ['', '--- ATS TAILORING NOTES ---', f'Company: {company or "Not specified"}', f'Role: {role}', f'JD keyword match: {match}%']
    if matched: out.append('Matched JD skills: '+', '.join(matched))
    if missing: out.append('JD skills not found in the original resume: '+', '.join(missing))
    out.append('Important: Do not claim a missing skill unless you genuinely have it. Add it to the resume only after gaining/confirming that skill.')
    return '\n'.join(out), matched, missing, match

def resume_docx(text):
    from docx import Document
    from docx.shared import Pt
    doc=Document(); style=doc.styles['Normal']; style.font.name='Aptos'; style.font.size=Pt(10.5)
    for line in text.splitlines():
        if not line.strip(): doc.add_paragraph(''); continue
        if line.isupper() or line.startswith('---'):
            p=doc.add_paragraph(); r=p.add_run(line); r.bold=True; r.font.size=Pt(11.5)
        else: doc.add_paragraph(line)
    bio=io.BytesIO(); doc.save(bio); return bio.getvalue()

# ---------------- QUESTION BANK ----------------
QUESTION_BANK={
'Technical':[("Python","What is the difference between a list and a tuple in Python?","Explain with one practical example."),("Python","What is a dictionary in Python?","Mention average-case lookup."),("OOP","What are the four pillars of OOP?","Explain each briefly."),("DBMS","What is normalization in DBMS?","Why is it useful?"),("SQL","What is the difference between WHERE and HAVING?","Give an example."),("ML","What is overfitting in machine learning?","How can you reduce it?"),("ML","Classification vs regression?","Give one example of each."),("DSA","What is the time complexity of binary search?","What condition is required?"),("OS","Process vs thread?","Keep it interview-ready."),("Networks","HTTP vs HTTPS?","Why is HTTPS safer?")],
'HR':[("HR","Tell me about yourself.","Use Present → Past → Future."),("HR","Why should we hire you?","Connect strengths to the role."),("HR","What is your biggest weakness?","Mention improvement."),("HR","Where do you see yourself in five years?","Keep it realistic."),("HR","Tell me about a time you worked in a team.","Use STAR."),("HR","How do you handle pressure or deadlines?","Give a real example."),("HR","Why do you want this job?","Connect to target role.")],
'Project':[("Project","Explain your main project in 60 seconds.","Problem, solution, technology, result."),("Project","Why did you choose this technology?","Mention alternatives and reason."),("Project","Biggest project challenge?","Explain how you solved it."),("Project","What would you improve with more time?","Show technical thinking."),("Project","How did you test your project?","Mention functional and edge-case testing.")],
'Aptitude':[("Quantitative","A train travels 120 km in 2 hours. What is its speed?","Answer in km/h."),("Quantitative","What is 20% of 250?","Show calculation."),("Logical","If all A are B and all B are C, what follows?","State conclusion."),("Verbal","Which is better: 'I did many things' or 'I developed a Python module' ?","Explain why."),("Quantitative","₹800 discounted by 10% = ?","Calculate.")],
'Coding':[("Python","Write a Python function to check whether a string is a palindrome.","Focus on clarity."),("Python","Find the largest number in a list without max().","Explain complexity."),("Python","Count frequency of each character in a string.","Use a dictionary."),("DSA","Find duplicate values in a list.","Mention approach and complexity.")]
}

def answer_quality(answer):
    a=(answer or '').strip()
    if not a:return 0,['No answer provided.']
    score=35; n=len(a.split())
    if n>=15:score+=15
    if n>=35:score+=10
    keys=['because','example','project','result','experience','approach','problem','solution','impact']
    hits=sum(k in a.lower() for k in keys); score+=min(25,hits*5)
    tips=[]
    if n<15:tips.append('Give a more complete answer.')
    if hits<2:tips.append('Add a reason, example, or result.')
    if any(x in a.lower() for x in ['i think','maybe','not sure']):score-=8; tips.append('Use more confident language.')
    if not tips:tips.append('Good structure. Add a measurable result if possible.')
    return max(0,min(100,score)),tips

def company_rounds(role):
    r=(role or '').lower()
    if any(x in r for x in ['data','ml','ai']):return ['Aptitude','Coding','Technical','Project','Managerial','HR']
    if any(x in r for x in ['software','developer']):return ['Aptitude','Coding','Technical','Project','HR']
    return ['Aptitude','Technical','Project','HR']

# ---------------- AUTH ----------------
def auth_page():
    st.markdown('<div class="hero"><span class="badge">YOUR PLACEMENT JOURNEY STARTS HERE</span><h1>Turn preparation into your next offer.</h1><p>Build confidence, sharpen your answers, and practise with your personal AI interview coach — one round at a time.</p></div>',unsafe_allow_html=True)
    left,right=st.columns([1,1])
    with left:
        st.markdown('<div class="card"><h3>Login</h3><p class="small">Use your email, phone number, or username.</p></div>',unsafe_allow_html=True)
        identifier=st.text_input('Email / Phone / Username',key='login_id')
        password=st.text_input('Password',type='password',key='login_pw')
        if st.button('Login',type='primary',use_container_width=True):
            row=login_user(identifier,password)
            if row:
                st.session_state.user_id=row[0]; st.session_state.user_name=row[1]; st.rerun()
            else: st.error('Invalid login details.')
    with right:
        st.markdown('<div class="card"><h3>Create account</h3><p class="small">One account for your full placement journey.</p></div>',unsafe_allow_html=True)
        name=st.text_input('Full name',key='signup_name'); ident=st.text_input('Email / Phone / Username',key='signup_id'); pw=st.text_input('Create password',type='password',key='signup_pw'); pw2=st.text_input('Confirm password',type='password',key='signup_pw2')
        if st.button('Create Account',use_container_width=True):
            if not name.strip() or not ident.strip() or not pw: st.error('Fill all fields.')
            elif len(pw)<6: st.error('Password should be at least 6 characters.')
            elif pw!=pw2: st.error('Passwords do not match.')
            else:
                uid,err=create_user(ident,pw,name)
                if err: st.error(err)
                else: st.session_state.user_id=uid; st.session_state.user_name=name; st.success('Account created.'); st.rerun()

if 'user_id' not in st.session_state:
    auth_page(); st.stop()

uid=st.session_state.user_id; profile=get_profile(uid)

# ---------------- NAV ----------------
def nav():
    st.sidebar.markdown('## 🎯 InterviewMate')
    st.sidebar.caption('Your complete placement journey')
    if profile: st.sidebar.success(f"Hi, {profile[0]}")
    pages=['🏠 Dashboard','👤 Profile & Documents','🪄 Resume Tailor','🎯 Job Match','🧠 Diagnostic Test','📚 Preparation Roadmap','💻 Coding Round','🧪 Aptitude Round','🛠 Technical Round','📁 Project Round','🎤 HR & Communication','🤖 AI Mock Interview','🏢 Full Mock Placement','📊 Progress & Readiness']
    page=st.sidebar.radio('Navigate',pages)
    if st.sidebar.button('Log out'):
        for k in ('user_id','iv','api_key'): st.session_state.pop(k,None)
        st.rerun()
    return page

# ---------------- AI MOCK INTERVIEW (chat interviewer + camera + tab-switch termination) ----------------
INTERVIEW_PAGE='🤖 AI Mock Interview'
STRICT_FOCUS_CHECK=True   # True: also end the interview when the browser window loses focus (alt-tab / another app). False: only real tab switches.
INTERVIEW_KINDS={'Complete Placement Interview (All Topics)':'all','Mixed (HR + Technical + Project)':'mixed','HR / Behavioural':'hr','Technical':'technical','Project deep-dive':'project'}
VIOLATIONS={
    'tab_hidden':'You switched to another browser tab.',
    'window_blur':'You left the interview window (another window or app took focus).',
    'camera_lost':'The camera was turned off or disconnected.',
    'camera_denied':'Camera access was blocked.',
    'gaze_terminated':'Maximum look-away warning limit reached (10/10).',
}
_PROCTOR=components.declare_component('interviewmate_proctor',path=str(APP_DIR/'proctor_component'))
_VOICE=components.declare_component('interviewmate_voice',path=str(APP_DIR/'voice_component'))

def run_proctor(mode,session):
    """Show a live camera preview and monitor tab/window focus. Video stays in-browser; it is not recorded or uploaded."""
    st.markdown('#### 📷 Camera & interview monitoring')
    ev=_PROCTOR(mode=mode,session=session,strict_focus=STRICT_FOCUS_CHECK,key='im_proctor',default=None)
    if mode=='monitor':
        st.caption('Keep your face toward the camera. Looking away triggers a “Look at center” warning; 10 warnings terminate the interview. Camera video is processed in your browser and is not recorded or uploaded.')
    else:
        st.caption('Allow camera access to preview your camera before starting. Video stays in your browser and is not recorded or uploaded.')
    return ev

def end_interview(iv,status,reason='',overall=None):
    # Idempotent lifecycle transition: only the first terminal event may save/close this attempt.
    if iv.get('saved') or iv.get('lifecycle') in ('TERMINATING','COMPLETED','TERMINATED'):
        return
    iv['lifecycle']='TERMINATING'
    iv['status']=status
    iv['reason']=reason
    iv['saved']=True
    eng=iv['engine']
    save_interview(uid,iv['id'],iv['kind'],eng.mode,status,overall,reason,json.dumps(eng.transcript))
    if status=='finished' and overall is not None: save_score(uid,'AI Interview',overall)
    iv['lifecycle']='COMPLETED' if status=='finished' else 'TERMINATED'

def finish_interview(iv):
    with st.spinner('Preparing your feedback report…'):
        iv['engine'].complete=True; rep=iv['engine'].report(); iv['report']=rep
    end_interview(iv,'finished','',rep['overall'] if rep else None)

def get_api_key():
    with st.expander('🔑 Optional: enable Claude-powered conversational evaluation'):
        entered=st.text_input('Anthropic API key',type='password',help='Kept only in this browser session. You can also set the ANTHROPIC_API_KEY environment variable.')
        if entered.strip(): st.session_state.api_key=entered.strip()
    key=st.session_state.get('api_key') or os.environ.get('ANTHROPIC_API_KEY','')
    if not key:
        try: key=st.secrets.get('ANTHROPIC_API_KEY','')
        except Exception: key=''
    st.caption('🤖 AI mode: Claude-powered answer interpretation is enabled.' if key else '🧩 Offline mode: heuristic answer assessment and targeted follow-ups (no API key). This mode is less semantically flexible than an LLM.')
    return key

def interview_setup():
    # A new account may not have saved Profile & Documents yet.
    # Keep general interviews available instead of unpacking None.
    profile_data = profile or ('', '', '', '', '', 0, '')
    # Older or partially populated profile rows are padded safely.
    profile_data = tuple(profile_data) + ('',) * max(0, 7 - len(profile_data))
    name, role, company, resume, jd, _, _ = profile_data[:7]
    name = name or st.session_state.get('user_name', '')
    role = role or ''
    company = company or ''
    resume = resume or ''
    jd = jd or ''
    st.markdown("""<div class="hero"><span class="badge">VOICE-TO-VOICE MOCK INTERVIEW</span><h1>Your practice room. Your next breakthrough.</h1><p>Speak naturally, think out loud, and build real interview confidence. Your AI interviewer listens, responds aloud, and moves to the next question after a five-second pause.</p></div><div class="feature-grid"><div class="feature-tile"><div class="feature-icon">🎧</div><div class="feature-title">Speak your answers</div><div class="feature-desc">Hands-free voice conversation with automatic pause detection.</div></div><div class="feature-tile"><div class="feature-icon">📷</div><div class="feature-title">Camera check</div><div class="feature-desc">Preview your camera before you begin the monitored session.</div></div><div class="feature-tile"><div class="feature-icon">🎯</div><div class="feature-title">All-round practice</div><div class="feature-desc">Aptitude, reasoning, coding, technical, HR and more.</div></div><div class="feature-tile"><div class="feature-icon">🏆</div><div class="feature-title">Actionable feedback</div><div class="feature-desc">Review strengths, gaps and your interview performance.</div></div></div>""",unsafe_allow_html=True)
    st.markdown("""<div class="card"><b>How the voice interview works</b><br><span class="small">Your browser microphone captures your answer. When you stop speaking for 5 seconds, InterviewMate submits the answer, responds with speech, and asks the next question. Chrome or Edge is recommended. Microphone permission is required. Speech recognition support depends on your browser and may require internet access.</span></div>""",unsafe_allow_html=True)
    c1,c2=st.columns([2,1])
    label=c1.selectbox('Interview coverage',list(INTERVIEW_KINDS),index=0)
    is_all=INTERVIEW_KINDS[label]=='all'
    n=c2.slider('Main questions',18 if is_all else 8,20,18 if is_all else 8)
    key=get_api_key()
    cam_event=run_proctor('check','preflight')
    if isinstance(cam_event,dict):
        if cam_event.get('type') in ('camera_ready','monitoring'):
            st.session_state.camera_ok=True
        elif cam_event.get('type') in ('camera_denied','camera_lost'):
            st.session_state.camera_ok=False
    st.caption('The complete interview includes aptitude, logical reasoning, technical fundamentals, coding, projects, critical thinking, managerial scenarios, communication and HR. Offline mode works without an API key; Claude mode is optional.')
    if not resume:
        st.warning('For the best personalized interview, save your resume in Profile & Documents first. You can still continue with a general interview.')
    camera_ok=bool(st.session_state.get('camera_ok',False))
    if camera_ok:
        st.success('Camera is connected. You can start the monitored interview.')
    else:
        st.info('Camera permission is required. Allow access in your browser prompt; if you blocked it earlier, click the camera icon beside the address bar and allow Camera, then reload this page.')
    agree=st.checkbox('I am ready to allow microphone access and answer aloud.')
    if st.button('🎙️ Start voice interview',type='primary',use_container_width=True,disabled=(not agree or not camera_ok)):
        try:
            llm=ClaudeLLM(key,os.environ.get('INTERVIEWMATE_MODEL',DEFAULT_MODEL)) if key else None
            eng=InterviewEngine(name=name or st.session_state.get('user_name',''),role=role,company=company,resume=resume,jd=jd,kind=INTERVIEW_KINDS[label],
                                n_questions=n,skill_hits=skill_hits,sections_from_resume=sections_from_resume,answer_quality=answer_quality,llm=llm)
            with st.spinner('Your interviewer is joining…'): eng.start()
        except BotUnavailable as e:
            st.error(f'Could not reach the AI interviewer ({e}). Check the API key / internet connection, or clear the key to use offline mode.'); return
        st.session_state.iv={'id':uuid.uuid4().hex[:10],'status':'active','lifecycle':'ACTIVE','kind':INTERVIEW_KINDS[label],'engine':eng,'reason':'','saved':False,'report':None,'processed_voice_id':None}
        st.rerun()
    rows=get_interviews(uid)
    if rows:
        st.markdown('### Recent interviews')
        st.dataframe([{'Date':d,'Type':k,'Mode':m,'Result':st_.title(),'Score':('' if o is None else round(o)),'Note':r} for d,k,m,st_,o,r in rows],use_container_width=True,hide_index=True)

def interview_active(iv):
    eng=iv['engine']
    st.markdown("""<div class="hero"><span class="badge">LIVE SESSION</span><h1>AI Voice Interview</h1><p>Answer out loud. A 5-second pause submits your answer. Keep looking toward the camera; 10 look-away warnings end the session.</p></div>""",unsafe_allow_html=True)
    # Two-column interview room: camera stays beside the questions on desktop and stacks neatly on phones.
    interview_col, camera_col = st.columns([1.8, 1], gap='large')
    with camera_col:
        proctor_event=run_proctor('monitor',iv['id'])
    if isinstance(proctor_event,dict) and proctor_event.get('type') in VIOLATIONS:
        end_interview(iv,'terminated',VIOLATIONS[proctor_event['type']])
        st.error('Interview terminated: '+VIOLATIONS[proctor_event['type']])
        st.session_state.camera_ok=False
        st.rerun()
    cur,total=eng.progress()
    with interview_col:
        a,b=st.columns([3,1])
        a.markdown(f'**Question {cur} of {total}**' if total else f'**Answer {cur} · adaptive interview**')
        if total: a.progress(min(1.0,(cur-1)/total))
        if b.button('⏹ End interview',use_container_width=True):
            if eng.user_turns()==0: end_interview(iv,'ended','You ended the interview before answering anything.')
            else: finish_interview(iv)
            st.rerun()
        # Keep the live interview focused on the interviewer prompt only.
        # Candidate answers remain available internally for assessment, but are not rendered in the UI.
        latest_bot=next((m['content'] for m in reversed(eng.transcript) if m['role']=='assistant'),'')
        st.markdown('<div class="card"><b>Current interview prompt</b><br><span class="small">Listen to the interviewer and answer aloud. Your spoken responses are evaluated privately and are not shown on screen.</span></div>',unsafe_allow_html=True)
        if latest_bot:
            st.info(latest_bot)
        voice= _VOICE(question=latest_bot, session=iv['id'], enabled=(iv.get('status')=='active'), lifecycle=iv.get('lifecycle','ACTIVE'), silence_seconds=5, max_answer_seconds=120, key='im_voice_'+iv['id'], default=None)
        if isinstance(voice,dict) and voice.get('event')=='answer_submitted' and voice.get('answer') and voice.get('answer_id') != iv.get('processed_voice_id') and iv.get('status')=='active':
            iv['processed_voice_id']=voice.get('answer_id')
            try:
                with st.spinner('Answer received — preparing the interviewer response…'):
                    eng.reply(voice['answer'])
            except BotUnavailable as e:
                st.error(f'The interviewer could not respond ({e}). Your answer was captured. You can use the text-answer fallback below.'); return
            if eng.complete: finish_interview(iv)
            st.rerun()
        st.markdown('#### Alternative answer input')
        with st.form('text_answer_'+iv['id'], clear_on_submit=True):
            typed_answer=st.text_area('If voice recognition is unavailable, type your answer here. Submitted text will not be displayed in the interview transcript.', key='typed_answer_'+iv['id'], height=100)
            typed_submit=st.form_submit_button('Submit text answer', use_container_width=True)
        if typed_submit and typed_answer.strip():
            try:
                with st.spinner('Preparing the interviewer response…'):
                    eng.reply(typed_answer.strip())
            except BotUnavailable as e:
                st.error(f'The interviewer could not respond ({e}). Please try again or check the AI configuration.'); return
            if eng.complete: finish_interview(iv)
            st.rerun()
        st.caption('Microphone access starts only after you click Enable microphone inside the voice panel. Chrome or Edge on localhost/HTTPS is recommended. The browser must support SpeechRecognition for spoken answers; otherwise use the text-answer fallback.')

def interview_result(iv):
    eng=iv['engine']; status=iv['status']
    # Keep the voice iframe alive for one render with enabled=False so speech and recognition are explicitly stopped.
    _VOICE(question='', session=iv['id'], enabled=False, lifecycle=iv.get('lifecycle','TERMINATED'), silence_seconds=5, key='im_voice_'+iv['id'], default=None)
    _PROCTOR(mode='stop', session=iv['id'], strict_focus=False, key='im_proctor', default=None)
    if status=='terminated':
        st.error('🚫 Interview terminated: '+iv['reason'])
        st.write('Leaving the interview tab or window is not allowed, so this attempt has been closed and saved without a score. You can start a new interview any time.')
    elif status=='abandoned': st.warning('⚠️ '+iv['reason']+' This attempt was saved without a score.')
    elif status=='ended': st.info(iv['reason'])
    else:
        rep=iv['report']
        if not rep: st.info('No answers to evaluate.')
        else:
            st.markdown('## 📋 Interview feedback'); a,b=st.columns(2); a.metric('Overall score',f"{rep['overall']}%"); b.metric('Verdict',rep['verdict'])
            st.progress(rep['overall']/100)
            if rep.get('note'): st.caption(rep['note'])
            c1,c2=st.columns(2)
            with c1:
                st.markdown('**✅ Strengths**'); [st.write('• '+x) for x in rep['strengths']]
            with c2:
                st.markdown('**🎯 Improve next**'); [st.write('• '+x) for x in rep['improvements']]
            st.markdown('### Question by question')
            for r in rep['per_question']:
                with st.expander(f"{r['score']}/100 · {r.get('topic') or r['question'][:70]}"):
                    st.write('**Question:** '+r['question'])
                    if r.get('feedback'): st.write('**Feedback:** '+r['feedback'])
    if st.button('Start a new interview',type='primary'): st.session_state.pop('iv',None); st.rerun()

def ai_interview_page():
    st.title('🤖 AI Mock Interview')
    st.caption('A two-way voice interviewer that listens to your spoken answers, responds aloud, and gives a final report. A saved resume makes questions more personal but is optional.')
    iv=st.session_state.get('iv')
    if iv and iv['status']=='active': interview_active(iv)
    elif iv: interview_result(iv)
    else: interview_setup()

page=nav(); profile=get_profile(uid)

# Leaving the AI Mock Interview page during an active session terminates and saves the attempt.
_active_iv=st.session_state.get('iv')
if _active_iv and _active_iv.get('status')=='active' and page != INTERVIEW_PAGE:
    end_interview(_active_iv,'terminated','You navigated away from the interview page.')
    st.session_state.camera_ok=False
    st.warning('Your interview was terminated because you left the interview page. Open AI Mock Interview to review the status or start again.')

# ---------------- PAGES ----------------
if page=='🏠 Dashboard':
    st.markdown('<div class="hero"><span class="badge">YOUR PERSONAL PLACEMENT CO-PILOT</span><span class="badge">AI-POWERED PRACTICE</span><h1>From “I hope I’m ready” to “I’ve got this.”</h1><p>One focused space to build a stronger resume, discover skill gaps, practise every placement round, and track your progress with confidence.</p></div>',unsafe_allow_html=True)
    st.markdown('<div class="feature-grid"><div class="feature-tile"><div class="feature-icon">✨</div><div class="feature-title">Resume Studio</div><div class="feature-desc">Tailor your profile to the role and highlight your strengths.</div></div><div class="feature-tile"><div class="feature-icon">🎙️</div><div class="feature-title">Live AI Interview</div><div class="feature-desc">Speak naturally, get follow-ups, and practise under pressure.</div></div><div class="feature-tile"><div class="feature-icon">🧠</div><div class="feature-title">Skill Builder</div><div class="feature-desc">Prepare for aptitude, reasoning, coding, technical and HR rounds.</div></div><div class="feature-tile"><div class="feature-icon">📈</div><div class="feature-title">Progress Tracker</div><div class="feature-desc">See your readiness improve and know what to practise next.</div></div></div>',unsafe_allow_html=True)
    if not profile:
        st.info('Start with Profile & Documents: upload your resume and the company Job Description.')
    else:
        name,role,company,resume,jd,ready,tailored=profile; match,matched,missing=jd_match(resume,jd)
        c=st.columns(4); c[0].metric('Job Match',f'{match}%'); c[1].metric('Readiness',f'{ready:.0f}%'); c[2].metric('Resume Skills',len(skill_hits(resume))); c[3].metric('JD Skill Gaps',len(missing))
        st.markdown('### Your placement flow')
        st.write('**1. Validate Resume → 2. Understand Company/Role → 3. Tailor Resume → 4. Close Skill Gaps → 5. Practice Rounds → 6. Full Mock → 7. Readiness**')
        if tailored: st.success('Your role-specific resume has been tailored. Open Resume Tailor to review/download it.')
        else: st.warning('Tailor your resume to the company + job role before applying.')

elif page=='👤 Profile & Documents':
    st.title('👤 Profile & Documents')
    current=profile or ('','','','','',0,'')
    name=st.text_input('Your name',current[0] or st.session_state.get('user_name',''))
    role=st.text_input('Target job role',current[1] or 'Software Engineer')
    company=st.text_input('Company name',current[2] or '')
    resume_file=st.file_uploader('Upload Resume — PDF / DOCX / TXT',type=['pdf','docx','txt'],key='resume_upload')
    jd_file=st.file_uploader('Upload Job Description — PDF / DOCX / TXT',type=['pdf','docx','txt'],key='jd_upload')
    resume=extract_text(resume_file) if resume_file else current[3]
    jd=extract_text(jd_file) if jd_file else current[4]
    if resume_file:
        ok,msg=validate_document(resume,'resume'); (st.success if ok else st.error)(('✅ ' if ok else '❌ ')+msg)
    if jd_file:
        ok,msg=validate_document(jd,'job description'); (st.success if ok else st.error)(('✅ ' if ok else '❌ ')+msg)
    resume_text=st.text_area('Resume text',resume,height=250)
    jd_text=st.text_area('Job description text',jd,height=220)
    if st.button('💾 Save Profile',type='primary'):
        rok,rmsg=validate_document(resume_text,'resume') if resume_text else (False,'Resume is empty.')
        jok,jmsg=validate_document(jd_text,'job description') if jd_text else (True,'')
        if not rok: st.error('Resume not saved: '+rmsg)
        elif jd_text and not jok: st.error('Job description not saved: '+jmsg)
        else:
            r=readiness(resume_text,jd_text); save_profile(uid,name,role,company,resume_text,jd_text,r,current[6] if len(current)>6 else '')
            st.success(f'Profile saved. Initial readiness: {r}%')
    if resume_text: st.write('**Detected resume skills:**',', '.join(skill_hits(resume_text)) or 'None detected')

elif page=='🪄 Resume Tailor':
    st.title('🪄 Resume Tailor — Company + Role Specific')
    st.caption('InterviewMate rewrites and reorders the information you already have so it aligns better with the selected company and job description. It does not invent experience.')
    if not profile: st.warning('Complete Profile & Documents first.')
    else:
        name,role,company,resume,jd,ready,tailored=profile
        c1,c2=st.columns(2); role2=c1.text_input('Job role',role); company2=c2.text_input('Company',company)
        jd2=st.text_area('Paste / review the exact company Job Description',jd,height=220)
        if not resume: st.error('A valid resume is required.')
        elif not jd2: st.warning('Add the company Job Description to tailor accurately.')
        else:
            ok,msg=validate_document(jd2,'job description')
            if not ok: st.error('Invalid Job Description: '+msg)
            if st.button('✨ Tailor My Resume',type='primary',use_container_width=True):
                new_text,matched,missing,score=tailor_resume(resume,jd2,role2,company2)
                save_profile(uid,name,role2,company2,resume,jd2,readiness(resume,jd2),new_text)
                st.session_state.tailored=new_text; st.rerun()
        tailored=st.session_state.get('tailored',tailored)
        if tailored:
            st.markdown('### Tailored result')
            old_match,old_m,old_gap=jd_match(resume,jd2); _,matched,missing,score=tailor_resume(resume,jd2,role2,company2) if jd2 else (0,[],[],0)
            a,b,c=st.columns(3); a.metric('Current JD Match',f'{old_match}%'); b.metric('Matched Keywords',len(matched)); c.metric('Gaps to learn',len(missing))
            st.text_area('ATS-friendly tailored resume',tailored,height=600)
            st.download_button('⬇️ Download Tailored Resume (TXT)',tailored,file_name='InterviewMate_Tailored_Resume.txt',mime='text/plain',use_container_width=True)
            try:
                st.download_button('📄 Download Tailored Resume (DOCX)',resume_docx(tailored),file_name='InterviewMate_Tailored_Resume.docx',mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',use_container_width=True)
            except Exception as e: st.info('DOCX download needs python-docx installed.')
            st.markdown('### What was changed')
            st.write('• Role/company-specific professional summary')
            st.write('• JD-matched skills moved to the front')
            st.write('• Existing project/experience lines prioritized by relevance')
            st.write('• ATS keywords identified from the JD')
            if missing: st.warning('Missing from original resume: '+', '.join(missing))
            st.info('Important: only add a missing keyword to your final resume if you genuinely know or have used that skill.')

elif page=='🎯 Job Match':
    st.title('🎯 Resume ↔ Job Description Match')
    if not profile: st.warning('Create your profile first.')
    else:
        _,_,_,resume,jd,_,_=profile
        if not jd: st.info('Add a Job Description in Profile & Documents.')
        else:
            score,matched,missing=jd_match(resume,jd); a,b,c=st.columns(3); a.metric('Job Match',f'{score}%'); b.metric('Matched',len(matched)); c.metric('Gaps',len(missing)); st.progress(score/100)
            st.success('Matched: '+(', '.join(matched) or 'None'))
            st.warning('Improve: '+(', '.join(missing) or 'No major common skill gaps detected.'))

elif page=='🧠 Diagnostic Test':
    st.title('🧠 Placement Diagnostic Test')
    qs=[('Python','Which data type stores key-value pairs?','dictionary'),('SQL','Which clause filters grouped records?','having'),('ML','Which problem predicts a continuous number?','regression'),('DSA','Average time complexity of binary search?','log'),('HR','Which structure is useful for behavioral answers?','star'),('Aptitude','20% of 250 is?','50')]
    with st.form('diagnostic'):
        answers=[st.text_input(f'{topic}: {q}',key='d'+str(i)) for i,(topic,q,a) in enumerate(qs)]; submit=st.form_submit_button('Evaluate Diagnostic')
    if submit:
        scores=[]
        for (_,_,expected),ans in zip(qs,answers): scores.append(100 if expected in ans.lower() else (40 if ans.strip() else 0))
        total=round(sum(scores)/len(scores)); st.metric('Diagnostic Score',f'{total}%'); st.progress(total/100); save_score(uid,'Diagnostic',total)
        if profile: save_profile(uid,profile[0],profile[1],profile[2],profile[3],profile[4],readiness(profile[3],profile[4],scores),profile[6])

elif page=='📚 Preparation Roadmap':
    st.title('📚 Personalized Preparation Roadmap')
    if not profile: st.warning('Create your profile first.')
    else:
        _,role,_,resume,jd,ready,_=profile; _,_,missing=jd_match(resume,jd); priority=missing[:6] if missing else ['Python','SQL','DSA','Communication']; days=st.slider('Plan length',7,30,14); st.metric('Current readiness',f'{ready:.0f}%')
        st.write('**Priority:** '+', '.join(priority))
        for d in range(1,days+1):
            focus=priority[(d-1)%len(priority)]
            with st.expander(f'Day {d} — {focus}'):
                st.write(f'30 min: revise {focus} · 20 min: practice questions · 15 min: interview answer · 10 min: mistake review')

elif page in ['💻 Coding Round','🧪 Aptitude Round','🛠 Technical Round','📁 Project Round','🎤 HR & Communication']:
    mapping={'💻 Coding Round':'Coding','🧪 Aptitude Round':'Aptitude','🛠 Technical Round':'Technical','📁 Project Round':'Project','🎤 HR & Communication':'HR'}; rn=mapping[page]; st.title(page)
    key='idx_'+rn; st.session_state.setdefault(key,0); qs=QUESTION_BANK[rn]; idx=st.session_state[key]%len(qs); topic,q,hint=qs[idx]; st.markdown(f'### {topic}'); st.info(q); st.caption('Hint: '+hint); ans=st.text_area('Your answer',height=180,key='ans'+rn+str(idx))
    if st.button('Evaluate Answer',type='primary'): score,tips=answer_quality(ans); st.metric('Answer Score',f'{score}/100'); st.progress(score/100); [st.write('• '+x) for x in tips]; save_score(uid,rn,score)
    a,b=st.columns(2)
    if a.button('← Previous'): st.session_state[key]-=1; st.rerun()
    if b.button('Next Question →'): st.session_state[key]+=1; st.rerun()

elif page==INTERVIEW_PAGE:
    ai_interview_page()

elif page=='🏢 Full Mock Placement':
    st.title('🏢 Full Mock Placement')
    if not profile: st.warning('Create your profile first.')
    else:
        name,role,company,resume,jd,ready,tailored=profile; rounds=company_rounds(role); st.write('Simulation for **'+(company or 'Target Company')+' — '+role+'**')
        vals=[]
        for r in rounds: vals.append(st.slider(r,0,100,0,key='mock'+r))
        if st.button('Generate Final Placement Report',type='primary'):
            overall=round(sum(vals)/len(vals)); st.metric('Overall Readiness',f'{overall}%'); (st.success if overall>=80 else st.warning if overall>=65 else st.error)('🟢 READY' if overall>=80 else '🟡 ALMOST READY' if overall>=65 else '🔴 NOT READY YET'); weak=rounds[vals.index(min(vals))]; st.write('**Highest priority:** '+weak)
            for r,s in zip(rounds,vals): save_score(uid,'Mock '+r,s)
            save_profile(uid,name,role,company,resume,jd,overall,tailored)

elif page=='📊 Progress & Readiness':
    st.title('📊 Progress & Readiness'); rows=get_scores(uid)
    if not rows: st.info('Complete a round to build progress history.')
    else:
        latest={}
        for r,s,d in rows:
            if r not in latest: latest[r]=s
        cols=st.columns(min(4,max(1,len(latest))))
        for i,(r,s) in enumerate(latest.items()): cols[i%len(cols)].metric(r,f'{s:.0f}%')
        st.bar_chart(latest); st.dataframe([{'Round':r,'Score':round(s,1),'Date':d} for r,s,d in rows[:20]],use_container_width=True,hide_index=True)
