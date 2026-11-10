from typing import Dict, List, Optional

MUSIC_LANGUAGES = {
    "hindi": {"name": "🇮🇳 Hindi Hits", "flag": "🇮🇳"},
    "punjabi": {"name": "🎶 Punjabi Beats", "flag": "🎶"},
    "english": {"name": "🇬🇧 English & US", "flag": "🇬🇧"},
    "spanish": {"name": "🇲🇽 Spanish & Latin", "flag": "🇲🇽"},
    "kpop": {"name": "🇰🇷 K-Pop Hits", "flag": "🇰🇷"},
    "bhojpuri": {"name": "🎬 Bhojpuri Pop", "flag": "🎬"},
    "haryanvi": {"name": "💥 Haryanvi Hits", "flag": "💥"},
    "tamil": {"name": "⚡ Tamil Hits", "flag": "⚡"},
    "telugu": {"name": "🔥 Telugu Hits", "flag": "🔥"},
    "malayalam": {"name": "🌴 Malayalam Hits", "flag": "🌴"},
    "kannada": {"name": "🎧 Kannada Hits", "flag": "🎧"},
    "marathi": {"name": "🚩 Marathi Hits", "flag": "🚩"},
    "gujarati": {"name": "🕺 Gujarati Hits", "flag": "🕺"},
    "bengali": {"name": "🎨 Bengali Hits", "flag": "🎨"},
    "urdu": {"name": "🌙 Urdu & Ghazal", "flag": "🌙"},
    "arabic": {"name": "🕌 Arabic Hits", "flag": "🕌"},
    "phonk": {"name": "🏎️ Phonk Tracks", "flag": "🏎️"},
    "beats": {"name": "☕ Chill Beats & Lo-Fi", "flag": "☕"}
}

SINGERS_CATALOG = {
    "hindi": [
        {
            "id": "arijit",
            "name": "Arijit Singh",
            "songs": [
                "Kesariya", "Tum Hi Ho", "Apna Bana Le", "Chaleya", "Agar Tum Saath Ho",
                "Shayad", "O Maahi", "Satranga", "Lutt Putt Gaya", "Heeriye",
                "Tera Yaar Hoon Main", "Khairiyat", "Tujhe Kitna Chahne Lage", "Ae Dil Hai Mushkil", "Ghodey Pe Sawaar"
            ]
        },
        {
            "id": "shreya",
            "name": "Shreya Ghoshal",
            "songs": [
                "Teri Ore", "Param Sundari", "Sunn Raha Hai", "Deewani Mastani", "Ghar More Pardesiya",
                "Thodi Der", "Ve Kamleya", "Zihaal e Miskin", "Chikni Chameli", "Manwa Laage",
                "Pal Pal Dil Ke Paas", "Nagada Sang Dhol", "Bahara", "Saibo", "Samjhawan"
            ]
        },
        {
            "id": "jubin",
            "name": "Jubin Nautiyal",
            "songs": [
                "Raataan Lambiyan", "Lut Gaye", "Zindagi Kuch Toh Bata", "Humnava Mere", "Tum Hi Aana",
                "Kinna Sona", "Tujhe Kitna Chahein Aur", "Mast Nazron Se", "Barsaat Ki Dhun", "Wafa Na Raas Aayee",
                "Taro Ke Shehar", "Kuch Baatein", "Dil Galti Kar Baitha Hai", "Mehabooba", "Dil Pe Zakhm"
            ]
        },
        {
            "id": "neha",
            "name": "Neha Kakkar",
            "songs": [
                "O Saki Saki", "Dilbar", "Kala Chashma", "Garmi", "Mile Ho Tum",
                "Aankh Marey", "Manali Trance", "Nikle Currant", "Coca Cola", "Yaad Piya Ki Aane Lahi",
                "Kar Gayi Chull", "Hauli Hauli", "Badri Ki Dulhania", "Dil Ko Karaar Aaya", "Shona Shona"
            ]
        },
        {
            "id": "badshah",
            "name": "Badshah",
            "songs": [
                "Jugnu", "Soulmate", "Mercy", "Genda Phool", "Paani Paani",
                "Bachpan Ka Pyaar", "DJ Waley Babu", "Garmi", "She Move It Like", "Proper Patola",
                "Sanak", "Gone Girl", "Tauba Tauba", "Voodoo", "Abhi Toh Party Shuru Hui Hai"
            ]
        },
        {
            "id": "sonu",
            "name": "Sonu Nigam",
            "songs": [
                "Kal Ho Naa Ho", "Abhi Mujh Mein Kahin", "Suraj Hua Maddham", "Main Agar Kahoon", "Deewana Main Tera",
                "Soniyo", "Tumse Milke Dil Ka", "Shukran Allah", "Yeh Dil Deewana", "Saathiya",
                "Mere Haath Mein", "Jane Nahi Denge Tujhe", "Sandese Aate Hai", "Do Pal", "Kabhi Alvida Naa Kehna"
            ]
        },
        {
            "id": "kk",
            "name": "KK (Krishnakumar Kunnath)",
            "songs": [
                "Pal", "Yaaron", "Tadap Tadap", "Tu Hi Meri Shab Hai", "Zara Sa",
                "Labon Ko", "Aankhon Mein Teri", "Kya Mujhe Pyar Hai", "Dil Ibaadat", "Khuda Jaane",
                "Alvida", "Beete Lamhein", "Sach Keh Raha Hai Deewana", "O Meri Zohrajabeen", "Tu Jo Mila"
            ]
        },
        {
            "id": "atif",
            "name": "Atif Aslam",
            "songs": [
                "Aadat", "Tere Bin", "Jeene Laga Hoon", "Tu Jaane Na", "Tajdar e Haram", "Dil Diyan Gallan", "Pehli Nazar Mein", "Tera Hone Laga Hoon", "Woh Lamhe", "Mai Rang Sharbaton Ka", "O Saathi", "Be Intehaan"
            ]
        }
    ],
    "punjabi": [
        {
            "id": "sidhu",
            "name": "Sidhu Moose Wala",
            "songs": [
                "295", "The Last Ride", "So High", "Same Beef", "Legend",
                "Levels", "Never Fold", "SYL", "Bambiha Bole", "Dollar",
                "Old Skool", "Tibeyan Da Putt", "Drippy", "Attachment", "Just Listen"
            ]
        },
        {
            "id": "aujla",
            "name": "Karan Aujla",
            "songs": [
                "Softly", "Winning Speech", "Tauba Tauba", "Adhiya", "Mexico",
                "52 Bars", "Admiring You", "Players", "Don't Look", "Chithiyaan",
                "WYTB", "On Top", "Jee Ni Lagda", "Try Me", "White Brown Black"
            ]
        },
        {
            "id": "diljit",
            "name": "Diljit Dosanjh",
            "songs": [
                "Lover", "Naina", "GOAT", "Born To Shine", "Lemonade",
                "Kinni Kinni", "Case", "Hass Hass", "Peaches", "Do You Know",
                "Proper Patola", "Laembadgini", "Vibe", "Clash", "Black & White"
            ]
        },
        {
            "id": "apdhillon",
            "name": "AP Dhillon",
            "songs": [
                "Brown Munde", "Excuses", "With You", "Insane", "Summer High",
                "Desires", "Spaceship", "True Stories", "Dil Nu", "Majhail",
                "Saada Pyaar", "Foreigns", "Wo Noor", "Old Money", "Takeover"
            ]
        },
        {
            "id": "honeysingh",
            "name": "Yo Yo Honey Singh",
            "songs": [
                "Desi Kalakaar", "Blue Eyes", "Love Dose", "Dope Shope", "High Heels",
                "Kuley Kuley", "Kalaastar", "Brown Rang", "Millionaire", "Payal",
                "Lungi Dance", "Breakup Party", "Bring Me Back", "One Bottle Down", "Makhna"
            ]
        }
    ],
    "english": [
        {
            "id": "weeknd",
            "name": "The Weeknd",
            "songs": [
                "Starboy", "Blinding Lights", "Save Your Tears", "Die For You", "The Hills",
                "Can't Feel My Face", "Call Out My Name", "Popular", "Creepin", "Out of Time",
                "I Was Never There", "Stargirl Interlude", "Heartless", "Earned It", "Often"
            ]
        },
        {
            "id": "taylor",
            "name": "Taylor Swift",
            "songs": [
                "Cruel Summer", "Blank Space", "Love Story", "Shake It Off", "Anti Hero",
                "You Belong With Me", "Style", "Cardigan", "Fortnight", "Wildest Dreams",
                "Look What You Made Me Do", "I Knew You Were Trouble", "Don't Blame Me", "Delicate", "Karma"
            ]
        },
        {
            "id": "drake",
            "name": "Drake",
            "songs": [
                "One Dance", "Gods Plan", "Hotline Bling", "Rich Baby Daddy", "In My Feelings",
                "Passionfruit", "First Person Shooter", "Knife Talk", "Nonstop", "Jimmy Cooks",
                "Toosie Slide", "Hold On We're Going Home", "Laugh Now Cry Later", "Fair Trade", "IDGAF"
            ]
        },
        {
            "id": "bieber",
            "name": "Justin Bieber",
            "songs": [
                "Baby", "Stay", "Peaches", "Sorry", "Love Yourself",
                "What Do You Mean", "Intentions", "Ghost", "Yummy", "Boyfriend",
                "Despacito Remix", "As Long As You Love Me", "Beauty and a Beat", "Company", "Hold On"
            ]
        },
        {
            "id": "eminem",
            "name": "Eminem",
            "songs": [
                "Houdini", "Without Me", "Lose Yourself", "Love The Way You Lie", "The Real Slim Shady",
                "Mockingbird", "Venom", "Stan", "Godzilla", "Not Afraid", "Rap God", "Superman", "Till I Collapse", "When I'm Gone", "Smack That"
            ]
        }
    ],
    "spanish": [
        {
            "id": "badbunny",
            "name": "Bad Bunny",
            "songs": [
                "Monaco", "Me Porto Bonito", "Titi Me Pregunto", "Dakiti", "Callaita",
                "La Jumpa", "Un Preview", "Yonaguni", "Mia", "Ojitos Lindos"
            ]
        },
        {
            "id": "shakira",
            "name": "Shakira",
            "songs": [
                "Hips Don't Lie", "Waka Waka", "Bzrp Music Sessions 53", "La Tortura", "Chantaje",
                "Whenever Wherever", "Punteria", "Girl Like Me", "She Wolf", "Loca"
            ]
        },
        {
            "id": "enrique",
            "name": "Enrique Iglesias",
            "songs": [
                "Bailando", "Hero", "El Perdon", "Subeme La Radio", "Duele El Corazon",
                "Tonight I'm Loving You", "I Like It", "Escape", "Ring My Bells", "Loco"
            ]
        },
        {
            "id": "luisfonsi",
            "name": "Luis Fonsi",
            "songs": [
                "Despacito", "Echame La Culpa", "No Me Doy Por Vencido", "Calypso", "Imposible",
                "Date La Vuelta", "Sola", "Llegaste Tu", "Aqui Estoy Yo", "Corazon En La Maleta"
            ]
        }
    ],
    "kpop": [
        {
            "id": "bts",
            "name": "BTS (방탄소년단)",
            "songs": [
                "Dynamite", "Butter", "Boy With Luv", "Fake Love", "DNA",
                "Mic Drop", "Spring Day", "Blood Sweat & Tears", "Life Goes On", "RUN BTS",
                "IDOL", "Permission to Dance", "Save ME", "Black Swan", "Fire"
            ]
        },
        {
            "id": "blackpink",
            "name": "BLACKPINK (블랙핑크)",
            "songs": [
                "How You Like That", "Kill This Love", "DDU-DU DDU-DU", "Pink Venom", "Shut Down",
                "As If It's Your Last", "Boombayah", "Lovesick Girls", "Solo (Jennie)", "Money (Lisa)",
                "Flower (Jisoo)", "On The Ground (Rosé)", "Whistle", "Playing With Fire", "Ice Cream"
            ]
        },
        {
            "id": "twice",
            "name": "TWICE",
            "songs": [
                "The Feels", "What is Love", "Fancy", "I Can't Stop Me", "TT",
                "Cheer Up", "Alcohol-Free", "Feel Special", "YES or YES", "Moonlight Sunrise"
            ]
        },
        {
            "id": "newjeans",
            "name": "NewJeans",
            "songs": [
                "Super Shy", "OMG", "Ditto", "Hype Boy", "Attention",
                "ETA", "New Jeans", "Cool With You", "How Sweet", "Bubble Gum"
            ]
        }
    ],
    "bhojpuri": [
        {
            "id": "khesari",
            "name": "Khesari Lal Yadav",
            "songs": [
                "Nathuniya", "Piyawa Gaye Re Pardes", "Leke Pehla Pehla Pyar", "Saj Ke Sawar Ke", "Dhamaka",
                "Chhaudi Re", "Tension Fret", "Le La Neenu", "Bhatar Ko Bhi Bhul Jaogi", "Dodi Par Maat Aaba"
            ]
        },
        {
            "id": "pawan",
            "name": "Pawan Singh",
            "songs": [
                "Lollypop Lagelu", "Raja Ji", "Pudina A Ah Ah", "Badnaam Karogi", "Current",
                "Hari Hari Odhani", "Zindagi 2.0", "Kamar Patre Patre", "Chhalakata Hamro Jawani", "Lalu Ki Lali"
            ]
        },
        {
            "id": "shilpi",
            "name": "Shilpi Raj",
            "songs": [
                "Nadi Bich Naiya Dole", "Relia Re", "Kamar Kahiya Ka", "Raja Ji Ke Dilwa", "Balamua",
                "Godanwa", "Dhadkan", "Jaan Leva Ka", "Piya Ji Se Mulaqat", "Nagin"
            ]
        }
    ],
    "haryanvi": [
        {
            "id": "gulzaar",
            "name": "Gulzaar Chhaniwala",
            "songs": [
                "Filter Shot", "Kasoote", "Middle Class", "Faad Faad", "Yamraaj",
                "System", "Dada", "Desi Bilotia", "Randa Party", "Godfather"
            ]
        },
        {
            "id": "khasa",
            "name": "Khasa Aala Chahar",
            "songs": [
                "Father Saab", "Mohtarma", "Loot Liya", "College Life", "Air Hostess",
                "Kasoote2", "Gadi Chori", "Faraar", "Badnaam", "Yaar Ki Shaadi"
            ]
        },
        {
            "id": "renuka",
            "name": "Renuka Panwar",
            "songs": [
                "52 Gaj Ka Daman", "Chatak Matak", "Kabootar", "Uncha Lamba Kad", "Bahu Kale Ki",
                "Chham Chham", "Suno Suno", "Gaon Ki Larki", "Dhan Dhan", "Parindey"
            ]
        }
    ],
    "tamil": [
        {
            "id": "anirudh",
            "name": "Anirudh Ravichander",
            "songs": [
                "Hukum", "Naa Ready", "Chaleya", "Arabic Kuthu", "Badass",
                "Vaathi Coming", "Why This Kolaveri Di", "Master Coming", "Private Party", "Hayyoda",
                "Two Two Two", "Dippam Dappam", "Chellamma", "Marana Mass", "Rathamaarey"
            ]
        },
        {
            "id": "arrahman_t",
            "name": "A.R. Rahman (Tamil)",
            "songs": [
                "Chinnanjiru Nilave", "Aathangara Marame", "Musthafa Musthafa", "Enna Sona", "Urvashi Urvashi",
                "Vande Mataram", "Netru Aval Irundhal", "New York Nagaram", "Marakkuma Nenjam", "Aaromale"
            ]
        },
        {
            "id": "sidsriram_t",
            "name": "Sid Sriram (Tamil)",
            "songs": [
                "Inkem Inkem", "Kannana Kanne", "Thalli Pogathey", "Kadhaippoma", "Srimathi",
                "Unnaalunnal", "Adiye", "Nira", "Anbae Peranbae", "Mehereezam"
            ]
        }
    ],
    "telugu": [
        {
            "id": "dsp",
            "name": "Devi Sri Prasad (DSP)",
            "songs": [
                "Oo Antava", "Srivalli", "Pushpa Pushpa", "Saami Saami", "Seeti Maar",
                "Mind Block", "Whistle Podu", "He's So Cute", "Dada Mass", "Ringa Ringa"
            ]
        },
        {
            "id": "thaman",
            "name": "S. Thaman",
            "songs": [
                "Ramuloo Ramulaa", "Samajavaragamana", "Butta Bomma", "Kurchi Madathapetti", "Hungry Cheetah", "Bheemla Nayak", "La La Bheemla", "Kalavathi", "Nijame Ne Chepputha", "OMG Pilla"
            ]
        },
        {
            "id": "sidsriram_tel",
            "name": "Sid Sriram (Telugu)",
            "songs": [
                "Inkem Inkem", "Samajavaragamana", "Srivalli", "Maguva Maguva", "Kumkumala",
                "Kalaavathi", "Nee Singali", "Oke Oka Lokam", "Arere Yekkada", "Undiporaadhey"
            ]
        }
    ],
    "malayalam": [
        {
            "id": "sushin",
            "name": "Sushin Shyam",
            "songs": [
                "Illuminati", "Cherathukal", "Jaada", "Neela Akasham", "Beeshma Parvam Theme",
                "Kicha Kicha", "Aaro", "Mathapithakkale", "Romancham Theme", "Kudukku"
            ]
        },
        {
            "id": "hesham",
            "name": "Hesham Abdul Wahab",
            "songs": [
                "Darshana", "Onakka Munthiri", "Priyathama", "Manasse Manasse", "Kani Konna",
                "Aaromale", "Hridayam Theme", "Kushi Theme", "Kannu Vecho", "Nizhal"
            ]
        }
    ],
    "kannada": [
        {
            "id": "ravibasrur",
            "name": "Ravi Basrur",
            "songs": [
                "KGF Monster Theme", "Toofan", "Salaar Theme", "Sulthana", "Mehabooba",
                "Garuda Theme", "Dheera", "Kantara Reclaim", "KGF Anthem", "Kabzaa Theme"
            ]
        },
        {
            "id": "vijayprakash",
            "name": "Vijay Prakash",
            "songs": [
                "Belageddu", "Bombe Sayuthaam", "Singara Siriye", "Open Hairu", "Kavyanjali",
                "Khali Quarter", "Henne Henne", "Neene Neene", "Nanna Regga", "Subbalakshmi"
            ]
        }
    ],
    "marathi": [
        {
            "id": "ajayatul",
            "name": "Ajay-Atul",
            "songs": [
                "Zingaat", "Sairat Zaala Ji", "Yad Lagla", "Chandra", "Khel Mandala",
                "Apsara Aali", "Dolby Walya", "Mauli Mauli", "Deva Shree Ganesha", "Shanti Kranti"
            ]
        },
        {
            "id": "swapnil",
            "name": "Swapnil Bandodkar",
            "songs": [
                "Radha Hi Bawari", "Galavar Khali", "Kuni Tari Yenar", "Tula Japnar Aahe", "Man Udhan Varyache"
            ]
        }
    ],
    "gujarati": [
        {
            "id": "kinjal",
            "name": "Kinjal Dave",
            "songs": [
                "Char Char Bangdi Vaali Gaadi", "Garbe Ghume Tu", "Leri Lala", "Dhan Che Gujarat", "Makhan Chor"
            ]
        },
        {
            "id": "aditya",
            "name": "Aditya Gadhvi",
            "songs": [
                "Khalasi (Gotilo)", "Nagar Nandji Na Lal", "Charan Kanya", "Sapna Vina Ni Raat", "Mahadev"
            ]
        }
    ],
    "bengali": [
        {
            "id": "arijit_b",
            "name": "Arijit Singh (Bengali)",
            "songs": [
                "Mon Majhi Re", "Tomake Chai", "Ki Kore Bolbo Tomay", "Bojhena Shey Bojhena", "Egiye De",
                "Parbona", "Shona", "Tor Ek Kothay", "Amar Mawna", "Kobe"
            ]
        },
        {
            "id": "anupam",
            "name": "Anupam Roy",
            "songs": [
                "Amake Amar Moto Thakte Dao", "Boba Tunnel", "Tumi Jaake Bhalobasho", "Ekbaar Bol", "Alik Shukh"
            ]
        }
    ],
    "urdu": [
        {
            "id": "nfak",
            "name": "Nusrat Fateh Ali Khan",
            "songs": [
                "Ye Jo Halka Halka Suroor Hai", "Rashk e Qamar", "Tumhein Dillagi Bhool Jani Padegi", "Coke Studio Afreen Afreen", "Sanu Ek Pal Chain",
                "Kinna Sohna Tainu", "Wohi Khuda Hai", "Tajdar e Haram", "Allah Hoo", "Sanson Ki Mala Pe"
            ]
        },
        {
            "id": "rfak",
            "name": "Rahat Fateh Ali Khan",
            "songs": [
                "Zaroori Tha", "Afreen Afreen", "O Re Piya", "Main Jahaan Rahoon", "Tere Mast Mast Do Nain",
                "Nit Khair Manga", "Bol Na Halke Halke", "Tum Jo Aaye", "Dagabaaz Re", "Sanu Ek Pal"
            ]
        }
    ],
    "arabic": [
        {
            "id": "amrdiab",
            "name": "Amr Diab",
            "songs": [
                "Tamally Maak", "Nour El Ain", "Habibi Ya Nours El Ain", "Ya Ana Ya La", "El Kisses"
            ]
        },
        {
            "id": "saad",
            "name": "Saad Lamjarred",
            "songs": [
                "LMGHARBA", "LM3ALLEM", "Ghaltana", "Min Awel Dekika", "Casablanca"
            ]
        }
    ],
    "phonk": [
        {
            "id": "kordhell",
            "name": "Kordhell Phonk",
            "songs": [
                "Murder In My Mind", "Live Another Day", "Killers From The North", "Scopin", "Land of Fire",
                "Fatality", "GOAT", "Massacre", "Vuk Vuk", "Endless"
            ]
        },
        {
            "id": "dvrst",
            "name": "DVRST Phonk",
            "songs": [
                "Close Eyes", "Komarovo", "Motion", "Reason", "Thinkin Of U",
                "Dreambound", "Endless Love", "My Reason", "Autumn", "Night Walk"
            ]
        },
        {
            "id": "brazilian",
            "name": "Brazilian Phonk Hits",
            "songs": [
                "Montagem PR Funk", "Funk Estranho", "Voisins Phonk", "Automotivo", "MTG Phonk",
                "Montagem Coral", "Toma Toma", "Mano", "Sequencia Da OS 1", "Dança Da Motoca"
            ]
        }
    ],
    "beats": [
        {
            "id": "lofi",
            "name": "Lo-Fi & Chill Beats",
            "songs": [
                "Lofi Hip Hop Chill Beats", "Late Night Lo Fi Study", "Coffee Shop Lo-Fi", "Rainy Mood Lofi", "Sunset Chillhop",
                "Sleep Lofi Beats", "Midnight Jazz Lofi", "Aesthetic Chill Hop", "Soft Piano Lofi", "Coding Lofi Beats"
            ]
        },
        {
            "id": "trap",
            "name": "Trap & Cyberpunk Beats",
            "songs": [
                "Cyberpunk Synthwave Beats", "Aggressive Trap Instrumental", "Chillhop Trap Beats", "Hard Hitting Bass Beats", "Midnight Drive Beats",
                "Futuristic Cyber Beats", "Phonk Trap Hybrid", "Heavy Bassline Beat", "Dark Synthwave", "Vaporwave Retro"
            ]
        }
    ]
}

def get_singers_for_lang(lang_key: str) -> List[Dict]:
    return SINGERS_CATALOG.get(lang_key, [])

def get_singer_details(lang_key: str, singer_id: str) -> Optional[Dict]:
    singers = SINGERS_CATALOG.get(lang_key, [])
    for singer in singers:
        if singer["id"] == singer_id:
            return singer
    return None
