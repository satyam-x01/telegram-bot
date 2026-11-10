"""
Study Mode Data Catalog
Contains syllabus, subjects, authentic chapter lists, and exam metadata
for Maharashtra State Board, CBSE, ICSE, and Competitive Exams (JEE, NEET, etc.)
"""

EXAMS_CATALOG = {
    "jee_mains": {
        "name": "🎯 JEE Mains",
        "full_name": "Joint Entrance Examination (Main)",
        "conducted_by": "National Testing Agency (NTA)",
        "level": "National (Engineering)",
        "subjects": ["Physics", "Chemistry", "Mathematics"],
        "top_websites": [
            {"name": "NTA Official Portal", "url": "https://jeemain.nta.nic.in"},
            {"name": "Physics Wallah", "url": "https://www.pw.live"},
            {"name": "MathonGo (JEE Prep)", "url": "https://www.mathongo.com"},
            {"name": "Embibe JEE Practice", "url": "https://www.embibe.com"},
            {"name": "Marks App (PYQs by MathonGo)", "url": "https://web.getmarks.app"}
        ],
        "top_apps": ["Marks App (PYQs)", "Physics Wallah", "Unacademy", "Allen Test MyPrep"],
        "high_yield_topics": {
            "Physics": "Modern Physics, Current Electricity, Optics, Thermodynamics, Electrostatics",
            "Chemistry": "Coordination Compounds, Chemical Bonding, GOC & Hydrocarbons, Solutions, Thermodynamics",
            "Mathematics": "3D Geometry & Vectors, Definite Integration, Matrices & Determinants, Coordinate Geometry, Sequences & Series"
        },
        "description": "National entrance exam for admission into NITs, IIITs, CFTIs, and qualifying test for JEE Advanced."
    },
    "jee_adv": {
        "name": "🚀 JEE Advanced",
        "full_name": "Joint Entrance Examination (Advanced)",
        "conducted_by": "IITs (Rotating)",
        "level": "National (IIT Admissions)",
        "subjects": ["Physics", "Chemistry", "Mathematics"],
        "top_websites": [
            {"name": "JEE Advanced Official", "url": "https://jeeadv.ac.in"},
            {"name": "Physics Galaxy by Ashish Arora", "url": "https://www.physicsgalaxy.com"},
            {"name": "Mohit Tyagi (Competishun)", "url": "https://www.youtube.com/@MohitTyagi"},
            {"name": "IIT Bombay Research Notes", "url": "https://www.iitb.ac.in"}
        ],
        "top_apps": ["Physics Galaxy", "Competishun App", "Allen Digital"],
        "high_yield_topics": {
            "Physics": "Rotational Dynamics, Electromagnetism, Wave Optics, Advanced Thermodynamics",
            "Chemistry": "Organic Reaction Mechanisms, Qualitative Analysis, Chemical Equilibrium, Electrochemistry",
            "Mathematics": "Calculus (Definite Integrals & Diff Eq), Probability & Combinatorics, Complex Numbers, Conic Sections"
        },
        "description": "The premier exam for undergraduate admissions to all 23 Indian Institutes of Technology (IITs)."
    },
    "neet": {
        "name": "🩺 NEET UG",
        "full_name": "National Eligibility cum Entrance Test (Undergraduate)",
        "conducted_by": "National Testing Agency (NTA)",
        "level": "National (Medical - MBBS/BDS)",
        "subjects": ["Biology (Botany & Zoology)", "Physics", "Chemistry"],
        "top_websites": [
            {"name": "NEET NTA Official", "url": "https://neet.nta.nic.in"},
            {"name": "Physics Wallah Medical", "url": "https://www.pw.live/neet"},
            {"name": "NCERT Biology Online", "url": "https://ncert.nic.in"},
            {"name": "Darwin NEET Prep App", "url": "https://darwin.app"}
        ],
        "top_apps": ["Darwin NEET Prep", "NEETPrep App", "PW App", "Unacademy NEET"],
        "high_yield_topics": {
            "Biology": "Genetics & Evolution, Human Physiology, Ecology, Cell Structure & Function, Plant Physiology",
            "Physics": "Modern Physics, Current Electricity, Semi-conductors, Dual Nature of Matter",
            "Chemistry": "Biomolecules, Hydrocarbons, Chemical Bonding, Equilibrium, Electrochemistry"
        },
        "description": "Sole national medical entrance examination for MBBS, BDS, AYUSH, and veterinary programs across India."
    },
    "mht_cet": {
        "name": "⚡ MHT-CET",
        "full_name": "Maharashtra Common Entrance Test (PCM & PCB)",
        "conducted_by": "State Common Entrance Test Cell, Maharashtra",
        "level": "State Level (Maharashtra Engineering & Pharmacy)",
        "subjects": ["Mathematics / Biology", "Physics", "Chemistry"],
        "top_websites": [
            {"name": "Mahacet Official", "url": "https://cetcell.mahacet.org"},
            {"name": "Dinesh Sir (Maths)", "url": "https://www.youtube.com/@DineshSir"},
            {"name": "Mukesh Nayak (Physics)", "url": "https://www.youtube.com/@PhysicsGyaanMukeshNayak"},
            {"name": "Sovind Sir (Chemistry)", "url": "https://www.youtube.com/@ChemistrybySovindSir"}
        ],
        "top_apps": ["Dinesh Sir App", "PGMN App", "Target Publications App"],
        "high_yield_topics": {
            "Mathematics": "Vectors & 3D, Integration & Diff Equations, Matrices, Trigonometric Functions",
            "Physics": "Rotational Dynamics, Oscillations, Current Electricity, Wave Optics",
            "Chemistry": "Solutions, Ionic Equilibria, Coordination Compounds, Halogen Derivatives"
        },
        "description": "Premier Maharashtra entrance test based 80% on Class 12 and 20% on Class 11 Maharashtra State Board syllabus."
    },
    "upsc": {
        "name": "🏛 UPSC Civil Services",
        "full_name": "Union Public Service Commission (IAS / IPS / IFS)",
        "conducted_by": "UPSC",
        "level": "National (Civil Services)",
        "subjects": ["General Studies (Prelims & Mains)", "CSAT", "Essay", "Optional Subject"],
        "top_websites": [
            {"name": "UPSC Official", "url": "https://upsc.gov.in"},
            {"name": "Vision IAS", "url": "https://www.visionias.in"},
            {"name": "InsightsonIndia", "url": "https://www.insightsonindia.com"},
            {"name": "Drishti IAS", "url": "https://www.drishtiias.com"}
        ],
        "top_apps": ["Drishti IAS", "Vision IAS", "ClearIAS"],
        "high_yield_topics": {
            "GS-1": "Indian Heritage & Culture, Modern Indian History, Geography of India & World",
            "GS-2": "Indian Constitution, Governance, Polity, International Relations",
            "GS-3": "Economy, Agriculture, Science & Technology, Environment & Biodiversity, Internal Security"
        },
        "description": "India's premier administrative examination for Indian Administrative Service (IAS), Police (IPS), and Foreign Service (IFS)."
    },
    "nda": {
        "name": "⚔️ NDA / NA",
        "full_name": "National Defence Academy & Naval Academy Exam",
        "conducted_by": "UPSC & Indian Armed Forces",
        "level": "National (Army, Navy, Air Force)",
        "subjects": ["Mathematics (300 Marks)", "General Ability Test (GAT - 600 Marks)"],
        "top_websites": [
            {"name": "UPSC NDA Official", "url": "https://upsc.gov.in"},
            {"name": "Defencemania", "url": "https://defencemania.com"},
            {"name": "Centurion Defence Academy", "url": "https://www.centuriondefenceacademy.com"}
        ],
        "top_apps": ["Testbook", "Unacademy Defence", "Adda247"],
        "high_yield_topics": {
            "Mathematics": "Trigonometry, Matrices & Determinants, Calculus, Probability, Vectors",
            "GAT": "English Vocabulary & Grammar, Indian History, Geography, General Science & Current Affairs"
        },
        "description": "Prestigious exam for young candidates directly after 12th standard to become commissioned officers in Indian Armed Forces."
    },
    "gate": {
        "name": "💻 GATE",
        "full_name": "Graduate Aptitude Test in Engineering",
        "conducted_by": "IISc Bangalore & IITs",
        "level": "National (Postgraduate & PSU Recruitment)",
        "subjects": ["Engineering Mathematics", "General Aptitude", "Core Engineering Branch"],
        "top_websites": [
            {"name": "GATE Official Portal", "url": "https://gate.iitk.ac.in"},
            {"name": "GeeksforGeeks GATE CS", "url": "https://www.geeksforgeeks.org/gate-corner-2"},
            {"name": "Made Easy Publications", "url": "https://www.madeeasy.in"}
        ],
        "top_apps": ["GeeksforGeeks", "Unacademy GATE", "Made Easy Prime"],
        "high_yield_topics": {
            "Core": "Data Structures & Algorithms, OS, DBMS, Computer Networks, Engineering Mathematics",
            "Aptitude": "Verbal Reasoning, Quantitative Aptitude, Spatial Aptitude"
        },
        "description": "Qualifying test for Master's programs (M.Tech/Ph.D.) and lucrative PSU recruitments (ONGC, IOCL, NTPC, BHEL)."
    },
    "cuet": {
        "name": "🎓 CUET UG",
        "full_name": "Common University Entrance Test (Undergraduate)",
        "conducted_by": "National Testing Agency (NTA)",
        "level": "National (Central Universities - DU, BHU, JNU)",
        "subjects": ["Section 1: Languages", "Section 2: Domain Subjects (NCERT)", "Section 3: General Test"],
        "top_websites": [
            {"name": "CUET NTA Official", "url": "https://cuetug.ntaonline.in"},
            {"name": "Adda247 CUET", "url": "https://www.adda247.com/cuet"},
            {"name": "Career Launcher CUET", "url": "https://www.careerlauncher.com/cuet"}
        ],
        "top_apps": ["Adda247", "Testbook", "Dubuddy"],
        "high_yield_topics": {
            "Domain": "NCERT Class 12 Core Syllabus across Humanities, Commerce, and Science",
            "General Test": "General Knowledge, Current Affairs, Numerical Ability, Reasoning"
        },
        "description": "Standardized entrance test for undergraduate admissions in over 250 Central, State, and Private universities."
    }
}


CLASSES_CATALOG = {
    "class_10": {
        "name": "🔟 Class 10 (SSC / 10th Standard)",
        "boards": [
            "msbshse", "cbse", "icse", "upmsp", "bseb", "rbse", "mpbse", "gseb",
            "wbbse", "kseab", "tndge", "apbse", "tsbie", "kbpe", "pseb", "bseh",
            "chse_od", "jac", "cgbse", "seba", "nios"
        ]
    },
    "class_12": {
        "name": "🎓 Class 12 (HSC / 12th Standard)",
        "boards": [
            "msbshse", "cbse", "icse", "upmsp", "bseb", "rbse", "mpbse", "gseb",
            "wbbse", "kseab", "tndge", "apbse", "tsbie", "kbpe", "pseb", "bseh",
            "chse_od", "jac", "cgbse", "seba", "nios"
        ]
    },
    "class_11": {
        "name": "🎒 Class 11 (FYJC / 11th Standard)",
        "boards": [
            "msbshse", "cbse", "icse", "upmsp", "bseb", "rbse", "mpbse", "gseb",
            "wbbse", "kseab", "tndge", "apbse", "tsbie", "kbpe", "pseb", "bseh",
            "chse_od", "jac", "cgbse", "seba", "nios"
        ]
    },
    "class_9": {
        "name": "📖 Class 9 (9th Standard)",
        "boards": [
            "msbshse", "cbse", "icse", "upmsp", "bseb", "rbse", "mpbse", "gseb",
            "wbbse", "kseab", "tndge", "apbse", "tsbie", "kbpe", "pseb", "bseh",
            "chse_od", "jac", "cgbse", "seba", "nios"
        ]
    },
    "class_8": {
        "name": "📚 Class 8 (8th Standard)",
        "boards": [
            "msbshse", "cbse", "icse", "upmsp", "bseb", "rbse", "mpbse", "gseb",
            "wbbse", "kseab", "tndge", "apbse", "tsbie", "kbpe", "pseb", "bseh",
            "chse_od", "jac", "cgbse", "seba", "nios"
        ]
    }
}

BOARDS_CATALOG = {
    "msbshse": {
        "name": "🏛 Maharashtra State Board (Balbharati / SSC / HSC)",
        "short_name": "Maharashtra (Balbharati)",
        "code": "Maharashtra Board"
    },
    "cbse": {
        "name": "📘 CBSE / NCERT (All-India)",
        "short_name": "CBSE / NCERT",
        "code": "CBSE"
    },
    "icse": {
        "name": "📕 ICSE / ISC (CISCE)",
        "short_name": "ICSE / ISC",
        "code": "ICSE"
    },
    "upmsp": {
        "name": "🏛 Uttar Pradesh Board (UPMSP)",
        "short_name": "UP Board (UPMSP)",
        "code": "UP Board"
    },
    "bseb": {
        "name": "🏛 Bihar Board (BSEB Patna)",
        "short_name": "Bihar Board (BSEB)",
        "code": "Bihar Board"
    },
    "rbse": {
        "name": "🏛 Rajasthan Board (RBSE / BSER)",
        "short_name": "Rajasthan (RBSE)",
        "code": "Rajasthan Board"
    },
    "mpbse": {
        "name": "🏛 Madhya Pradesh Board (MPBSE)",
        "short_name": "MP Board (MPBSE)",
        "code": "MP Board"
    },
    "gseb": {
        "name": "🏛 Gujarat Board (GSEB)",
        "short_name": "Gujarat (GSEB)",
        "code": "Gujarat Board"
    },
    "wbbse": {
        "name": "🏛 West Bengal Board (WBBSE / WBCHSE)",
        "short_name": "West Bengal (WBBSE)",
        "code": "West Bengal Board"
    },
    "kseab": {
        "name": "🏛 Karnataka State Board (KSEAB)",
        "short_name": "Karnataka (KSEAB)",
        "code": "Karnataka Board"
    },
    "tndge": {
        "name": "🏛 Tamil Nadu State Board (TNDGE)",
        "short_name": "Tamil Nadu (TNDGE)",
        "code": "Tamil Nadu Board"
    },
    "apbse": {
        "name": "🏛 Andhra Pradesh Board (BSEAP / BIEAP)",
        "short_name": "Andhra Pradesh Board",
        "code": "AP Board"
    },
    "tsbie": {
        "name": "🏛 Telangana Board (TSBIE / BSE)",
        "short_name": "Telangana (TSBIE)",
        "code": "Telangana Board"
    },
    "kbpe": {
        "name": "🏛 Kerala Board (KBPE / DHSE)",
        "short_name": "Kerala (KBPE)",
        "code": "Kerala Board"
    },
    "pseb": {
        "name": "🏛 Punjab School Education Board (PSEB)",
        "short_name": "Punjab (PSEB)",
        "code": "Punjab Board"
    },
    "bseh": {
        "name": "🏛 Haryana Board (BSEH / HBSE)",
        "short_name": "Haryana (BSEH)",
        "code": "Haryana Board"
    },
    "chse_od": {
        "name": "🏛 Odisha Board (BSE Odisha / CHSE)",
        "short_name": "Odisha Board",
        "code": "Odisha Board"
    },
    "jac": {
        "name": "🏛 Jharkhand Academic Council (JAC)",
        "short_name": "Jharkhand (JAC)",
        "code": "Jharkhand Board"
    },
    "cgbse": {
        "name": "🏛 Chhattisgarh Board (CGBSE)",
        "short_name": "Chhattisgarh (CGBSE)",
        "code": "Chhattisgarh Board"
    },
    "seba": {
        "name": "🏛 Assam Board (SEBA / AHSEC)",
        "short_name": "Assam (SEBA)",
        "code": "Assam Board"
    },
    "nios": {
        "name": "🌐 NIOS (Open Schooling)",
        "short_name": "NIOS (Open School)",
        "code": "NIOS"
    }
}


CURRICULUM_DATA = {
    # ─────────────────────────────────────────────────────────────
    # CLASS 10 - MAHARASHTRA STATE BOARD
    # ─────────────────────────────────────────────────────────────
    ("class_10", "msbshse"): {
        "english": {
            "name": "English (Kumarbharati)",
            "chapters": [
                # Unit 1
                "1.1 Where the Mind is Without Fear (Rabindranath Tagore)",
                "1.2 The Thief's Story (Ruskin Bond)",
                "1.3 On Wings of Courage (Air Marshal Arjan Singh)",
                "1.4 All the World's a Stage (William Shakespeare)",
                "1.5 Joan of Arc (George Bernard Shaw)",
                # Unit 2
                "2.1 You Start Dying Slowly... (Pablo Neruda)",
                "2.2 The Boy who Broke the Bank (Ruskin Bond)",
                "2.3 The Twins (Henry Sambrooke Leigh)",
                "2.4 An Epitome of Courage (Stephen Hawking)",
                "2.5 Book Review - Swami and Friends (R. K. Narayan)",
                "2.6 World Heritage (UNESCO Heritage Sites)",
                # Unit 3
                "3.1 If— (Rudyard Kipling)",
                "3.2 A Lesson in Life from a Beggar (Sudha Murty)",
                "3.3 Stopping by Woods on a Snowy Evening (Robert Frost)",
                "3.4 Let's March! (Kailash Satyarthi Nobel Lecture)",
                "3.5 The Science of Executive Communication",
                "3.6 The Alchemy of Nature (Raksha Bharadia)",
                # Unit 4
                "4.1 The World is Mine (Joy Lovelet Crawford)",
                "4.2 Bepin Choudhury's Lapse of Memory (Satyajit Ray)",
                "4.3 O Captain! My Captain! (Walt Whitman)",
                "4.4 Unbeatable Spirit - Mary Kom",
                "4.5 The Concert (Shanta Rao)",
                "4.6 A Brave Heart Dedicated to Science and Humanity"
            ]
        },
        "science_1": {
            "name": "Science & Technology Part 1 (Physics & Chemistry)",
            "chapters": [
                "Chapter 1: Gravitation (Kepler's Laws, Universal Law, Free Fall, Escape Velocity)",
                "Chapter 2: Periodic Classification of Elements (Mendeleev, Modern Periodic Table)",
                "Chapter 3: Chemical Reactions and Equations (Types of Reactions, Redox, Corrosion)",
                "Chapter 4: Effects of Electric Current (Joule's Heating, Magnetic Effects, Motor, Generator)",
                "Chapter 5: Heat (Latent Heat, Anomalous Behavior of Water, Specific Heat Capacity)",
                "Chapter 6: Refraction of Light (Laws of Refraction, Refractive Index, Mirage, Rainbow)",
                "Chapter 7: Lenses (Convex & Concave Lenses, Lens Formula, Power, Human Eye, Defects of Vision)",
                "Chapter 8: Metallurgy (Physical & Chemical Properties of Metals/Non-metals, Extraction, Corrosion)",
                "Chapter 9: Carbon Compounds (Covalent Bonds, Functional Groups, IUPAC Nomenclature, Hydrocarbons)",
                "Chapter 10: Space Missions (Need for Space Missions, Artificial Satellites, Satellite Launch Vehicles)"
            ]
        },
        "science_2": {
            "name": "Science & Technology Part 2 (Biology & Environment)",
            "chapters": [
                "Chapter 1: Heredity and Evolution (Transcription, Translation, Darwin's Theory, Human Evolution)",
                "Chapter 2: Life Processes in Living Organisms Part 1 (Cellular Respiration, Cell Division: Mitosis & Meiosis)",
                "Chapter 3: Life Processes in Living Organisms Part 2 (Asexual & Sexual Reproduction in Plants and Humans)",
                "Chapter 4: Environmental Management (Ecosystem, Environment & Ecosystem Conservation, Biodiversity Hotspots)",
                "Chapter 5: Towards Green Energy (Thermal, Nuclear, Hydroelectric, Solar & Wind Power Generation)",
                "Chapter 6: Animal Classification (Phylum Porifera to Chordata, Modern Classification Criteria)",
                "Chapter 7: Introduction to Microbiology (Applied Microbiology, Industrial Products, Probiotics, Sewage)",
                "Chapter 8: Cell Biology and Biotechnology (Stem Cells, Biotechnology in Agriculture, Medicine, Cloning)",
                "Chapter 9: Social Health (Factors Affecting Social Health, Cybercrimes, Stress Management)",
                "Chapter 10: Disaster Management (First Aid, Mock Drills, Disaster Preparedness, Types of Disasters)"
            ]
        },
        "maths_1": {
            "name": "Mathematics Part 1 (Algebra)",
            "chapters": [
                "Chapter 1: Linear Equations in Two Variables (Graphical Method, Cramer's Rule, Word Problems)",
                "Chapter 2: Quadratic Equations (Factorisation, Completing Square, Formula Method, Nature of Roots)",
                "Chapter 3: Arithmetic Progression (nth term of an A.P., Sum of first n terms, Word Problems)",
                "Chapter 4: Financial Planning (GST on Goods & Services, Shares, Face Value, Market Value, Mutual Funds)",
                "Chapter 5: Probability (Random Experiment, Sample Space, Events, Probability of an Event)",
                "Chapter 6: Statistics (Mean, Median, Mode of Grouped Data, Histogram, Frequency Polygon, Pie Chart)"
            ]
        },
        "maths_2": {
            "name": "Mathematics Part 2 (Geometry)",
            "chapters": [
                "Chapter 1: Similarity (Ratio of Areas of Triangles, Basic Proportionality Theorem, Tests of Similarity)",
                "Chapter 2: Pythagoras Theorem (Geometric Mean Theorem, Proof of Pythagoras Theorem, Applications)",
                "Chapter 3: Circle (Tangent Theorem, Inscribed Angle Theorem, Cyclic Quadrilateral, Tangent Secant)",
                "Chapter 4: Geometric Constructions (Construction of Similar Triangles, Tangents to a Circle)",
                "Chapter 5: Co-ordinate Geometry (Distance Formula, Section Formula, Midpoint Formula, Slope of a Line)",
                "Chapter 6: Trigonometry (Trigonometric Ratios, Trigonometric Identities, Heights and Distances Problems)",
                "Chapter 7: Mensuration (Surface Area & Volume of Cylinder, Cone, Sphere, Frustum, Area of Sector)"
            ]
        },
        "history": {
            "name": "History & Political Science",
            "chapters": [
                "History Ch 1: Historiography Development in the West",
                "History Ch 2: Historiography Indian Tradition",
                "History Ch 3: Applied History",
                "History Ch 4: History of Indian Arts",
                "History Ch 5: Mass Media and History",
                "History Ch 6: Entertainment and History",
                "History Ch 7: Sports and History",
                "History Ch 8: Tourism and History",
                "History Ch 9: Heritage Management",
                "Pol Sci Ch 1: Working of the Constitution",
                "Pol Sci Ch 2: The Electoral Process",
                "Pol Sci Ch 3: Political Parties",
                "Pol Sci Ch 4: Social and Political Movements",
                "Pol Sci Ch 5: Challenges faced by Indian Democracy"
            ]
        },
        "geography": {
            "name": "Geography",
            "chapters": [
                "Chapter 1: Field Visit (Preparation, Questionnaire, Report Writing)",
                "Chapter 2: Location and Extent (India and Brazil Comparison)",
                "Chapter 3: Physiography and Drainage (Himalayas, Amazon Basin, Coastal Plains)",
                "Chapter 4: Climate (Monsoon in India, Brazilian Tropical Climate)",
                "Chapter 5: Natural Vegetation and Wildlife (Rainforests, Wildlife Reserves)",
                "Chapter 6: Population (Distribution, Density, Sex Ratio, Literacy)",
                "Chapter 7: Human Settlements (Patterns of Settlements, Urbanisation)",
                "Chapter 8: Economy and Occupations (Agriculture, Fisheries, Mining, Trade)",
                "Chapter 9: Tourism, Transport and Communication (Tourism Potential, Waterways, Internet)"
            ]
        },
        "marathi": {
            "name": "Marathi (Aksharbharati / Kumarbharati)",
            "chapters": [
                "पाठ १: तू बुद्धी दे (प्रार्थना - गुरु ठाकूर)",
                "पाठ २: संतवाणी - अ) अंकिला मी दास तुझा, आ) योगी सर्वकाळ सुखदाता",
                "पाठ ३: शाल (राग जाधव)",
                "पाठ ४: उपास (पु. ल. देशपांडे)",
                "पाठ ५: दोन दिवस (कविता - नारायण सुर्वे)",
                "पाठ ६: चुडीवाला (जयश्री रुईकर)",
                "पाठ ७: फुटप्रिंट्स (डॉ. प्रदीप आवटे)",
                "पाठ ८: ऊर्जाशक्तीचा जागर (डॉ. रघुनाथ माशेलकर)",
                "पाठ ९: आश्वासक चित्र (कविता - नीरजा)",
                "पाठ १०: आप्पांचे पत्र (अरविंद जगताप)",
                "पाठ ११: गोष्ट अरुणिमाची (सुप्रिया जाधव)",
                "पाठ १२: भरतवाक्य (कविता - मोरोपंत)"
            ]
        }
    },

    # ─────────────────────────────────────────────────────────────
    # CLASS 10 - CBSE / NCERT BOARD
    # ─────────────────────────────────────────────────────────────
    ("class_10", "cbse"): {
        "science": {
            "name": "Science (NCERT)",
            "chapters": [
                "Chapter 1: Chemical Reactions and Equations",
                "Chapter 2: Acids, Bases and Salts",
                "Chapter 3: Metals and Non-metals",
                "Chapter 4: Carbon and its Compounds",
                "Chapter 5: Life Processes",
                "Chapter 6: Control and Coordination",
                "Chapter 7: How do Organisms Reproduce?",
                "Chapter 8: Heredity",
                "Chapter 9: Light – Reflection and Refraction",
                "Chapter 10: The Human Eye and the Colourful World",
                "Chapter 11: Electricity",
                "Chapter 12: Magnetic Effects of Electric Current",
                "Chapter 13: Our Environment"
            ]
        },
        "mathematics": {
            "name": "Mathematics (NCERT)",
            "chapters": [
                "Chapter 1: Real Numbers",
                "Chapter 2: Polynomials",
                "Chapter 3: Pair of Linear Equations in Two Variables",
                "Chapter 4: Quadratic Equations",
                "Chapter 5: Arithmetic Progressions",
                "Chapter 6: Triangles",
                "Chapter 7: Coordinate Geometry",
                "Chapter 8: Introduction to Trigonometry",
                "Chapter 9: Some Applications of Trigonometry",
                "Chapter 10: Circles",
                "Chapter 11: Areas Related to Circles",
                "Chapter 12: Surface Areas and Volumes",
                "Chapter 13: Statistics",
                "Chapter 14: Probability"
            ]
        },
        "english": {
            "name": "English (First Flight & Footprints)",
            "chapters": [
                "1. A Letter to God (G. L. Fuentes)",
                "2. Nelson Mandela: Long Walk to Freedom",
                "3. Two Stories about Flying (His First Flight & Black Aeroplane)",
                "4. From the Diary of Anne Frank",
                "5. Glimpses of India (Baker from Goa, Coorg, Tea from Assam)",
                "6. Mijbil the Otter (Gavin Maxwell)",
                "7. Madam Rides the Bus (Vallikkannan)",
                "8. The Sermon at Benares (Gautama Buddha)",
                "9. The Proposal (Anton Chekhov)",
                "Poem: Dust of Snow & Fire and Ice (Robert Frost)",
                "Poem: A Tiger in the Zoo & How to Tell Wild Animals",
                "Poem: The Ball Poem & Amanda!",
                "Footprints: A Triumph of Surgery",
                "Footprints: The Thief's Story",
                "Footprints: The Midnight Visitor",
                "Footprints: A Question of Trust",
                "Footprints: Footprints without Feet",
                "Footprints: The Making of a Scientist",
                "Footprints: The Necklace",
                "Footprints: Bholi",
                "Footprints: The Book that Saved the Earth"
            ]
        },
        "social_science": {
            "name": "Social Science (History, Pol Sci, Geo, Eco)",
            "chapters": [
                "History: The Rise of Nationalism in Europe",
                "History: Nationalism in India",
                "History: The Making of a Global World",
                "History: Print Culture and the Modern World",
                "Geography: Resources and Development",
                "Geography: Forest and Wildlife Resources",
                "Geography: Water Resources",
                "Geography: Agriculture",
                "Geography: Minerals and Energy Resources",
                "Geography: Manufacturing Industries",
                "Geography: Lifelines of National Economy",
                "Pol Sci: Power Sharing",
                "Pol Sci: Federalism",
                "Pol Sci: Gender, Religion and Caste",
                "Pol Sci: Political Parties",
                "Pol Sci: Outcomes of Democracy",
                "Economics: Development",
                "Economics: Sectors of the Indian Economy",
                "Economics: Money and Credit",
                "Economics: Globalisation and the Indian Economy"
            ]
        }
    },

    # ─────────────────────────────────────────────────────────────
    # CLASS 12 - MAHARASHTRA STATE BOARD (HSC)
    # ─────────────────────────────────────────────────────────────
    ("class_12", "msbshse"): {
        "physics": {
            "name": "Physics (HSC)",
            "chapters": [
                "Chapter 1: Rotational Dynamics (Circular Motion, Moment of Inertia, Rolling Motion)",
                "Chapter 2: Mechanical Properties of Fluids (Surface Tension, Viscosity, Bernoulli)",
                "Chapter 3: Kinetic Theory of Gases and Radiation (Blackbody Radiation, Stefan's Law)",
                "Chapter 4: Thermodynamics (First & Second Law, Heat Engine, Refrigerator, Carnot Cycle)",
                "Chapter 5: Oscillations (Simple Harmonic Motion, Differential Equation, Pendulum)",
                "Chapter 6: Superposition of Waves (Stationary Waves, Harmonics, Beats, Organ Pipes)",
                "Chapter 7: Wave Optics (Huygens' Principle, Interference, Young's Experiment, Diffraction)",
                "Chapter 8: Electrostatics (Gauss's Theorem, Electric Potential, Capacitors, Van de Graaff)",
                "Chapter 9: Current Electricity (Kirchhoff's Laws, Wheatstone Bridge, Potentiometer)",
                "Chapter 10: Magnetic Fields due to Electric Current (Biot-Savart Law, Ampere's Law, Solenoid)",
                "Chapter 11: Magnetic Materials (Diamagnetism, Paramagnetism, Ferromagnetism, Hysteresis)",
                "Chapter 12: Electromagnetic Induction (Faraday's Laws, Lenz's Law, Eddy Currents, AC Generator)",
                "Chapter 13: AC Circuits (LCR Series Circuit, Phasor Diagrams, Resonance, Power in AC)",
                "Chapter 14: Dual Nature of Radiation and Matter (Photoelectric Effect, De Broglie Hypothesis)",
                "Chapter 15: Structure of Atoms and Nuclei (Bohr Model, Radioactivity, Half-life, Nuclear Energy)",
                "Chapter 16: Semiconductor Devices (p-n Junction Diode, Zener Diode, Solar Cell, Logic Gates)"
            ]
        },
        "chemistry": {
            "name": "Chemistry (HSC)",
            "chapters": [
                "Chapter 1: Solid State (Crystalline Solids, Unit Cells, Packing Efficiency, Defects)",
                "Chapter 2: Solutions (Raoult's Law, Colligative Properties, Van't Hoff Factor)",
                "Chapter 3: Ionic Equilibria (Acids & Bases, pH, Buffer Solutions, Solubility Product)",
                "Chapter 4: Chemical Thermodynamics (Enthalpy, Hess's Law, Entropy, Gibbs Free Energy)",
                "Chapter 5: Electrochemistry (Kohlrausch's Law, Nernst Equation, Galvanic Cells, Fuel Cells)",
                "Chapter 6: Chemical Kinetics (Rate Law, Integrated Rate Equations, Arrhenius Equation)",
                "Chapter 7: Elements of Groups 16, 17 and 18 (Hydrides, Oxides, Interhalogen Compounds)",
                "Chapter 8: Transition and Inner Transition Elements (d and f Block, Lanthanoid Contraction)",
                "Chapter 9: Coordination Compounds (Werner's Theory, Valence Bond Theory, Crystal Field Theory)",
                "Chapter 10: Halogen Derivatives (SN1 and SN2 Mechanisms, Haloarenes, Grignard Reagent)",
                "Chapter 11: Alcohols, Phenols and Ethers (Preparation, Acidity, Kolbe & Reimer-Tiemann)",
                "Chapter 12: Aldehydes, Ketones and Carboxylic Acids (Aldol, Cannizzaro, Nucleophilic Addition)",
                "Chapter 13: Amines (Diazonium Salts, Gabriel Phthalimide Synthesis, Carbylamine Test)",
                "Chapter 14: Biomolecules (Carbohydrates, Amino Acids, Proteins, DNA/RNA)",
                "Chapter 15: Introduction to Polymer Chemistry (Addition & Condensation Polymers, Biodegradable)",
                "Chapter 16: Green Chemistry and Nanochemistry (12 Principles of Green Chemistry, Nanoparticles)"
            ]
        },
        "mathematics": {
            "name": "Mathematics & Statistics (HSC)",
            "chapters": [
                "Part 1 Ch 1: Mathematical Logic (Truth Tables, Quantifiers, Circuit Applications)",
                "Part 1 Ch 2: Matrices (Inverse of Matrix, Adjoint, Method of Inversion & Reduction)",
                "Part 1 Ch 3: Trigonometric Functions (General Solutions, Polar Coordinates, Sine/Cosine Rule)",
                "Part 1 Ch 4: Pair of Straight Lines (Homogeneous Equations, Angle between Lines)",
                "Part 1 Ch 5: Vectors (Dot and Cross Product, Triple Products, Direction Cosines)",
                "Part 1 Ch 6: Line and Plane (Vector & Cartesian Equations, Shortest Distance)",
                "Part 1 Ch 7: Linear Programming (LPP Formulation, Graphical Method)",
                "Part 2 Ch 1: Differentiation (Chain Rule, Derivatives of Inverse, Parametric, Higher Order)",
                "Part 2 Ch 2: Applications of Derivatives (Tangents & Normals, Rate Measure, Maxima & Minima)",
                "Part 2 Ch 3: Indefinite Integration (Standard Integrals, Substitution, By Parts, Partial Fractions)",
                "Part 2 Ch 4: Definite Integration (Fundamental Theorem, Properties of Definite Integrals)",
                "Part 2 Ch 5: Application of Definite Integration (Area under Curve, Area between Two Curves)",
                "Part 2 Ch 6: Differential Equations (Formation, Variable Separable, Homogeneous, Linear Diff Eq)",
                "Part 2 Ch 7: Probability Distributions (Random Variables, PMF, PDF, Expected Value)",
                "Part 2 Ch 8: Binomial Distribution (Bernoulli Trials, Mean and Variance)"
            ]
        },
        "biology": {
            "name": "Biology (HSC)",
            "chapters": [
                "Chapter 1: Reproduction in Lower and Higher Plants (Microsporogenesis, Double Fertilization)",
                "Chapter 2: Reproduction in Lower and Higher Animals (Human Reproductive System, Menstrual Cycle)",
                "Chapter 3: Inheritance and Variation (Mendelian Genetics, Gene Interaction, Sex-linked Inheritance)",
                "Chapter 4: Molecular Basis of Inheritance (DNA Structure, Replication, Genetic Code, Operon Model)",
                "Chapter 5: Origin and Evolution of Life (Organic Evolution, Modern Synthetic Theory, Hardy-Weinberg)",
                "Chapter 6: Plant Water Relation (Absorption, Translocation, Transpiration)",
                "Chapter 7: Plant Growth and Mineral Nutrition (Phytohormones: Auxin, Gibberellin, Cytokinin)",
                "Chapter 8: Respiration and Circulation (Internal & External Respiration, Heart Structure, ECG, Blood)",
                "Chapter 9: Control and Co-ordination (Nervous System, Endocrine Glands, Hormonal Disorders)",
                "Chapter 10: Human Health and Diseases (Immunity, Vaccines, Cancer, AIDS, Mental Health)",
                "Chapter 11: Enhancement of Food Production (Plant Breeding, Tissue Culture, Animal Husbandry)",
                "Chapter 12: Biotechnology (Recombinant DNA Technology, PCR, Applications in Agriculture & Medicine)",
                "Chapter 13: Organisms and Populations (Adaptations, Population Attributes, Interactions)",
                "Chapter 14: Ecosystems and Energy Flow (Ecological Pyramids, Nutrient Cycles, Succession)",
                "Chapter 15: Biodiversity, Conservation and Environmental Issues (Conservation Strategies, Pollution)"
            ]
        },
        "english": {
            "name": "English (Yuvakbharati)",
            "chapters": [
                "1.1 An Astrologer's Day (R. K. Narayan)",
                "1.2 On Saying “Please” (A. G. Gardiner)",
                "1.3 The Cop and the Anthem (O. Henry)",
                "1.4 Big Data-Big Insights",
                "1.5 The New Dress (Virginia Woolf)",
                "1.6 Into the Wild (Kiran Purandare)",
                "1.7 Why We Travel (Pico Iyer)",
                "1.8 Voyaging Towards Excellence (Achyut Godbole)",
                "2.1 Song of the Open Road (Walt Whitman)",
                "2.2 Indian Weavers (Sarojini Naidu)",
                "2.3 The Inchcape Rock (Robert Southey)",
                "2.4 Have you Earned your Tomorrow (Edgar Guest)",
                "2.5 Father Returning Home (Dilip Chitre)",
                "2.6 Money (William H. Davies)",
                "2.7 She Walks in Beauty (Lord Byron)",
                "2.8 Small Towns and Rivers (Mamang Dai)",
                "3.1 Summary Writing & Do School",
                "3.2 Mind Mapping & Statement of Purpose (SOP)",
                "4.1 History of English Novel",
                "4.2 To Sir, with Love (E. R. Braithwaite)",
                "4.3 Around the World in Eighty Days (Jules Verne)",
                "4.4 The Sign of Four (Sir Arthur Conan Doyle)"
            ]
        }
    },

    # ─────────────────────────────────────────────────────────────
    # CLASS 12 - CBSE / NCERT BOARD
    # ─────────────────────────────────────────────────────────────
    ("class_12", "cbse"): {
        "physics": {
            "name": "Physics (NCERT)",
            "chapters": [
                "Chapter 1: Electric Charges and Fields",
                "Chapter 2: Electrostatic Potential and Capacitance",
                "Chapter 3: Current Electricity",
                "Chapter 4: Moving Charges and Magnetism",
                "Chapter 5: Magnetism and Matter",
                "Chapter 6: Electromagnetic Induction",
                "Chapter 7: Alternating Current",
                "Chapter 8: Electromagnetic Waves",
                "Chapter 9: Ray Optics and Optical Instruments",
                "Chapter 10: Wave Optics",
                "Chapter 11: Dual Nature of Radiation and Matter",
                "Chapter 12: Atoms",
                "Chapter 13: Nuclei",
                "Chapter 14: Semiconductor Electronics: Materials, Devices and Simple Circuits"
            ]
        },
        "chemistry": {
            "name": "Chemistry (NCERT)",
            "chapters": [
                "Chapter 1: Solutions",
                "Chapter 2: Electrochemistry",
                "Chapter 3: Chemical Kinetics",
                "Chapter 4: The d- and f- Block Elements",
                "Chapter 5: Coordination Compounds",
                "Chapter 6: Haloalkanes and Haloarenes",
                "Chapter 7: Alcohols, Phenols and Ethers",
                "Chapter 8: Aldehydes, Ketones and Carboxylic Acids",
                "Chapter 9: Amines",
                "Chapter 10: Biomolecules"
            ]
        },
        "mathematics": {
            "name": "Mathematics (NCERT)",
            "chapters": [
                "Chapter 1: Relations and Functions",
                "Chapter 2: Inverse Trigonometric Functions",
                "Chapter 3: Matrices",
                "Chapter 4: Determinants",
                "Chapter 5: Continuity and Differentiability",
                "Chapter 6: Application of Derivatives",
                "Chapter 7: Integrals",
                "Chapter 8: Application of Integrals",
                "Chapter 9: Differential Equations",
                "Chapter 10: Vector Algebra",
                "Chapter 11: Three Dimensional Geometry",
                "Chapter 12: Linear Programming",
                "Chapter 13: Probability"
            ]
        },
        "biology": {
            "name": "Biology (NCERT)",
            "chapters": [
                "Chapter 1: Sexual Reproduction in Flowering Plants",
                "Chapter 2: Human Reproduction",
                "Chapter 3: Reproductive Health",
                "Chapter 4: Principles of Inheritance and Variation",
                "Chapter 5: Molecular Basis of Inheritance",
                "Chapter 6: Evolution",
                "Chapter 7: Human Health and Disease",
                "Chapter 8: Microbes in Human Welfare",
                "Chapter 9: Biotechnology: Principles and Processes",
                "Chapter 10: Biotechnology and its Applications",
                "Chapter 11: Organisms and Populations",
                "Chapter 12: Ecosystem",
                "Chapter 13: Biodiversity and Conservation"
            ]
        }
    }
}


def get_all_exams():
    """Returns all supported competitive exams."""
    return EXAMS_CATALOG


def get_exam_details(exam_id: str):
    """Get complete details for a competitive exam."""
    return EXAMS_CATALOG.get(exam_id)


def get_classes():
    """Get all supported school / college classes."""
    return CLASSES_CATALOG


def get_boards_for_class(class_id: str):
    """Get supported boards for a specific class."""
    class_info = CLASSES_CATALOG.get(class_id)
    if not class_info:
        return []
    boards = []
    for b_code in class_info["boards"]:
        if b_code in BOARDS_CATALOG:
            boards.append({
                "code": b_code,
                "name": BOARDS_CATALOG[b_code]["name"]
            })
    return boards


def get_subjects(class_id: str, board_id: str):
    """Get subjects for a specific class and board with smart NCERT / State standard fallback."""
    data = CURRICULUM_DATA.get((class_id, board_id))
    if not data:
        # Most Indian state boards (UP, Bihar, Rajasthan, MP, etc.) use NCERT curriculum for core subjects
        data = CURRICULUM_DATA.get((class_id, "cbse"))
    if not data:
        data = CURRICULUM_DATA.get((class_id, "msbshse"))
    if not data:
        data = CURRICULUM_DATA.get(("class_10", "cbse"), {})
    
    subjects = []
    for subj_code, subj_info in data.items():
        subjects.append({
            "code": subj_code,
            "name": subj_info["name"],
            "chapter_count": len(subj_info["chapters"])
        })
    return subjects


def get_chapters(class_id: str, board_id: str, subject_id: str):
    """Get chapters list for a given class, board, and subject."""
    data = CURRICULUM_DATA.get((class_id, board_id))
    if not data:
        data = CURRICULUM_DATA.get((class_id, "cbse"))
    if not data:
        data = CURRICULUM_DATA.get((class_id, "msbshse"))
    if not data:
        data = CURRICULUM_DATA.get(("class_10", "cbse"), {})
    
    subj_info = data.get(subject_id)
    if not subj_info:
        # Fallback to first available subject
        if data:
            first_key = list(data.keys())[0]
            subj_info = data[first_key]
        else:
            return []
    
    return subj_info.get("chapters", [])

