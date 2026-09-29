from datetime import datetime, timedelta, timezone
import hashlib, secrets, re, os, json, urllib.parse, urllib.request
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Header, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import create_engine, String, Integer, Float, Text, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker

RAW_DATABASE_URL=os.getenv("DATABASE_URL","").strip()
# Render should inject a real postgres:// or postgresql:// URL. If an old/manual
# deployment leaves a placeholder or malformed value, fall back safely to SQLite
# instead of crashing during import. A valid DATABASE_URL always wins.
if RAW_DATABASE_URL.startswith(("postgres://","postgresql://","sqlite:///")):
    DATABASE_URL=RAW_DATABASE_URL
else:
    DATABASE_URL="sqlite:///./skillbridge.db"
engine=create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True
)
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
class Base(DeclarativeBase): pass

class User(Base):
    __tablename__="users"; id:Mapped[int]=mapped_column(Integer,primary_key=True); name:Mapped[str]=mapped_column(String(160)); email:Mapped[str]=mapped_column(String(200),unique=True,index=True); password_hash:Mapped[str]=mapped_column(String(300)); role:Mapped[str]=mapped_column(String(40)); organization:Mapped[str]=mapped_column(String(200),default="")
class SessionToken(Base):
    __tablename__="session_tokens"; id:Mapped[int]=mapped_column(Integer,primary_key=True); token:Mapped[str]=mapped_column(String(160),unique=True,index=True); user_id:Mapped[int]=mapped_column(Integer); expires_at:Mapped[str]=mapped_column(String(50))
class Opportunity(Base):
    __tablename__="opportunities"; id:Mapped[int]=mapped_column(Integer,primary_key=True); title:Mapped[str]=mapped_column(String(200)); type:Mapped[str]=mapped_column(String(60)); provider:Mapped[str]=mapped_column(String(200)); location:Mapped[str]=mapped_column(String(120)); skills:Mapped[str]=mapped_column(Text,default=""); description:Mapped[str]=mapped_column(Text,default=""); status:Mapped[str]=mapped_column(String(40),default="Published"); owner_id:Mapped[int]=mapped_column(Integer,default=0)
class Application(Base):
    __tablename__="applications"; id:Mapped[int]=mapped_column(Integer,primary_key=True); student_id:Mapped[int]=mapped_column(Integer); opportunity_id:Mapped[int]=mapped_column(Integer); status:Mapped[str]=mapped_column(String(40),default="Submitted"); created_at:Mapped[str]=mapped_column(String(50),default=lambda:datetime.now(timezone.utc).isoformat())
class SkillProfile(Base):
    __tablename__="skill_profiles"; id:Mapped[int]=mapped_column(Integer,primary_key=True); owner_id:Mapped[int]=mapped_column(Integer,unique=True); technical_score:Mapped[float]=mapped_column(Float,default=0); soft_score:Mapped[float]=mapped_column(Float,default=0); strengths:Mapped[str]=mapped_column(Text,default=""); gaps:Mapped[str]=mapped_column(Text,default=""); skills:Mapped[str]=mapped_column(Text,default=""); interests:Mapped[str]=mapped_column(Text,default="")
class LearningItem(Base):
    __tablename__="learning_items"; id:Mapped[int]=mapped_column(Integer,primary_key=True); title:Mapped[str]=mapped_column(String(200)); kind:Mapped[str]=mapped_column(String(60)); provider:Mapped[str]=mapped_column(String(160)); skills:Mapped[str]=mapped_column(Text,default="")
class Enrollment(Base):
    __tablename__="enrollments"; id:Mapped[int]=mapped_column(Integer,primary_key=True); user_id:Mapped[int]=mapped_column(Integer); item_id:Mapped[int]=mapped_column(Integer); status:Mapped[str]=mapped_column(String(40),default="In Progress"); progress:Mapped[int]=mapped_column(Integer,default=0)
class PortfolioItem(Base):
    __tablename__="portfolio_items"; id:Mapped[int]=mapped_column(Integer,primary_key=True); user_id:Mapped[int]=mapped_column(Integer); title:Mapped[str]=mapped_column(String(200)); kind:Mapped[str]=mapped_column(String(60)); description:Mapped[str]=mapped_column(Text,default=""); skills:Mapped[str]=mapped_column(Text,default=""); verified:Mapped[bool]=mapped_column(default=False)
class Collaboration(Base):
    __tablename__="collaborations"; id:Mapped[int]=mapped_column(Integer,primary_key=True); title:Mapped[str]=mapped_column(String(200)); kind:Mapped[str]=mapped_column(String(60)); provider:Mapped[str]=mapped_column(String(200)); description:Mapped[str]=mapped_column(Text,default=""); target_role:Mapped[str]=mapped_column(String(40),default="All"); status:Mapped[str]=mapped_column(String(40),default="Open")
Base.metadata.create_all(engine)

app=FastAPI(title="SkillBridge API",version="2.0.0")
FRONTEND_ORIGIN=os.getenv("FRONTEND_ORIGIN","").strip()
ALLOWED_ORIGINS=[x.strip() for x in FRONTEND_ORIGIN.split(",") if x.strip()] or ["http://localhost:5500","http://127.0.0.1:5500"]
app.add_middleware(CORSMiddleware,allow_origins=ALLOWED_ORIGINS,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
ROLES={"Student","Academician","Industry","Institution"}

def db():
    s=SessionLocal()
    try: yield s
    finally: s.close()

def hp(password,salt=None):
    salt=salt or secrets.token_hex(16)
    return salt+"$"+hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),120000).hex()
def vp(password,stored):
    try:
        salt,digest=stored.split("$",1)
        return secrets.compare_digest(hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),120000).hex(),digest)
    except Exception: return False
def payload(u): return {"id":u.id,"name":u.name,"email":u.email,"role":u.role,"organization":u.organization}
def current(authorization:Optional[str]=Header(None),skillbridge_session:Optional[str]=Cookie(None),s:Session=Depends(db)):
    t=(skillbridge_session or "").strip()
    if not t and authorization and authorization.lower().startswith("bearer "):
        t=authorization.split(" ",1)[1].strip()
    if not t: raise HTTPException(401,"Authentication required")
    st=s.scalar(select(SessionToken).where(SessionToken.token==t))
    if not st or datetime.fromisoformat(st.expires_at)<=datetime.now(timezone.utc): raise HTTPException(401,"Session expired or invalid")
    u=s.get(User,st.user_id)
    if not u: raise HTTPException(401,"User not found")
    return u
def role(*roles):
    def dep(u:User=Depends(current)):
        if u.role not in roles: raise HTTPException(403,"This action is not available for your role")
        return u
    return dep
def parts(v): return [x.strip() for x in (v or "").split(",") if x.strip()]
ALIASES={"ml":"machine learning","ai/ml":"machine learning","machine-learning":"machine learning","js":"javascript","reactjs":"react","nodejs":"node","postgres":"postgresql","dsa":"data structures"}
def norm(v): return ALIASES.get(re.sub(r"\s+"," ",v.strip().lower()),re.sub(r"\s+"," ",v.strip().lower()))
def match(profile,required):
    p={norm(x) for x in profile}; r={norm(x) for x in required}; hit=sorted(p&r); miss=sorted(r-p)
    coverage=round(len(hit)/len(r)*100) if r else 0
    sem=round(min(100,coverage+len({x for x in p if any(a in x or x in a for a in r)})*5))
    return {"matched_skills":hit,"missing_skills":miss,"skill_coverage":coverage,"semantic_similarity":sem}
def score(p,required):
    m=match(p.get("skills",[]),required)
    total=round(.55*m["skill_coverage"]+.20*m["semantic_similarity"]+.15*p.get("technical_score",0)+.10*p.get("soft_score",0))
    return {**m,"match":total,"score_breakdown":{"skill_coverage":round(.55*m["skill_coverage"],1),"semantic_similarity":round(.20*m["semantic_similarity"],1),"technical":round(.15*p.get("technical_score",0),1),"soft_skills":round(.10*p.get("soft_score",0),1)}}

class Register(BaseModel): name:str=Field(min_length=2); email:EmailStr; password:str=Field(min_length=6); role:str="Student"; organization:str=""
class Login(BaseModel): email:EmailStr; password:str
class OpportunityIn(BaseModel): title:str; type:str="Internship"; provider:str=""; location:str="Flexible"; skills:List[str]=[]; description:str=""
class ApplicationIn(BaseModel): opportunity_id:int
class ProfileIn(BaseModel): technical_score:float=0; soft_score:float=0; strengths:List[str]=[]; gaps:List[str]=[]; skills:List[str]=[]; interests:List[str]=[]
class PortfolioIn(BaseModel): title:str; kind:str="Project"; description:str=""; skills:List[str]=[]
class ProgressIn(BaseModel): progress:int=Field(ge=0,le=100)
class PasswordChange(BaseModel):
    current_password:str=Field(min_length=6)
    new_password:str=Field(min_length=8)
class CollaborationIn(BaseModel): title:str; kind:str="Workshop"; provider:str=""; description:str=""; target_role:str="Student"

def op(o): return {"id":o.id,"title":o.title,"type":o.type,"provider":o.provider,"location":o.location,"skills":parts(o.skills),"description":o.description,"status":o.status}
def prof(p): return {"technical_score":p.technical_score,"soft_score":p.soft_score,"strengths":parts(p.strengths),"gaps":parts(p.gaps),"skills":parts(p.skills),"interests":parts(p.interests)}

@app.get("/api/health")
def health(): return {"status":"ok","service":"SkillBridge API","version":"2.0.0"}

@app.post("/api/auth/register",status_code=201)
def register(x:Register,s:Session=Depends(db)):
    if x.role not in ROLES: raise HTTPException(400,"Invalid role")
    if s.scalar(select(User).where(User.email==x.email.lower())): raise HTTPException(409,"Email already registered")
    u=User(name=x.name.strip(),email=x.email.lower(),password_hash=hp(x.password),role=x.role,organization=x.organization.strip()); s.add(u); s.commit(); s.refresh(u); return {"user":payload(u)}
@app.post("/api/auth/login")
def login(x:Login,response:Response,s:Session=Depends(db)):
    u=s.scalar(select(User).where(User.email==x.email.lower()))
    if not u or not vp(x.password,u.password_hash): raise HTTPException(401,"Invalid email or password")
    exp=datetime.now(timezone.utc)+timedelta(hours=12); token=secrets.token_urlsafe(48); s.add(SessionToken(token=token,user_id=u.id,expires_at=exp.isoformat())); s.commit()
    response.set_cookie("skillbridge_session",token,max_age=12*60*60,httponly=True,secure=True,samesite="none",path="/")
    return {"expires_at":exp.isoformat(),"user":payload(u)}
@app.get("/api/auth/me")
def me(u:User=Depends(current)): return payload(u)

@app.post("/api/auth/change-password")
def change_password(x:PasswordChange,u:User=Depends(current),s:Session=Depends(db)):
    if not vp(x.current_password,u.password_hash): raise HTTPException(401,"Current password is incorrect")
    u.password_hash=hp(x.new_password); s.commit()
    s.query(SessionToken).filter(SessionToken.user_id==u.id).delete(synchronize_session=False); s.commit()
    return {"ok":True,"message":"Password changed; please log in again."}

@app.post("/api/auth/logout")
def logout(response:Response,authorization:Optional[str]=Header(None),skillbridge_session:Optional[str]=Cookie(None),s:Session=Depends(db)):
    t=(skillbridge_session or "").strip()
    if not t and authorization and authorization.lower().startswith("bearer "): t=authorization.split(" ",1)[1].strip()
    if t:
        st=s.scalar(select(SessionToken).where(SessionToken.token==t))
        if st: s.delete(st); s.commit()
    response.delete_cookie("skillbridge_session",path="/")
    return {"ok":True}

MARKET_CACHE={"at":0,"data":[],"source":"none"}
MARKET_TTL=300

def _http_json(url,timeout=12):
    req=urllib.request.Request(url,headers={"User-Agent":"SkillBridge/2.1"})
    with urllib.request.urlopen(req,timeout=timeout) as r: return json.loads(r.read().decode("utf-8"))

@app.get("/api/market/jobs")
def market_jobs(q:Optional[str]="software engineer",location:Optional[str]="remote",limit:int=20):
    limit=max(5,min(limit,40)); now=datetime.now(timezone.utc).timestamp()
    if now-MARKET_CACHE["at"]<MARKET_TTL and MARKET_CACHE["data"]: return {"jobs":MARKET_CACHE["data"],"source":MARKET_CACHE["source"],"fetched_at":datetime.fromtimestamp(MARKET_CACHE["at"],timezone.utc).isoformat(),"live":True}
    jobs=[]; source="none"
    app_id=os.getenv("ADZUNA_APP_ID","").strip(); app_key=os.getenv("ADZUNA_APP_KEY","").strip()
    if app_id and app_key:
        try:
            country=os.getenv("ADZUNA_COUNTRY","in").strip().lower(); params=urllib.parse.urlencode({"app_id":app_id,"app_key":app_key,"results_per_page":limit,"what":q,"where":location})
            raw=_http_json(f"https://api.adzuna.com/v1/api/jobs/{country}/search/1?{params}")
            for x in raw.get("results",[]): jobs.append({"id":"adzuna-"+str(x.get("id")),"title":x.get("title",""),"company":(x.get("company") or {}).get("display_name","Unknown"),"location":(x.get("location") or {}).get("display_name",location),"description":x.get("description",""),"url":x.get("redirect_url",""),"created":x.get("created"),"source":"Adzuna"})
            source="Adzuna"
        except Exception as e: print(f"Adzuna feed unavailable: {e}")
    if not jobs:
        try:
            raw=_http_json("https://www.arbeitnow.com/api/job-board-api"); rows=raw.get("data",[])
            words=[w.lower() for w in re.findall(r"[a-z0-9+#.]+",q or "") if len(w)>2]
            for x in rows:
                hay=(x.get("title","")+" "+x.get("description","")).lower()
                if words and not any(w in hay for w in words): continue
                jobs.append({"id":"arbeitnow-"+str(x.get("slug") or len(jobs)),"title":x.get("title",""),"company":x.get("company_name","Unknown"),"location":x.get("location") or "Remote","description":x.get("description",""),"url":x.get("url",""),"created":x.get("created_at"),"source":"Arbeitnow"})
                if len(jobs)>=limit: break
            source="Arbeitnow"
        except Exception as e: print(f"Public market feed unavailable: {e}")
    MARKET_CACHE.update({"at":now,"data":jobs,"source":source})
    return {"jobs":jobs,"source":source,"fetched_at":datetime.fromtimestamp(now,timezone.utc).isoformat(),"live":bool(jobs),"cache_seconds":MARKET_TTL}
@app.get("/api/opportunities")
def opportunities(kind:Optional[str]=None,s:Session=Depends(db)):
    q=select(Opportunity).where(Opportunity.status!="Closed")
    if kind: q=q.where(Opportunity.type==kind)
    return [op(x) for x in s.scalars(q.order_by(Opportunity.id.desc())).all()]
@app.post("/api/opportunities",status_code=201)
def create_opportunity(x:OpportunityIn,u:User=Depends(role("Industry")),s:Session=Depends(db)):
    o=Opportunity(title=x.title,type=x.type,provider=x.provider or u.organization or u.name,location=x.location,skills=", ".join(x.skills),description=x.description,owner_id=u.id); s.add(o); s.commit(); s.refresh(o); return op(o)
@app.patch("/api/opportunities/{oid}/close")
def close_opportunity(oid:int,u:User=Depends(role("Industry")),s:Session=Depends(db)):
    o=s.get(Opportunity,oid)
    if not o or o.owner_id!=u.id: raise HTTPException(404,"Opportunity not found")
    o.status="Closed"; s.commit(); return op(o)

@app.get("/api/skill-profiles/me")
def get_profile(u:User=Depends(role("Student")),s:Session=Depends(db)):
    p=s.scalar(select(SkillProfile).where(SkillProfile.owner_id==u.id)); return prof(p) if p else None
@app.put("/api/skill-profiles")
def save_profile(x:ProfileIn,u:User=Depends(role("Student")),s:Session=Depends(db)):
    p=s.scalar(select(SkillProfile).where(SkillProfile.owner_id==u.id))
    if not p: p=SkillProfile(owner_id=u.id); s.add(p)
    p.technical_score=x.technical_score;p.soft_score=x.soft_score;p.strengths=", ".join(x.strengths);p.gaps=", ".join(x.gaps);p.skills=", ".join(x.skills);p.interests=", ".join(x.interests);s.commit();s.refresh(p);return prof(p)
@app.get("/api/recommendations")
def recommendations(u:User=Depends(role("Student")),s:Session=Depends(db)):
    p=s.scalar(select(SkillProfile).where(SkillProfile.owner_id==u.id)); profile=prof(p) if p else {"skills":[],"technical_score":0,"soft_score":0}
    out=[{**op(o),**score(profile,parts(o.skills))} for o in s.scalars(select(Opportunity).where(Opportunity.status!="Closed")).all()]
    return sorted(out,key=lambda x:(x["match"],x["skill_coverage"]),reverse=True)

@app.post("/api/applications",status_code=201)
def apply(x:ApplicationIn,u:User=Depends(role("Student")),s:Session=Depends(db)):
    o=s.get(Opportunity,x.opportunity_id)
    if not o or o.status=="Closed": raise HTTPException(404,"Opportunity not available")
    if s.scalar(select(Application).where(Application.student_id==u.id,Application.opportunity_id==o.id)): raise HTTPException(409,"Already applied")
    a=Application(student_id=u.id,opportunity_id=o.id);s.add(a);s.commit();s.refresh(a);return {"id":a.id,"status":a.status,"opportunity":op(o)}
@app.get("/api/applications/me")
def applications_me(u:User=Depends(role("Student")),s:Session=Depends(db)):
    rows=s.scalars(select(Application).where(Application.student_id==u.id).order_by(Application.id.desc())).all()
    return [{"id":a.id,"status":a.status,"created_at":a.created_at,"opportunity":op(s.get(Opportunity,a.opportunity_id))} for a in rows]
@app.patch("/api/applications/{aid}/status")
def application_status(aid:int,status:str,u:User=Depends(role("Industry")),s:Session=Depends(db)):
    a=s.get(Application,aid);o=s.get(Opportunity,a.opportunity_id) if a else None
    if not a or not o or o.owner_id!=u.id: raise HTTPException(404,"Application not found")
    if status not in {"Under Review","Shortlisted","Interview","Selected","Rejected"}: raise HTTPException(400,"Invalid status")
    a.status=status;s.commit();return {"id":a.id,"status":a.status}

@app.get("/api/candidates/{oid}")
def candidates(oid:int,u:User=Depends(role("Industry")),s:Session=Depends(db)):
    o=s.get(Opportunity,oid)
    if not o or o.owner_id not in (0,u.id): raise HTTPException(404,"Opportunity not found")
    out=[]
    for st in s.scalars(select(User).where(User.role=="Student")).all():
        p=s.scalar(select(SkillProfile).where(SkillProfile.owner_id==st.id))
        if p: out.append({"student":st.name,"student_id":st.id,**score(prof(p),parts(o.skills))})
    return sorted(out,key=lambda x:x["match"],reverse=True)

@app.get("/api/learning")
def learning(s:Session=Depends(db)):
    return [{"id":x.id,"title":x.title,"kind":x.kind,"provider":x.provider,"skills":parts(x.skills)} for x in s.scalars(select(LearningItem)).all()]
@app.post("/api/learning/{item_id}/enroll")
def enroll(item_id:int,u:User=Depends(role("Student")),s:Session=Depends(db)):
    if not s.get(LearningItem,item_id): raise HTTPException(404,"Learning item not found")
    if s.scalar(select(Enrollment).where(Enrollment.user_id==u.id,Enrollment.item_id==item_id)): raise HTTPException(409,"Already enrolled")
    s.add(Enrollment(user_id=u.id,item_id=item_id));s.commit();return {"ok":True,"progress":0}
@app.get("/api/learning/me")
def learning_me(u:User=Depends(role("Student")),s:Session=Depends(db)):
    rows=s.scalars(select(Enrollment).where(Enrollment.user_id==u.id)).all()
    return [{"id":e.id,"progress":e.progress,"status":e.status,"item":{"id":i.id,"title":i.title,"kind":i.kind,"provider":i.provider} if (i:=s.get(LearningItem,e.item_id)) else None} for e in rows]
@app.patch("/api/learning/{eid}")
def learning_progress(eid:int,x:ProgressIn,u:User=Depends(role("Student")),s:Session=Depends(db)):
    e=s.get(Enrollment,eid)
    if not e or e.user_id!=u.id: raise HTTPException(404,"Enrollment not found")
    e.progress=x.progress;e.status="Completed" if x.progress==100 else "In Progress";s.commit();return {"id":e.id,"progress":e.progress,"status":e.status}

@app.get("/api/portfolio")
def portfolio(u:User=Depends(role("Student")),s:Session=Depends(db)):
    return [{"id":x.id,"title":x.title,"kind":x.kind,"description":x.description,"skills":parts(x.skills),"verified":x.verified} for x in s.scalars(select(PortfolioItem).where(PortfolioItem.user_id==u.id)).all()]
@app.post("/api/portfolio",status_code=201)
def add_portfolio(x:PortfolioIn,u:User=Depends(role("Student")),s:Session=Depends(db)):
    p=PortfolioItem(user_id=u.id,title=x.title,kind=x.kind,description=x.description,skills=", ".join(x.skills));s.add(p);s.commit();s.refresh(p);return {"id":p.id,"title":p.title,"kind":p.kind,"description":p.description,"skills":parts(p.skills),"verified":p.verified}

@app.get("/api/collaborations")
def collaborations(role_name:Optional[str]=None,s:Session=Depends(db)):
    return [{"id":x.id,"title":x.title,"kind":x.kind,"provider":x.provider,"description":x.description,"target_role":x.target_role,"status":x.status} for x in s.scalars(select(Collaboration)).all() if not role_name or x.target_role in (role_name,"All")]
@app.post("/api/collaborations",status_code=201)
def add_collab(x:CollaborationIn,u:User=Depends(role("Academician","Industry")),s:Session=Depends(db)):
    c=Collaboration(title=x.title,kind=x.kind,provider=x.provider or u.organization or u.name,description=x.description,target_role=x.target_role);s.add(c);s.commit();s.refresh(c);return {"id":c.id,"title":c.title,"kind":c.kind,"provider":c.provider,"description":c.description,"target_role":c.target_role,"status":c.status}

@app.get("/api/analytics")
def analytics(u:User=Depends(role("Institution")),s:Session=Depends(db)):
    students=s.scalar(select(func.count(User.id)).where(User.role=="Student")) or 0; profiles=s.scalar(select(func.count(SkillProfile.id))) or 0; opportunities=s.scalar(select(func.count(Opportunity.id)).where(Opportunity.status!="Closed")) or 0; apps=s.scalar(select(func.count(Application.id))) or 0; selected=s.scalar(select(func.count(Application.id)).where(Application.status=="Selected")) or 0
    supply={};demand={}
    for p in s.scalars(select(SkillProfile)).all():
        for k in parts(p.skills): supply[k]=supply.get(k,0)+1
    for o in s.scalars(select(Opportunity)).all():
        for k in parts(o.skills): demand[k]=demand.get(k,0)+1
    return {"students":students,"profiles":profiles,"profile_completion":round(profiles/students*100) if students else 0,"open_opportunities":opportunities,"applications":apps,"selected":selected,"top_student_skills":sorted(supply.items(),key=lambda x:x[1],reverse=True)[:8],"industry_demand":sorted(demand.items(),key=lambda x:x[1],reverse=True)[:8]}
@app.get("/api/institution/reports")
def reports(u:User=Depends(role("Institution")),s:Session=Depends(db)): return {"generated_at":datetime.now(timezone.utc).isoformat(),"metrics":analytics(u,s)}

@app.post("/api/seed")
def seed(s:Session=Depends(db)):
    if not s.scalar(select(Opportunity)):
        for x in [("Software Engineering Internship","Internship","Tech Partner","Hybrid",["Python","Git","Data Structures"]),("AI/ML Live Project","Project","AI Lab Partner","Remote",["Python","NumPy","Pandas","Machine Learning"]),("Faculty Industry Training","Training","Industry Partner","Online",["Domain Expertise","Communication"]),("Campus Skill Gap Program","Training","Industry Partner","Hybrid",["Programming","Communication"])]:
            s.add(Opportunity(title=x[0],type=x[1],provider=x[2],location=x[3],skills=", ".join(x[4]),description="Industry-aligned opportunity for SkillBridge participants."))
    if not s.scalar(select(LearningItem)):
        for x in [("Python for Data Analysis","Course",["Python","Pandas","NumPy"]),("Practical Machine Learning","Course",["Machine Learning","Python"]),("Communication for Engineers","Workshop",["Communication"])]:
            s.add(LearningItem(title=x[0],kind=x[1],provider="SkillBridge Academy",skills=", ".join(x[2])))
    if not s.scalar(select(Collaboration)):
        for x in [("Industry Internships","Internship","Industry Network","Find structured internship opportunities.","Student"),("Live Industry Projects","Project","Industry Network","Work on real problem statements.","Student"),("Faculty FDP & Training","FDP","Industry Network","Industry-oriented faculty development.","Academician"),("Research Collaboration","Research","Innovation Network","Connect institutions and industry around research.","Academician"),("Innovation Challenges","Challenge","Industry Network","Solve real-world challenges.","All")]:
            s.add(Collaboration(title=x[0],kind=x[1],provider=x[2],description=x[3],target_role=x[4]))
    s.commit();return {"ok":True}


# Seed the demo environment automatically after the module is fully loaded.
# This keeps a fresh prototype deployment immediately usable while preserving
# any existing data.
try:
    with SessionLocal() as _startup_session:
        seed(_startup_session)
except Exception as _seed_error:
    print(f"Startup seed skipped: {_seed_error}")
