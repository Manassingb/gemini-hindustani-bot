INTERACTION_CATEGORY_ORDER = [
    "interaction",
    "love",
    "daily",
    "funny",
    "anime",
    "premium",
]

INTERACTION_CATEGORY_TITLES = {
    "interaction": "Interaction",
    "love": "Love and Couple",
    "daily": "Daily Life",
    "funny": "Funny and Meme",
    "anime": "Anime and Mood",
    "premium": "Premium",
}


def _spec(category, display, emoji, media_candidates, target_action, solo_action, description):
    return {
        "category": category,
        "display": display,
        "emoji": emoji,
        "media_candidates": list(media_candidates),
        "target_action": target_action,
        "solo_action": solo_action,
        "description": description,
    }


INTERACTION_COMMAND_SPECS = {
    "hug": _spec("interaction", "Hug", "🤗", ["hug", "cuddle", "glomp"], "ne {target} ko warm hug diya", "warm hug vibes spread kar raha hai", "send a warm hug"),
    "kiss": _spec("interaction", "Kiss", "😘", ["kiss", "blowkiss", "peck"], "ne {target} ko pyaara sa kiss diya", "sweet kiss vibes uda raha hai", "send a kiss gif"),
    "flingkiss": _spec("love", "Fling Kiss", "💋", ["blowkiss", "kiss", "peck", "wink"], "ne {target} ki taraf flying kiss bheja", "flying kiss vibes uda raha hai", "send a fling kiss gif"),
    "slap": _spec("interaction", "Slap", "👋", ["slap", "bonk"], "ne {target} ko dramatic slap mara", "full filmy slap energy dikh raha hai", "send a slap gif"),
    "pat": _spec("interaction", "Pat", "🫳", ["pat", "smile"], "ne {target} ko softly pat kiya", "soft pat mood me hai", "send a pat gif"),
    "cuddle": _spec("interaction", "Cuddle", "🫂", ["cuddle", "hug", "lappillow"], "ne {target} ko cozy cuddle diya", "cozy cuddle mood bana raha hai", "send a cuddle gif"),
    "lick": _spec("interaction", "Lick", "😛", ["lick", "nom", "smug"], "ne {target} ko naughty lick diya", "mischievous lick vibe me hai", "send a lick gif"),
    "bite": _spec("interaction", "Bite", "🦷", ["bite", "nom"], "ne {target} ko playful bite diya", "playful bite mode me hai", "send a bite gif"),
    "poke": _spec("interaction", "Poke", "👉", ["poke", "wave"], "ne {target} ko poke kiya", "sabko poke karke notice le raha hai", "send a poke gif"),
    "tickle": _spec("interaction", "Tickle", "😆", ["tickle", "laugh"], "ne {target} ko tickle kiya", "tickle wali masti chala raha hai", "send a tickle gif"),
    "punch": _spec("interaction", "Punch", "🥊", ["punch", "bonk"], "ne {target} ko anime punch mara", "anime punch energy me hai", "send a punch gif"),
    "kick": _spec("interaction", "Kick", "🦵", ["kick", "yeet"], "ne {target} ko flying kick diya", "kick mode on kar diya", "send a kick gif"),
    "wave": _spec("interaction", "Wave", "👋", ["wave", "happy"], "ne {target} ko pyara sa wave diya", "sabko hello wave kar raha hai", "send a wave gif"),
    "highfive": _spec("interaction", "High Five", "🙌", ["highfive", "clap"], "ne {target} ko high five diya", "high five energy spread kar raha hai", "send a high five gif"),
    "handshake": _spec("interaction", "Handshake", "🤝", ["handshake", "salute"], "ne {target} se handshake kiya", "handshake wali formal vibe la raha hai", "send a handshake gif"),
    "cheers": _spec("interaction", "Cheers", "🥂", ["sip", "clap"], "ne {target} ke saath cheers kiya", "sabke saath cheers vibe share kar raha hai", "send a cheers gif"),
    "smile": _spec("interaction", "Smile", "😊", ["smile", "happy"], "ne {target} ko cute smile di", "pyari smile ke saath chamak raha hai", "send a smile gif"),
    "laugh": _spec("interaction", "Laugh", "😂", ["laugh", "teehee"], "ne {target} ke saath zor se laugh kiya", "full hasi ke mood me hai", "send a laugh gif"),
    "cry": _spec("interaction", "Cry", "😭", ["cry", "pout"], "ne {target} ke saamne emotional cry kiya", "thoda emotional ho gaya hai", "send a cry gif"),
    "angry": _spec("interaction", "Angry", "😤", ["angry", "pout"], "ne {target} par angry look diya", "angry anime energy dikha raha hai", "send an angry gif"),
    "blush": _spec("interaction", "Blush", "😊", ["blush", "smug"], "ko dekhkar blush kar gaya", "blush karke cute lag raha hai", "send a blush gif"),
    "dance": _spec("interaction", "Dance", "💃", ["dance", "happy"], "ne {target} ke saamne dance kar diya", "dance floor vibes chala raha hai", "send a dance gif"),
    "sleep": _spec("interaction", "Sleep", "😴", ["sleep", "yawn"], "ne {target} ke paas sleepy mood dikhaya", "sleep mode me ja raha hai", "send a sleep gif"),
    "run": _spec("interaction", "Run", "🏃", ["run", "wave"], "ne {target} ki taraf full speed run lagayi", "run mode me zoom kar raha hai", "send a run gif"),
    "jump": _spec("interaction", "Jump", "🦘", ["spin", "happy"], "ne {target} ke saamne excited jump kiya", "khushi me jump kar raha hai", "send a jump gif"),
    "facepalm": _spec("interaction", "Facepalm", "🤦", ["facepalm", "tableflip"], "ne {target} ki baat par facepalm kiya", "pure facepalm mood me hai", "send a facepalm gif"),
    "shrug": _spec("interaction", "Shrug", "🤷", ["shrug", "confused"], "ne {target} ko shrug de diya", "shrug karke chill bana hua hai", "send a shrug gif"),
    "wink": _spec("interaction", "Wink", "😉", ["wink", "smile"], "ne {target} ko wink maara", "wink karke vibe bana raha hai", "send a wink gif"),
    "love": _spec("love", "Love", "❤️", ["love", "blowkiss", "kiss"], "ne {target} par pyaar barsaya", "love vibes uda raha hai", "share love vibes"),
    "romance": _spec("love", "Romance", "💞", ["cuddle", "kiss", "handhold"], "ke saath romantic moment bana diya", "romantic aura chala raha hai", "send a romance gif"),
    "date": _spec("love", "Date", "🍫", ["handhold", "cuddle", "smile"], "ko dreamy date par le gaya", "date vibes set kar raha hai", "send a date gif"),
    "propose": _spec("love", "Propose", "💍", ["blowkiss", "kabedon", "kiss"], "ko dramatic propose kar diya", "proposal mood me dil rakh raha hai", "send a proposal gif"),
    "marry": _spec("love", "Marry", "💒", ["kiss", "handhold", "cuddle"], "ko shaadi ka offer de diya", "shaadi wali cute vibes la raha hai", "send a marry gif"),
    "flirt": _spec("love", "Flirt", "😏", ["smug", "wink", "blush"], "se stylish flirt kar diya", "flirty mood me smooth ban raha hai", "send a flirt gif"),
    "jealous": _spec("love", "Jealous", "😒", ["angry", "pout", "baka"], "ko dekhkar jealous ho gaya", "jealous vibe me sulking kar raha hai", "send a jealous gif"),
    "miss": _spec("love", "Miss", "🥺", ["cry", "hug", "love"], "ko bahut miss kar raha hai", "kisi ko yaad karke soft ho gaya hai", "send a miss gif"),
    "care": _spec("love", "Care", "💗", ["hug", "pat", "cuddle"], "ki care kar raha hai", "care aur softness spread kar raha hai", "send a care gif"),
    "support": _spec("love", "Support", "🫶", ["hug", "thumbsup", "salute"], "ko full support de raha hai", "supportive energy share kar raha hai", "send a support gif"),
    "comfort": _spec("love", "Comfort", "🤍", ["cuddle", "hug", "pat"], "ko comfort kar raha hai", "comfort aur calm vibes de raha hai", "send a comfort gif"),
    "holdhand": _spec("love", "Hold Hand", "🤝", ["handhold", "cuddle"], "ka haath pakad liya", "handhold wali sweet vibe me hai", "send a hold hand gif"),
    "goodmorning": _spec("daily", "Good Morning", "☀️", ["wave", "smile", "happy"], "ko sweet good morning wish kiya", "sabko bright good morning keh raha hai", "send a good morning gif"),
    "goodnight": _spec("daily", "Good Night", "🌙", ["sleep", "yawn", "wink"], "ko pyara sa good night bola", "sabko cozy good night wish kar raha hai", "send a good night gif"),
    "goodevening": _spec("daily", "Good Evening", "🌆", ["wave", "smile", "happy"], "ko soft good evening wish kiya", "sabko peaceful good evening bol raha hai", "send a good evening gif"),
    "goodafternoon": _spec("daily", "Good Afternoon", "🌤", ["wave", "happy", "smile"], "ko good afternoon wish kiya", "sabko sunny good afternoon keh raha hai", "send a good afternoon gif"),
    "welcome": _spec("daily", "Welcome", "🎉", ["wave", "happy", "smile"], "ka dil se welcome kiya", "sabko warmly welcome kar raha hai", "send a welcome gif"),
    "bye": _spec("daily", "Bye", "👋", ["wave", "salute", "wink"], "ko bye bol diya", "sabko soft bye keh raha hai", "send a bye gif"),
    "welcome_back": _spec("daily", "Welcome Back", "✨", ["wave", "hug", "happy"], "ka welcome back kiya", "returning vibes ka welcome kar raha hai", "send a welcome back gif"),
    "takecare": _spec("daily", "Take Care", "🌷", ["pat", "hug", "salute"], "ko take care bolkar pyar bheja", "take care aur soft concern share kar raha hai", "send a take care gif"),
    "study": _spec("daily", "Study", "📚", ["think", "nod", "smile"], "ko study mode me bhej diya", "serious study mood me aa gaya hai", "send a study gif"),
    "work": _spec("daily", "Work", "💼", ["think", "thumbsup", "nod"], "ko work focus de raha hai", "work mode activate kar raha hai", "send a work gif"),
    "rest": _spec("daily", "Rest", "🛌", ["sleep", "yawn", "lappillow"], "ko rest karne bhej diya", "rest aur recharge mood me hai", "send a rest gif"),
    "lol": _spec("funny", "LOL", "🤣", ["laugh", "teehee", "happy"], "ko dekhkar lol mode on kar diya", "lol vibes me phat ke hans raha hai", "send a lol gif"),
    "rofl": _spec("funny", "ROFL", "🤣", ["laugh", "yeet", "teehee"], "ko dekhkar rofl ho gaya", "itna hans raha hai ki control hi nahi hai", "send a rofl gif"),
    "cringe": _spec("funny", "Cringe", "😬", ["cringe", "confused", "facepalm"], "ko cringe look de diya", "cringe se hil gaya hai", "send a cringe gif"),
    "confused": _spec("funny", "Confused", "😵", ["confused", "stare", "shrug"], "ko dekhkar confused ho gaya", "confused aura me atak gaya hai", "send a confused gif"),
    "thinking": _spec("funny", "Thinking", "🤔", ["think", "stare", "nod"], "ke bare me soch me pad gaya", "deep thinking pose me hai", "send a thinking gif"),
    "dead": _spec("funny", "Dead", "💀", ["tableflip", "facepalm", "shocked"], "ki baat par dead reaction de diya", "dead reaction wali meme energy la raha hai", "send a dead meme gif"),
    "sus": _spec("funny", "Sus", "🕵️", ["stare", "confused", "smug"], "ko sus bol diya", "sus detective vibe me dekh raha hai", "send a sus gif"),
    "noob": _spec("funny", "Noob", "🐣", ["baka", "bonk", "shrug"], "ko noob bolkar chhed diya", "noob meme mode me aa gaya hai", "send a noob gif"),
    "pro": _spec("funny", "Pro", "😎", ["cool", "thumbsup", "smug"], "ko full pro declare kar diya", "pro gamer vibes flaunt kar raha hai", "send a pro gif"),
    "hack": _spec("funny", "Hack", "💻", ["think", "smug", "stare"], "par hacker mode chala diya", "hack vibes ke saath mastermind lag raha hai", "send a hack gif"),
    "tsundere": _spec("anime", "Tsundere", "😤", ["baka", "pout", "blush"], "ko tsundere attitude dikha diya", "full tsundere mode me pighal bhi raha hai", "send a tsundere gif"),
    "yandere": _spec("anime", "Yandere", "🖤", ["stare", "angry", "kabedon"], "ke liye yandere obsession dikha diya", "thoda dangerous yandere vibe la raha hai", "send a yandere gif"),
    "baka": _spec("anime", "Baka", "😝", ["baka", "bonk"], "ko baka bol diya", "baka anime vibes chala raha hai", "send a baka gif"),
    "senpai": _spec("anime", "Senpai", "🌸", ["blush", "smile", "wink"], "ko senpai kehkar impress kar diya", "senpai notice-me vibes la raha hai", "send a senpai gif"),
    "kawaii": _spec("anime", "Kawaii", "🌷", ["smile", "blush", "happy"], "ko kawaii bol diya", "kawaii sweetness spread kar raha hai", "send a kawaii gif"),
    "cool": _spec("anime", "Cool", "🕶", ["cool", "smug", "wink"], "ko cool style de diya", "full cool aura carry kar raha hai", "send a cool gif"),
    "hot": _spec("anime", "Hot", "🔥", ["blush", "smug", "wink"], "ko hot look de diya", "hot anime energy me chamak raha hai", "send a hot gif"),
    "sleepy": _spec("anime", "Sleepy", "🥱", ["sleep", "yawn", "lappillow"], "ko dekhkar sleepy ho gaya", "sleepy cloud me kho gaya hai", "send a sleepy gif"),
    "hungry": _spec("anime", "Hungry", "🍜", ["feed", "nom", "sip"], "ko dekhkar hungry ho gaya", "hungry anime tummy vibes dikha raha hai", "send a hungry gif"),
    "drunk": _spec("anime", "Drunk", "🍷", ["sip", "blush", "smug"], "ke saamne tipsy act kar raha hai", "drunk meme energy la raha hai", "send a drunk gif"),
    "respect": _spec("premium", "Respect", "🫡", ["salute", "thumbsup", "handshake"], "ko full respect diya", "respect aur honor vibes show kar raha hai", "send a respect gif"),
    "ignore": _spec("premium", "Ignore", "🙈", ["nope", "lurk", "shrug"], "ko total ignore kar diya", "ignore karke side ho gaya hai", "send an ignore gif"),
    "challenge": _spec("premium", "Challenge", "⚔️", ["kabedon", "stare", "shake"], "ko challenge de diya", "challenge aura me ready khada hai", "send a challenge gif"),
    "fight": _spec("premium", "Fight", "🥷", ["punch", "slap", "kick"], "ko fight ke liye bula liya", "fight mode me charged up hai", "send a fight gif"),
    "protect": _spec("premium", "Protect", "🛡", ["hug", "salute", "carry"], "ko protect karne aa gaya", "protective shield vibes la raha hai", "send a protect gif"),
    "carry": _spec("premium", "Carry", "🏋️", ["carry", "hug", "cuddle"], "ko uthakar carry kar liya", "carry hero mode me aa gaya hai", "send a carry gif"),
    "kidnap": _spec("premium", "Kidnap", "😈", ["carry", "run", "kabedon"], "ko drama style me kidnap kar liya", "full dramatic kidnap meme chala raha hai", "send a kidnap gif"),
    "rescue": _spec("premium", "Rescue", "🚑", ["carry", "hug", "run"], "ko rescue kar liya", "rescue hero vibe me daud raha hai", "send a rescue gif"),
    "attack": _spec("premium", "Attack", "⚡", ["shoot", "punch", "slap"], "par anime attack launch kar diya", "attack mode me full power dikha raha hai", "send an attack gif"),
    "defend": _spec("premium", "Defend", "🧱", ["salute", "thumbsup", "shake"], "ko defend karne khada ho gaya", "defend stance me steady khada hai", "send a defend gif"),
}


INTERACTION_COMMAND_NAMES = tuple(INTERACTION_COMMAND_SPECS.keys())

REGISTERED_INTERACTION_COMMAND_NAMES = INTERACTION_COMMAND_NAMES


def get_interaction_commands_text():
    lines = []
    for category in INTERACTION_CATEGORY_ORDER:
        title = INTERACTION_CATEGORY_TITLES[category]
        names = [name for name, spec in INTERACTION_COMMAND_SPECS.items() if spec["category"] == category]
        lines.append(f"{title}:")
        lines.append(" ".join(f"/{name}" for name in names))
        lines.append("")
    return "\n".join(lines).strip()
