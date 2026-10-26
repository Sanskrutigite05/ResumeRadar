"""Word lists the rules use. Plain data, easy to read and extend."""

SECTION_ALIASES = {
    "summary": ["summary", "professional summary", "career summary", "profile", "professional profile",
                "objective", "career objective", "about me", "about"],
    "education": ["education", "academic background", "academics", "academic qualifications",
                  "qualifications", "education & training", "education and training"],
    "experience": ["experience", "work experience", "professional experience", "employment",
                   "employment history", "work history", "internships", "internship",
                   "internship experience", "career history", "industry experience"],
    "projects": ["projects", "academic projects", "personal projects", "key projects",
                 "project work", "selected projects", "technical projects"],
    "skills": ["skills", "technical skills", "key skills", "core competencies", "technologies",
               "tech stack", "skills & tools", "skills and tools", "tools & technologies",
               "technical proficiency", "skills & technologies"],
    "certifications": ["certifications", "certificates", "licenses", "courses", "training"],
    "achievements": ["achievements", "awards", "honors", "honours", "accomplishments",
                     "extracurricular", "extracurricular activities", "activities", "leadership",
                     "positions of responsibility", "awards & achievements"],
    "other": ["languages", "interests", "hobbies", "references", "publications", "declaration"],
}

BULLET_CHARS = "•●▪■◦○➢➤►▶‣⁃-–—*·"

ACTION_VERBS = set("""
accelerated achieved acquired adapted administered advised analysed analyzed announced applied appointed
architected assembled assessed audited authored automated boosted brought budgeted built calculated
captured chaired championed clarified coached collaborated collected communicated compiled completed
composed conceived conducted configured consolidated constructed consulted continued contributed
controlled converted coordinated created cut debugged decreased defined delegated delivered demonstrated
deployed designed detected developed devised diagnosed directed discovered documented doubled drafted
drove earned edited educated eliminated enabled encouraged engineered enhanced ensured established
estimated evaluated examined executed expanded expedited explained extracted facilitated finalized
fixed forecasted formulated founded generated guided handled headed identified implemented improved
increased influenced informed initiated innovated inspected installed integrated interpreted interviewed
introduced invented investigated launched led leveraged maintained managed mapped marketed mentored
migrated minimized modeled modelled modernized monitored motivated negotiated operated optimized
orchestrated organized oversaw owned partnered performed pioneered planned presented prioritized
processed produced programmed promoted proposed prototyped provided published raised ran rebuilt
recommended reconciled recorded recruited redesigned reduced refactored refined rehabilitated released
remodeled reorganized replaced reported researched resolved restructured retrieved reviewed revised
revitalized saved scaled scheduled scripted secured selected served shaped shipped simplified simulated
solved sourced spearheaded standardized streamlined strengthened structured supervised supported
surpassed synthesized systematized tailored taught tested tracked trained transformed translated
troubleshot tuned uncovered unified updated upgraded used utilized validated visualized won wrote
""".split())

# weak opening phrase -> a stronger verb to try instead
WEAK_STARTS = {
    "responsible for": "Led",
    "worked on": "Developed",
    "worked with": "Collaborated with",
    "helped": "Supported",
    "helped with": "Supported",
    "assisted with": "Supported",
    "assisted in": "Supported",
    "involved in": "Contributed to",
    "participated in": "Contributed to",
    "duties included": "Delivered",
    "tasked with": "Delivered",
    "in charge of": "Managed",
    "was responsible for": "Led",
    "did ": "Completed ",
    "made ": "Built ",
}

BUZZWORDS = [
    "hard-working", "hardworking", "hard working", "team player", "self-motivated", "self motivated",
    "detail-oriented", "detail oriented", "go-getter", "results-oriented", "results oriented",
    "dynamic", "synergy", "passionate", "think outside the box", "quick learner", "fast learner",
    "excellent communication skills", "good communication skills", "people person", "motivated individual",
    "seeking a challenging", "challenging position", "best of my knowledge", "highly motivated",
]

UNPROFESSIONAL_EMAIL_WORDS = ["cool", "sexy", "baby", "hot", "cute", "lover", "king", "queen", "dude",
                              "boss", "killer", "rockstar", "swag", "bad", "angel", "devil"]

STOPWORDS = set("""
a about above after again all also am an and any are as at be because been before being below between both
but by can could did do does doing down during each few for from further had has have having he her here
hers him his how i if in into is it its just me more most my no nor not now of off on once only or other
our out over own same she should so some such than that the their them then there these they this those
through to too under until up us very was we were what when where which while who whom why will with would
you your etc per via able ability strong good great excellent including include includes within across
required preferred plus must looking join team role work working experience years year candidate position
responsibilities requirements qualifications job company opportunity ideal skills knowledge understanding
using use used new well will etc based related relevant like get make data business team teams
""".split())

# canonical skill -> list of ways people write it (all lowercase). The canonical name is also matched.
SKILLS = {
    "languages": {
        "python": [], "java": [], "javascript": ["js", "ecmascript"], "typescript": ["ts"],
        "c++": ["cpp"], "c#": ["csharp"], "go": ["golang"], "rust": [], "kotlin": [], "swift": [],
        "php": [], "ruby": [], "scala": [], "dart": [], "matlab": [], "sql": [], "bash": ["shell scripting", "shell"],
        "html": ["html5"], "css": ["css3"], "r": [], "c": [],
    },
    "web": {
        "react": ["react.js", "reactjs"], "angular": ["angularjs"], "vue": ["vue.js", "vuejs"],
        "node.js": ["nodejs", "node"], "express": ["express.js", "expressjs"], "django": [], "flask": [],
        "fastapi": [], "spring boot": ["springboot", "spring"], "next.js": ["nextjs"], "tailwind": ["tailwind css"],
        "bootstrap": [], "rest api": ["rest apis", "restful", "rest", "restful api", "restful apis"],
        "graphql": [], "flutter": [], "android": [], "jquery": [], "redux": [], "figma": [],
    },
    "data & ai": {
        "machine learning": ["ml"], "deep learning": ["dl"], "nlp": ["natural language processing"],
        "computer vision": ["opencv"], "tensorflow": [], "pytorch": [], "keras": [], "scikit-learn": ["sklearn", "scikit learn"],
        "pandas": [], "numpy": [], "matplotlib": [], "seaborn": [], "power bi": ["powerbi"], "tableau": [],
        "excel": ["ms excel", "microsoft excel"], "data analysis": ["data analytics", "analytics"],
        "data visualization": ["data visualisation"], "statistics": ["statistical analysis"],
        "spark": ["pyspark", "apache spark"], "hadoop": [], "airflow": [], "etl": [], "llm": ["large language models", "llms"],
        "rag": ["retrieval augmented generation", "retrieval-augmented generation"], "generative ai": ["genai"],
    },
    "databases": {
        "mysql": [], "postgresql": ["postgres"], "mongodb": ["mongo"], "sqlite": [], "oracle": [],
        "redis": [], "firebase": [], "dynamodb": [], "elasticsearch": [], "nosql": [],
    },
    "cloud & devops": {
        "aws": ["amazon web services"], "azure": [], "gcp": ["google cloud"], "docker": [], "kubernetes": ["k8s"],
        "git": [], "github": [], "gitlab": [], "ci/cd": ["cicd", "ci cd", "jenkins", "github actions"],
        "linux": [], "terraform": [], "ansible": [], "nginx": [], "microservices": [],
    },
    "core cs": {
        "data structures": ["dsa", "data structures and algorithms", "algorithms"], "oop": ["object oriented programming", "object-oriented programming", "object oriented"],
        "dbms": ["database management", "database design"], "operating systems": [], "computer networks": ["networking"],
        "system design": [], "unit testing": ["junit", "pytest", "testing"], "agile": ["scrum"], "api": ["apis"],
        "ui/ux": ["ux design", "ui design", "user experience", "ui ux"], "cybersecurity": ["information security", "security"],
        "iot": ["internet of things"], "embedded systems": ["embedded"], "ar/vr": ["augmented reality", "virtual reality", "unity"],
    },
    "soft skills": {
        "leadership": [], "communication": [], "teamwork": ["collaboration"], "problem solving": ["problem-solving"],
        "project management": [], "time management": [], "presentation": ["public speaking"],
        "critical thinking": [], "mentoring": [],
    },
}
