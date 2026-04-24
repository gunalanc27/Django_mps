"""
Management command: seed_fake_users
Creates 20 fake Tamil Nadu-inspired users with:
  - Tamil Nadu-flavoured usernames & display names
  - A colourful avatar (fetched from ui-avatars.com or dicebear)
  - Profile location set to a Tamil Nadu city
  - Reviews across ALL products (ratings weighted ≥ 4.3 average)

Usage:
    python manage.py seed_fake_users
    python manage.py seed_fake_users --clear   # wipe existing fake users first
"""

import random
import io
import urllib.request
import urllib.parse

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

from products.models import Product
from reviews.models import Review
from accounts.models import UserProfile

User = get_user_model()

# ── 20 Tamil Nadu inspired users ────────────────────────────────────────────
# (username, first_name, last_name, city, avatar_bg_hex, avatar_fg_hex)
TN_USERS = [
    ("karthik_tn",    "Karthikeyan",  "Murugesan",  "Chennai",     "E91E63", "FFFFFF"),
    ("priya_kovai",   "Priya",        "Subramaniam","Coimbatore",  "9C27B0", "FFFFFF"),
    ("muthu_madurai", "Muthuselvam",  "Pandian",    "Madurai",     "3F51B5", "FFFFFF"),
    ("anbu_thanjai",  "Anbuchelvan",  "Rajendran",  "Thanjavur",   "009688", "FFFFFF"),
    ("selvi_trichy",  "Selvarani",    "Krishnan",   "Tiruchirappalli", "FF5722", "FFFFFF"),
    ("vel_erode",     "Velmurugan",   "Govindasamy","Erode",       "795548", "FFFFFF"),
    ("meena_salem",   "Meenakshi",    "Sundaram",   "Salem",       "607D8B", "FFFFFF"),
    ("raja_vellore",  "Rajakumar",    "Narayanan",  "Vellore",     "F44336", "FFFFFF"),
    ("saranya_tnvl",  "Saranya",      "Venkatesh",  "Tirunelveli", "673AB7", "FFFFFF"),
    ("guru_cuddalore","Gurusamy",     "Annamalai",  "Cuddalore",   "2196F3", "FFFFFF"),
    ("devi_dindigul", "Devimani",     "Palani",     "Dindigul",    "4CAF50", "FFFFFF"),
    ("senthil_ooty",  "Senthilkumar", "Rangasamy",  "Ooty",        "FF9800", "FFFFFF"),
    ("kavya_tiruppur","Kavyashree",   "Manoharan",  "Tiruppur",    "00BCD4", "FFFFFF"),
    ("arun_karur",    "Arunachalam",  "Thangavelu", "Karur",       "8BC34A", "000000"),
    ("nalini_vdm",    "Nalini",       "Venkatraman","Virudhunagar","CDDC39", "000000"),
    ("balu_sivakasi", "Balaguru",     "Duraisamy",  "Sivakasi",    "FFEB3B", "000000"),
    ("rajan_pollachi","Rajanikanth",  "Suresh",     "Pollachi",    "FFC107", "000000"),
    ("tamil_hosur",   "Tamilvanan",   "Elumalai",   "Hosur",       "FF6F00", "FFFFFF"),
    ("jai_pudukkottai","Jaikumar",    "Sekar",      "Pudukkottai", "1A237E", "FFFFFF"),
    ("vani_nagercoil","Vanimathi",    "Pillai",     "Nagercoil",   "880E4F", "FFFFFF"),
]

# ── Review content pool (same pool from seed_reviews, extended) ──────────────
# Keyed by product ID with (title, comment) tuples
REVIEW_POOL: dict[int, list[tuple[str, str]]] = {
    13: [  # Multi Charge Pro 120W Car Charger
        ("Super fast charging!", "This charges my Android phone to full in under 35 minutes. Perfect for long drives."),
        ("Compact powerhouse", "Fits neatly in the car without dangling. The 120W output is genuinely impressive."),
        ("Daily commute essential", "I use this every morning. Keeps my phone at 100% by the time I reach office."),
        ("Great dual port design", "Charges my phone and earbuds simultaneously with no speed drop. Loved it."),
        ("Solid and reliable", "Three months of daily use and not a single issue. Built to last."),
        ("Charges iPhone at full speed", "Works at full 20W with my iPhone 15. Exactly what was promised."),
        ("Heat is manageable", "Gets slightly warm during fast charge but nothing alarming. Normal for 120W."),
        ("Excellent value", "Compared to branded chargers costing 3x the price, this performs identically."),
        ("Travel friendly", "Small enough to forget it's plugged in. Great for road trips across TN."),
        ("Highly recommended", "Recommended this to three friends. All of them ordered within a week. Says it all."),
    ],
    12: [  # Xnano Mini Portable Projector
        ("Perfect backyard movies!", "Set this up in my terrace in Chennai. 120-inch screen felt cinematic!"),
        ("Brilliant for small offices", "Used for a client presentation in a dim room. Everyone was impressed."),
        ("Excellent picture clarity", "Colours are vibrant and sharp even at larger screen sizes. Very happy."),
        ("Battery is more than enough", "Watched a full 2.5-hour movie on one charge. No interruptions."),
        ("USB-C charging is perfect", "Charges fast and the port is universal. No proprietary nonsense."),
        ("Compact and very portable", "Fits in my laptop bag. Brought it to a friend's place and wowed everyone."),
        ("Fan noise is subtle", "You notice it in a totally silent room but fine during movie audio."),
        ("Kids love movie night", "Set it up in the bedroom for my kids. They think it's a real cinema!"),
        ("Good connectivity options", "HDMI, USB, and wireless screen mirroring all worked flawlessly."),
        ("Amazing for the price", "At this price, I expected mediocre. Got something genuinely excellent instead."),
    ],
    11: [  # G5 Handheld Game Player 500 in 1
        ("Nostalgia overload", "All the NES classics I played in school. Brought back so many memories!"),
        ("Screen is bright and clear", "No glare or dim spots. Great for playing outdoors in moderate light."),
        ("Excellent battery life", "Played for 7 hours before it even showed a low battery warning. Impressive."),
        ("Great gift for nephews", "Bought for my sister's kids. They absolutely can't put it down."),
        ("D-pad is very responsive", "Fired through action games without a single missed input. Well engineered."),
        ("500 games, 150 are truly fun", "Obviously not all 500 are gems but for the price you're getting more than enough."),
        ("Pocket sized fun", "Slips into any pocket. Perfect entertainment during train journeys across Tamil Nadu."),
        ("Solid build quality", "No flex or creaking. Feels like proper hardware for a fair price."),
        ("Headphone jack works great", "Good audio through my earphones. The built-in speaker is also decently loud."),
        ("Worth every rupee", "I expected a cheap toy and got a genuinely fun gaming device. Superb value."),
    ],
    10: [  # Xnano X3 Smart Projector
        ("Smart projector, smart choice", "Android built in means Netflix and YouTube without any extra device. Brilliant."),
        ("Auto-focus is magical", "It just finds focus automatically and holds it. No manual fiddling at all."),
        ("Vibrant colours", "Watching movies feels premium. The contrast and saturation are excellent."),
        ("Voice remote is a bonus", "The voice search works accurately in English. Very convenient addition."),
        ("Perfect for gaming", "Low-latency mode is great for console gaming. No noticeable delay at all."),
        ("WiFi super stable", "Streamed 4K content over WiFi for 3 hours without a single buffering moment."),
        ("App store is acceptable", "Not every app is available but sideloading works fine for missing ones."),
        ("Room-filling audio", "The built-in speakers fill a medium room easily. No need for an external speaker."),
        ("Quick and easy setup", "Unboxed, plugged in, calibrated, and watching a movie in under 10 minutes."),
        ("Genuinely impressed", "This replaced my aging TV in the bedroom. Best purchase I made this year."),
    ],
    9: [  # Advance Wireless Mini Game Box AD-222
        ("Instant family favourite", "My whole family fights over who plays next. Keeps everyone entertained."),
        ("Great wireless range", "Controller works perfectly from across our large living room. Zero lag."),
        ("Plug and play", "My 60-year-old father set it up himself. That's how intuitive it is."),
        ("Massive game variety", "From cricket to racing to puzzle games. Something for everyone in the family."),
        ("Compact miracle", "Fits in my palm yet delivers a full console-style experience on the TV."),
        ("Great for travel", "Took this on our Kodaikanal trip. Kept the kids entertained in the resort."),
        ("Controller build is solid", "No cheap rattling plastic. Buttons are clicky and responsive."),
        ("Re-pairs instantly", "Press one button and it's connected. No Bluetooth headaches whatsoever."),
        ("Excellent value", "Paid less than a single video game for an entire console. Unbeatable."),
        ("Highly recommended", "5 stars without hesitation. The whole family uses it every single evening."),
    ],
    8: [  # Terminator 2-in-1 Mini Bug Zapper
        ("Finally mosquito-free nights", "Placed this in my bedroom and slept peacefully for the first time in summer."),
        ("2-in-1 is very practical", "Lamp mode during power cuts and zapper mode at night. Two birds one stone."),
        ("Effective and chemical free", "No sprays, no coils, no smell. Just clean, silent zapping. Love it."),
        ("Covers entire bedroom", "One unit in the centre of the room handles the whole space effectively."),
        ("USB charging is convenient", "Works with any power bank. Used it during our camping trip with zero issues."),
        ("Silent operation", "The zap sound is brief and then silence. Doesn't disturb sleep at all."),
        ("Great for outdoor use too", "Used it on our balcony during evening gatherings. Kept bugs completely away."),
        ("Easy to maintain", "The collection tray slides out cleanly. Takes seconds to empty and clean."),
        ("Durable after 6 months", "Still works perfectly after half a year of daily use. Very sturdy."),
        ("Gift it to everyone", "Gifted three of these to relatives in Chennai. All of them loved it immediately."),
    ],
    7: [  # S10 Controller Gamepad
        ("Premium feel controller", "Build quality rivals controllers costing 5x more. Extraordinary value."),
        ("Zero latency Bluetooth", "Not a single frame of input lag detected across hours of gaming sessions."),
        ("Mobile gaming transformed", "Clipping my phone in and gaming on BGMI changed everything. Very enjoyable."),
        ("Long battery life", "8+ hours per charge. A full weekend gaming session without needing to recharge."),
        ("Great trigger feedback", "The resistance and travel of the triggers is perfect for shooters and racing games."),
        ("Ergonomic and comfortable", "Even after 3-hour sessions, no hand cramps or discomfort whatsoever."),
        ("Wide device compatibility", "Works with Android, PC, and even my smart TV. Incredibly versatile."),
        ("Joystick precision", "Smooth, accurate, and zero dead zone. Great for competitive mobile gaming."),
        ("Pairs fast every time", "Hold one button and it connects within 2 seconds. Never had a failed pairing."),
        ("Best budget controller", "Compared four controllers in this range. This one wins on every parameter."),
    ],
    5: [  # Terminator Rechargeable Mosquito Bat
        ("One swing, problem solved", "Electric grid zaps mosquitoes instantly and effectively. Very satisfying."),
        ("Rechargeable saves money", "No more buying batteries every week. Just plug in and it's ready."),
        ("Great grip and balance", "The rubberised handle makes it easy to swing precisely. Well designed."),
        ("LED torch is very useful", "The built-in torch saves me during power cuts. An excellent bonus feature."),
        ("Safe with the protective mesh", "The outer mesh prevents accidental contact with the charged grid. Safety first."),
        ("Works on all flying insects", "Effective on mosquitoes, houseflies, and gnats equally. Very versatile."),
        ("Full week on one charge", "Charge it once on Sunday and use it comfortably through the entire week."),
        ("Gifted to parents", "My parents in Madurai love it. They use it every evening on the verandah."),
        ("Charge indicator is helpful", "LED tells you exactly when to recharge. A small but thoughtful detail."),
        ("Best mosquito bat ever", "Tried many brands over the years. This one is the most durable and effective."),
    ],
    3: [  # Apple AirPods 4 ANC
        ("ANC is a game-changer", "I can work in complete silence even in our noisy Chennai office. Incredible."),
        ("Crystal clear audio", "Music sounds phenomenal. Every instrument is detailed and perfectly balanced."),
        ("Seamless Apple experience", "Switches between iPhone, iPad, and Mac instantly. Magic."),
        ("5-hour ANC battery is great", "More than enough for a full workday. The case gives plenty of extra charges."),
        ("Call quality is superb", "Everyone says my voice sounds perfectly clear even in outdoor environments."),
        ("Transparency mode is excellent", "I can hear the world naturally when needed. Very useful on the road."),
        ("Comfortable for long sessions", "Wore these for 6 hours during a long train journey. No discomfort at all."),
        ("Workout tested and approved", "Used at the gym daily for a month. Never fell out, not even once."),
        ("Premium unboxing", "The packaging and accessories feel luxury. Worth expecting from Apple."),
        ("Absolutely worth the price", "The most I've spent on earbuds and the best I've ever experienced."),
    ],
    2: [  # 2.4G Wireless Controller Gamepad Game Stick Lite
        ("Instant plug and play", "Plugged the receiver into my TV and it worked immediately. No setup at all."),
        ("Responsive and accurate", "Every button press registers instantly. Zero lag over 2.4G connection."),
        ("Great battery economy", "AA batteries have lasted three weeks of daily use. Very efficient hardware."),
        ("Works on everything", "Compatible with Android TV, laptop, and PC. Extremely versatile product."),
        ("Comfortable for long sessions", "No hand fatigue even after 2-hour gaming sessions. Well-ergonomed."),
        ("8-metre range tested", "Walked to the back of my room and it still worked flawlessly. Great range."),
        ("Solid build quality", "Dropped it twice. Still works like new. Clearly built to take punishment."),
        ("D-pad is precise", "As a fighting game player the D-pad is accurate and responsive. Very happy."),
        ("Value for money", "This outperforms branded controllers costing 4x more. Unbelievable."),
        ("Simple and reliable", "No apps, no pairing headaches, no lag. Just works. Exactly what I needed."),
    ],
    1: [  # product1
        ("Good starter product", "Does its job without any fuss. Great for someone trying this category first time."),
        ("Solid quality", "Quality feels above average for this price point. Pleasantly surprised."),
        ("Quick delivery, great packing", "Arrived in two days and was perfectly packed. No damage at all."),
        ("Reliable daily use", "Using this daily for over a month now. Not a single issue encountered."),
        ("Better than expected", "Was hesitant from mixed reviews but my experience has been entirely positive."),
        ("Good first impression", "Looks and feels well-made on first use. Gives a premium impression."),
        ("Would buy again", "If mine ever breaks I would buy this exact product again without hesitation."),
        ("Recommended to friends", "Two friends ordered after seeing mine. Both extremely happy with it."),
        ("Functional and sturdy", "Shows no signs of wear after weeks of regular use. Very dependable."),
        ("Great value", "Priced perfectly for what you get. No regrets at all about this purchase."),
    ],
}

# Rating distribution that always yields ≥ 4.3 average
# Weights: 5★=5, 4★=4, 3★=1 → avg ≈ (5*5+4*4+3*1)/10 = (25+16+3)/10 = 4.4
HIGH_RATING_WEIGHTS = {5: 5, 4: 4, 3: 1, 2: 0, 1: 0}
RATING_CHOICES = list(HIGH_RATING_WEIGHTS.keys())
RATING_WEIGHTS = list(HIGH_RATING_WEIGHTS.values())


def _fetch_avatar_bytes(username: str, bg: str, fg: str) -> bytes:
    """Download a coloured avatar image from ui-avatars.com."""
    name_param = urllib.parse.quote(username.replace("_", " ").title())
    url = (
        f"https://ui-avatars.com/api/"
        f"?name={name_param}&background={bg}&color={fg}"
        f"&size=256&bold=true&rounded=true&format=png"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


class Command(BaseCommand):
    help = "Create 20 Tamil Nadu fake users with avatars and high-rating reviews."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete previously created fake users (by username list) before re-seeding.",
        )

    def handle(self, *args, **options):
        usernames = [u[0] for u in TN_USERS]

        if options["clear"]:
            deleted_users = User.objects.filter(username__in=usernames).count()
            User.objects.filter(username__in=usernames).delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted_users} existing fake user(s)."))

        products = list(Product.objects.all())
        if not products:
            self.stderr.write(self.style.ERROR("No products found. Seed products first."))
            return

        total_users_created = 0
        total_reviews_created = 0
        total_skipped = 0

        for (username, first_name, last_name, city, bg, fg) in TN_USERS:
            # ── Create user ──────────────────────────────────────────────────
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": f"{username}@example.com",
                    "is_active": True,
                },
            )
            if user_created:
                user.set_password("FakePass@2025")
                user.save()
                total_users_created += 1
                self.stdout.write(f"  Created user: {username} ({city})")
            else:
                self.stdout.write(f"  User already exists: {username}")

            # ── Ensure profile exists ────────────────────────────────────────
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.location = city
            profile.bio = f"Shopping from {city}, Tamil Nadu 🛍️"

            # ── Fetch and save avatar ────────────────────────────────────────
            if not profile.avatar:
                try:
                    image_bytes = _fetch_avatar_bytes(username, bg, fg)
                    profile.avatar.save(
                        f"{username}_avatar.png",
                        ContentFile(image_bytes),
                        save=False,
                    )
                    self.stdout.write(self.style.SUCCESS(f"    ✓ Avatar uploaded for {username}"))
                except Exception as exc:  # noqa: BLE001
                    self.stdout.write(self.style.WARNING(f"    ⚠ Avatar fetch failed for {username}: {exc}"))

            profile.save()

            # ── Write reviews ────────────────────────────────────────────────
            for product in products:
                if Review.objects.filter(product=product, user=user).exists():
                    total_skipped += 1
                    continue

                pool = REVIEW_POOL.get(product.pk)
                if not pool:
                    continue

                title, comment = random.choice(pool)
                rating = random.choices(RATING_CHOICES, weights=RATING_WEIGHTS, k=1)[0]

                Review.objects.create(
                    product=product,
                    user=user,
                    rating=rating,
                    title=title,
                    comment=comment,
                    is_approved=True,
                    helpful_count=random.randint(0, 40),
                )
                total_reviews_created += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done! {total_users_created} user(s) created, "
            f"{total_reviews_created} review(s) added, "
            f"{total_skipped} skipped (already existed)."
        ))
        self.stdout.write(self.style.SUCCESS(
            "All products now have weighted-high ratings (≥ 4.3 average expected)."
        ))
