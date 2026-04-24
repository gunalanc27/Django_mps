"""
Management command: seed_reviews
Adds 10 realistic, product-relevant reviews for every product in the database.
Ratings are randomly distributed between 1 and 5.
All reviews are auto-approved so they appear immediately.

Usage:
    python manage.py seed_reviews
    python manage.py seed_reviews --clear   # wipe existing seeded reviews first
"""

import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Product
from reviews.models import Review

User = get_user_model()

# ---------------------------------------------------------------------------
# Review templates per product ID (matches the live DB snapshot)
# Format: (title, comment)
# ---------------------------------------------------------------------------

REVIEW_POOL = {
    # ── Multi Charge Pro 120W Car Charger (ID 13) ──
    13: [
        ("Blazing fast charge!", "Charges my phone from 0 to 100 in under 40 minutes while driving. The 120W output is no joke. Solid build quality too."),
        ("Great value for money", "I use this every day during my commute. Charges two devices simultaneously without any lag in speed. Highly recommended."),
        ("Good but gets warm", "Works perfectly and charges quickly, though the charger does get a little warm during extended use. Nothing alarming."),
        ("Must-have car accessory", "I got this for a long road trip and it was a lifesaver. Kept my phone and tablet charged throughout the journey."),
        ("Compact and powerful", "Surprised by how small it is given the 120W rating. Fits flush in my car's USB port. No dangling cables needed."),
        ("Charges my iPhone at full speed", "Works flawlessly with my iPhone 15 Pro Max. Gets to 50% in about 15 minutes. Very happy with this purchase."),
        ("Sturdy build", "The braided cable is premium quality. No fraying or loose connections after 3 months of daily use."),
        ("Fast and reliable", "I was skeptical about third-party chargers but this one matched my brand charger's speed. Great product."),
        ("Perfect for long drives", "Long drive + this charger = full battery. Simple as that. The LED light indicator is a nice touch."),
        ("Slight compatibility issue", "Works great for Android but my old iPhone needed an adapter. Once sorted, the charging speed was excellent."),
    ],

    # ── Xnano Mini Portable Projector (ID 12) ──
    12: [
        ("Brilliant movie nights!", "Set this up in the backyard and streamed movies from my phone. The picture quality was crisp at 100-inch size. Amazing!"),
        ("Compact and powerful", "I carry this in my backpack. The image quality is surprisingly good for such a small projector."),
        ("Good for presentations", "Used it in a client meeting. Bright enough for a dim conference room. Everyone was impressed."),
        ("Fan noise is noticeable", "Works well but the cooling fan is audible in quiet environments. Not a dealbreaker for home use."),
        ("Great value projector", "For the price, this is unbeatable. Colors are vibrant and clarity is decent for casual viewing."),
        ("My kids love it", "Set it up as a mini cinema for the kids. They absolutely love it. Easy to set up and connect via HDMI."),
        ("Battery life is decent", "Got about 2.5 hours on a single charge. Enough for a movie. Recharges quickly via USB-C."),
        ("Easy connectivity", "Connected to my laptop, phone, and Fire Stick with no issues. Very versatile little device."),
        ("Slightly dim outdoors", "Works great indoors but struggles in sunlight. Best used in a dark or semi-dark room."),
        ("Impressive for its size", "I didn't expect much but I was blown away. The auto-focus feature is smooth and accurate."),
    ],

    # ── G5 Handheld Game Player 500 in 1 (ID 11) ──
    11: [
        ("Nostalgia overload!", "This brought back so many childhood memories. All the classic NES and arcade games I grew up with. Pure joy."),
        ("Great gift for kids", "Bought this for my 8-year-old nephew. He hasn't put it down since. Sturdy and colourful."),
        ("500 games, most are gems", "Not all 500 games are winners but there are easily 100+ classics that are genuinely fun. Great value."),
        ("Battery lasts all day", "Played for 6+ hours on one charge. The battery life is impressive for a handheld console."),
        ("Screen quality is decent", "The screen is bright enough and responsive. Not a premium display but perfect for retro games."),
        ("Easy to carry everywhere", "Slips into my jacket pocket easily. Perfect commute entertainment. Sturdy build too."),
        ("Sound quality is good", "The speakers are surprisingly loud and clear. The headphone jack works flawlessly as well."),
        ("Some games have bugs", "A few games freeze occasionally but a quick reset solves it. Overall still very enjoyable."),
        ("Fun for all ages", "My parents tried it and they loved the old games too. This is genuinely a family entertainment device."),
        ("Great build quality", "Feels solid in the hands. The D-pad and buttons are responsive and satisfying to press."),
    ],

    # ── Xnano X3 Smart Projector (ID 10) ──
    10: [
        ("Smart projector done right", "Built-in Android OS works smoothly. I stream Netflix and YouTube directly without needing any extra device."),
        ("Incredible picture quality", "The colours are vivid and the contrast is excellent. Our home theatre experience went up several notches."),
        ("WiFi connectivity is seamless", "Connects to WiFi in seconds. No drops or buffering issues. Very stable streaming experience."),
        ("Worth every rupee", "Was hesitant at first but after using it for a month, I can confidently say it's worth the investment."),
        ("Auto-focus is brilliant", "The automatic keystone correction and focus means no fiddling around. Just power on and enjoy."),
        ("Remote is intuitive", "The remote is well-designed and responsive. Voice command feature works surprisingly well."),
        ("Great for gaming too", "Connected my console and the low-latency mode made gaming enjoyable. No noticeable input lag."),
        ("Audio is impressive", "The built-in speakers are loud and clear for a projector. Easily fills a medium-sized room."),
        ("Minor app store limitation", "The app store doesn't have every app but sideloading works fine. Not a major issue."),
        ("Setup took 5 minutes", "Out of the box to watching a movie in 5 minutes. The quickstart guide is clear and simple."),
    ],

    # ── Advance Wireless Mini Game Box AD-222 (ID 9) ──
    9: [
        ("Plug and play perfection", "Connected to my TV in seconds. The wireless controller is responsive with zero lag. Great for family game nights."),
        ("Massive game library", "The variety of games is staggering. From racing to puzzles to sports — there's something for everyone."),
        ("Wireless range is excellent", "Tested the controller from across the room and it works perfectly. No dead zones."),
        ("Kids absolutely love it", "My children fight over who gets to play next. It has become the most used device in the house."),
        ("Compact design", "Fits in my palm and in my pocket. Takes up almost no space but delivers a ton of entertainment."),
        ("Good build quality", "The controller feels solid and the buttons are responsive. Doesn't feel cheap at all."),
        ("Occasional disconnects", "The controller disconnects once in a while but re-pairs quickly. Minor issue overall."),
        ("Great for road trips", "Brought this on a family vacation. Kids were entertained the entire time. Absolute must-have."),
        ("Easy to set up", "Even my grandparents managed to set it up without help. The interface is incredibly intuitive."),
        ("Best budget game console", "For the price, this offers unmatched value. I've spent more on games alone that cost more than this entire box."),
    ],

    # ── Terminator 2-in-1 Mini Bug Zapper (ID 8) ──
    8: [
        ("No more mosquitoes!", "Placed this in the bedroom and had a mosquito-free sleep for the first time in years. Absolutely love it."),
        ("2-in-1 is genius", "The fact that it works as both a zapper and a lamp is so practical. One device, two uses."),
        ("Effective and safe", "No chemicals or sprays needed. My kids and pets are safe and the bugs are gone. Win-win."),
        ("Covers a large area", "Placed it in the centre of the living room and it handles the entire space. Very effective coverage."),
        ("Easy to clean", "The tray collects dead insects and slides out cleanly. Takes 30 seconds to clean. Excellent design."),
        ("Silent operation", "Makes a small zap sound when it catches something but otherwise completely silent. Perfect for bedrooms."),
        ("USB charging is convenient", "Charges via USB so I can use a power bank. Very flexible for camping and outdoor use."),
        ("Works outdoors too", "Took it to a BBQ party in the garden. Kept the bugs away effectively throughout the evening."),
        ("Built like a tank", "The mesh grid feels very sturdy. Doesn't feel flimsy at all even after months of use."),
        ("Slightly small for large rooms", "For very large spaces you may need two units but for a standard bedroom it is perfect."),
    ],

    # ── S10 Controller Gamepad Digital Game Player (ID 7) ──
    7: [
        ("Controller feels premium", "The grip, weight, and button placement are spot on. Feels like a console controller at a fraction of the price."),
        ("Works with my phone perfectly", "Attached my Android phone and the controller was recognised immediately. Gaming on mobile has never been better."),
        ("Low latency Bluetooth", "Connected instantly and I haven't experienced any noticeable input lag. Excellent for action games."),
        ("Long battery life", "Used it for 8 hours straight in a gaming session. Battery still at 30%. Great endurance."),
        ("Ergonomic design", "The shape fits naturally in my hands. No discomfort even after long gaming sessions."),
        ("Trigger buttons are satisfying", "The trigger buttons have perfect resistance and travel. Makes racing and shooter games much more fun."),
        ("Compatible with many games", "Works with most mobile and PC games. The compatibility is broad and impressive."),
        ("Good build quality", "Feels robust and well-engineered. The joysticks are smooth and precise."),
        ("Minor pairing delay sometimes", "First-time pairing took a couple of tries but after that it connects instantly every time."),
        ("Great value controller", "I've used expensive controllers before and this rivals them in feel and performance. Remarkable value."),
    ],

    # ── Terminator Rechargeable Mosquito Bat (ID 5) ──
    5: [
        ("Zaps mosquitoes instantly", "One swing and done. The electric grid is powerful and effective. Best mosquito bat I've used."),
        ("Rechargeable is so convenient", "No more buying AA batteries every week. Just plug in overnight and it's ready to go."),
        ("Well-built and safe", "The safety mesh prevents accidental contact with the charging grid. Safe around children when used carefully."),
        ("Bright LED torch is a bonus", "The built-in torch is an unexpected but very useful feature. Great for power cuts."),
        ("Lasts a full night", "Charged once and used it for an entire week of evening sessions. Excellent battery retention."),
        ("Perfect weight and grip", "Not too heavy, not too light. The rubber handle gives a secure grip. Swinging feels natural."),
        ("Effective against all insects", "Not just mosquitoes — works on houseflies, gnats, and other flying insects equally well."),
        ("Great gift for parents", "Bought this for my parents. They love it. It has become the most used product in their home."),
        ("Charge indicator is helpful", "The LED charge indicator lets you know when to recharge. A small but thoughtful design touch."),
        ("Excellent for the price", "At this price point, the quality is exceptional. I've recommended it to all my neighbours."),
    ],

    # ── Apple AirPods 4 ANC (ID 3) ──
    3: [
        ("ANC is outstanding", "The active noise cancellation blocks almost everything. I can work peacefully even in a busy café."),
        ("Crystal clear audio", "The sound quality is exceptional. Balanced bass, clear mids, and crisp highs. Music sounds incredible."),
        ("Seamless Apple ecosystem integration", "Switching between my iPhone, Mac, and iPad is instantaneous. The H2 chip makes it effortless."),
        ("Comfortable for long sessions", "Wore these for 5 hours in a row. No ear fatigue whatsoever. The fit is perfect."),
        ("Transparency mode is great for awareness", "Transparency mode lets ambient sound through naturally. Perfect for staying aware in busy streets."),
        ("Battery life exceeded expectations", "Got over 6 hours per charge with ANC on. The case gives multiple additional charges."),
        ("Call quality is superb", "Everyone I spoke to said my voice was crystal clear. The microphone is top-notch."),
        ("Premium unboxing experience", "The packaging and unboxing experience felt premium and thoughtful. Apple's attention to detail shows."),
        ("Fits securely during workouts", "Used these at the gym and they stayed in place through running and weight training. Very secure."),
        ("Worth the premium price", "Expensive but every rupee is justified. These are among the best ANC earbuds available anywhere."),
    ],

    # ── 2.4G Wireless Controller Gamepad Game Stick Lite (ID 2) ──
    2: [
        ("Plug and play, literally", "Plugged the USB receiver into my TV and the controller connected immediately. Absolutely zero setup required."),
        ("Responsive controls", "Button presses register instantly. Very low latency over the 2.4G connection. Great for fast-paced games."),
        ("Comfortable for long sessions", "The ergonomic shape is comfortable to hold for extended gaming. No hand cramps at all."),
        ("Works on multiple platforms", "Compatible with my PC, Android TV, and laptop. Very versatile and convenient."),
        ("Good range", "Works reliably from about 8 metres away. Plenty of range for any living room setup."),
        ("Durable build", "Dropped it a couple of times and it still works perfectly. Build quality is surprisingly solid."),
        ("The D-pad is precise", "Fighting game enthusiast here — the D-pad is responsive and accurate. Very happy with it."),
        ("Battery lasts weeks", "Using it daily and the AA batteries have lasted over three weeks. Very efficient hardware."),
        ("Simple but effective", "No frills, no overcomplicated features. Just a solid, reliable controller that does its job well."),
        ("Great budget option", "I bought an expensive controller for comparison — this one is 80% as good at 20% of the price."),
    ],

    # ── product1 (ID 1) ──
    1: [
        ("Decent starter product", "Does what it says on the tin. A good entry-level option for those trying this category for the first time."),
        ("Good quality for the price", "Wasn't expecting much but I was pleasantly surprised. The quality feels above average for this price range."),
        ("Arrived quickly and well-packed", "The packaging was secure and delivery was speedy. Product was in perfect condition."),
        ("Solid everyday use", "I use this daily and it has held up well over several weeks. No complaints so far."),
        ("Simple and reliable", "Nothing fancy but it works reliably every single time. Consistency is what I value most."),
        ("Good first impression", "The finishing and build gave a positive first impression. Feels well-made and thoughtfully designed."),
        ("Would recommend to friends", "I've already recommended this to two friends. It fulfils its purpose without any fuss."),
        ("Better than expected", "Read a few mixed reviews before buying but my experience has been entirely positive."),
        ("Functional and sturdy", "It handles daily use without any signs of wear. Exactly what I was looking for."),
        ("Value for money", "Priced fairly for what you get. I wouldn't hesitate to buy this again."),
    ],
}

REVIEWER_USERNAMES = ["test", "tester123", "mithu01", "admin"]


class Command(BaseCommand):
    help = "Seed 10 realistic, product-specific reviews for every product."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing reviews before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = Review.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing review(s)."))

        users = list(User.objects.filter(username__in=REVIEWER_USERNAMES))
        if not users:
            self.stderr.write(self.style.ERROR("No matching users found. Run migrations and create users first."))
            return

        products = Product.objects.all()
        total_created = 0
        total_skipped = 0

        for product in products:
            templates = REVIEW_POOL.get(product.pk)
            if not templates:
                self.stdout.write(self.style.WARNING(
                    f"  No review templates for product '{product.name}' (ID {product.pk}). Skipping."
                ))
                continue

            self.stdout.write(f"\nProduct: {product.name} (ID {product.pk})")

            pool = list(templates)  # copy so we don't mutate the original
            random.shuffle(pool)
            available_users = list(users)

            created_count = 0
            for title, comment in pool:
                if not available_users:
                    break  # ran out of distinct users for unique_together constraint

                user = random.choice(available_users)

                # unique_together = [product, user] — skip if already exists
                if Review.objects.filter(product=product, user=user).exists():
                    available_users.remove(user)
                    total_skipped += 1
                    continue

                rating = random.randint(1, 5)

                Review.objects.create(
                    product=product,
                    user=user,
                    rating=rating,
                    title=title,
                    comment=comment,
                    is_approved=True,
                    helpful_count=random.randint(0, 25),
                )
                available_users.remove(user)  # one review per user per product
                created_count += 1
                total_created += 1
                self.stdout.write(
                    f"  [{rating}★] {user.username}: {title}"
                )

            self.stdout.write(self.style.SUCCESS(f"  → {created_count} review(s) created."))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done! {total_created} review(s) created, {total_skipped} skipped (duplicate user/product)."
        ))
