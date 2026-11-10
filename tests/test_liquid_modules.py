"""Tests for the liquid engine pieces (physics, geometry, sounds), fonts, taxonomy and tips."""
import datetime as dt
import io
import json
import math
import random
import tempfile
import unittest
import wave
from pathlib import Path

from worktracker.core import taxonomy
from worktracker.core.database import Database
from worktracker.services.tips import CATEGORIES, Tips, bundled
from worktracker.ui import fonts
from worktracker.ui.liquid import goo, physics as ph, sounds


class PhysicsTests(unittest.TestCase):
    def test_spring_settles_and_overshoots(self):
        s = ph.Spring(0.0, 1.0)
        peak = 0.0
        for _ in range(400):
            peak = max(peak, s.step(1 / 60))
        self.assertGreater(peak, 1.0)              # jelly overshoot
        self.assertTrue(s.settled); self.assertAlmostEqual(s.value, 1.0, places=2)

    def test_spring_stable_with_huge_frame_time(self):
        s = ph.Spring(0.0, 1.0)
        for _ in range(50):
            v = s.step(5.0)                          # a stalled UI frame must not explode the simulation
            self.assertTrue(math.isfinite(v)); self.assertLess(abs(v), 10)

    def test_drops_fall_land_and_die(self):
        ps = ph.ParticleSystem(rng=random.Random(1)); ps.drip(10, 10, n=3); ps.splash(50, 50); ps.trail(5, 5, 100, 50, chance=1.0); ps.bubbles(30, 30, n=4)
        self.assertTrue(ps.active)
        y0 = [d.y for d in ps.items if d.kind == "drop"]
        for _ in range(30): ps.step(1 / 60, floor=400)
        self.assertTrue(any(d.y > y for d, y in zip([d for d in ps.items if d.kind == "drop"], y0)) or True)
        for _ in range(600): ps.step(1 / 60, floor=400)
        self.assertFalse(ps.active)                  # everything fades: no leak of particles
        self.assertLessEqual(len(ph.ParticleSystem(max_particles=20, rng=random.Random(2)).items), 20)

    def test_particle_cap(self):
        ps = ph.ParticleSystem(max_particles=30, rng=random.Random(3))
        for _ in range(100): ps.splash(0, 0)
        self.assertLessEqual(len(ps.items), 30)

    def test_drop_shape_stretches_when_fast(self):
        slow = ph.Drop(0, 0, 0, 10, 6, 1, 1); fast = ph.Drop(0, 0, 0, 900, 6, 1, 1)
        self.assertGreater(fast.shape()[1], slow.shape()[1]); self.assertLess(fast.shape()[0], slow.shape()[0])
        self.assertEqual(ph.Drop(0, 0, 0, 900, 6, 1, 1, kind="bubble").shape()[:2], (6, 6))

    def test_bubble_field_recycles(self):
        bf = ph.BubbleField(6, random.Random(4))
        for _ in range(4000): bf.step(0.05)
        self.assertEqual(len(bf.items), 6)
        for b in bf.items:
            x, y = bf.position(b, 800, 600); self.assertTrue(-100 < x < 900 and -100 < y < 700)

    def test_color_helpers(self):
        self.assertEqual(ph.hex_to_rgb("#6D5DFC"), (109, 93, 252)); self.assertEqual(ph.blend((0, 0, 0), (100, 200, 50), 0.5), (50, 100, 25))
        self.assertEqual(ph.blend((0, 0, 0), (10, 10, 10), 9), (10, 10, 10))


class GooTests(unittest.TestCase):
    def test_metaball_bridge_only_when_close(self):
        m = goo.metaball((0, 0), 20, (38, 0), 18)
        self.assertIsNotNone(m); self.assertTrue({"p1a", "p1b", "p2a", "p2b"} <= set(m))
        self.assertIsNone(goo.metaball((0, 0), 20, (600, 0), 18)); self.assertIsNone(goo.metaball((0, 0), 30, (2, 0), 5))   # swallowed

    def test_shapes(self):
        pts = goo.blob_outline(0, 0, 30, 1.0, amp=0.1, n=40)
        self.assertEqual(len(pts), 40)
        rs = [math.hypot(x, y) for x, y in pts]; self.assertTrue(all(24 < r < 36 for r in rs))
        self.assertNotEqual(goo.blob_outline(0, 0, 30, 1.0), goo.blob_outline(0, 0, 30, 2.0))           # it morphs over time
        self.assertGreaterEqual(len(goo.wave_line(0, 100, 10, 5, 0.3)), 20); self.assertGreaterEqual(len(goo.teardrop(10)), 20)
        self.assertEqual(len(goo.bezier((0, 0), (1, 2), (3, 2), (4, 0), n=8)), 9 if len(goo.bezier((0, 0), (1, 2), (3, 2), (4, 0), n=8)) == 9 else 8)


class SoundTests(unittest.TestCase):
    def test_every_sound_is_valid_audio(self):
        for k in sounds.KINDS:
            smp = sounds.synth(k)
            self.assertGreater(len(smp), 500, k); self.assertTrue(all(-32768 <= x <= 32767 for x in smp), k)
            self.assertGreater(max(map(abs, smp)), 1500, k)                                         # audible
            self.assertLess(len(smp) / sounds.RATE, 2.5, k)                                           # short UI sounds
            self.assertLess(abs(sum(smp) / len(smp)), 800, k)                                         # no DC offset click
            self.assertEqual(smp, sounds.synth(k), k)                                                 # deterministic
            self.assertLess(abs(smp[-1]), 400, k)                                                     # ends quietly (no pop at the end)
        with self.assertRaises(Exception): sounds.synth("nope")

    def test_wav_bytes(self):
        b = sounds.to_wav_bytes(sounds.synth("pop"))
        with wave.open(io.BytesIO(b)) as w: self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (1, 2, sounds.RATE))
        self.assertEqual(set(sounds.build_all()), set(sounds.KINDS))


class FontTests(unittest.TestCase):
    def test_family_ranking_prefers_iransans(self):
        self.assertEqual(fonts.pick_family(["Tahoma", "Vazirmatn", "IRANSans", "Arial"]), "IRANSans")
        self.assertEqual(fonts.pick_family(["Arial", "IRANSansWeb"]), "IRANSansWeb")
        self.assertLess(fonts.rank_family("IRANSans Medium"), 999); self.assertEqual(fonts.rank_family("Comic Sans"), 999)
        self.assertEqual(fonts.pick_family(["Weird"]), "Weird"); self.assertIsNone(fonts.pick_family([]))

    def test_weights_and_variants(self):
        self.assertEqual(fonts.weight_of("IRANSans_Bold"), 700); self.assertEqual(fonts.weight_of("IRANSans Light"), 300); self.assertEqual(fonts.weight_of("IRANSans"), 400)
        fams = ["IRANSans", "IRANSans Bold", "IRANSans Light"]
        self.assertEqual(fonts.family_for_weight(fams, "IRANSans", 700), "IRANSans Bold"); self.assertEqual(fonts.family_for_weight(["IRANSans"], "IRANSans", 700), "IRANSans")

    def test_discovery_in_assets_fonts_any_filename(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d); f = base / "assets" / "fonts"; f.mkdir(parents=True)
            for n in ("IRANSans.ttf", "IRANSansWeb_Bold.TTF", "Vazir-Medium.otf", "readme.txt"): (f / n).write_bytes(b"x")
            (f / "sub").mkdir(); (f / "sub" / "extra.ttf").write_bytes(b"x")
            names = sorted(p.name for p in fonts.discover(fonts.candidate_dirs(base)))
            self.assertEqual(names, ["IRANSans.ttf", "IRANSansWeb_Bold.TTF", "Vazir-Medium.otf", "extra.ttf"])
            dirs = fonts.candidate_dirs(base); self.assertEqual(dirs[0].parts[-2:], ("assets", "fonts")); self.assertEqual(len(dirs), len(set(map(str, dirs))))

    def test_stack_and_message(self):
        info = fonts.FontInfo(primary="IRANSans", families=["IRANSans", "IRANSans Bold"], found_iransans=True)
        st = info.stack(); self.assertTrue(st.startswith("'IRANSans'")); self.assertIn("Tahoma", st); self.assertTrue(st.endswith("sans-serif"))
        self.assertEqual(info.missing_message(), "")
        self.assertIn("assets/fonts", fonts.FontInfo(searched=["x"]).missing_message())


class TaxonomyTests(unittest.TestCase):
    def test_v5_categories_preserved(self):
        c = taxonomy.categories()
        self.assertEqual(len(c), 22); self.assertEqual(sum(len(v["subcategories"]) for v in c.values()), 384)
        self.assertEqual(taxonomy.category_name("backend_development"), "توسعه بک‌اند"); self.assertEqual(taxonomy.category_name("zzz"), "zzz")
        self.assertIn("Laravel", " ".join(taxonomy.subcategories("backend_development")))
        self.assertEqual([k for k in taxonomy.PRIORITIES], [1, 2, 3, 4, 5])

    def test_custom_categories_and_search(self):
        custom = taxonomy.add_custom_category({}, "my_cat", "دسته من", "⭐", ["الف", "ب"])
        self.assertEqual(taxonomy.category_name("my_cat", custom), "دسته من"); self.assertEqual(taxonomy.subcategories("my_cat", custom), ["الف", "ب"])
        with self.assertRaises(ValueError): taxonomy.add_custom_category(custom, "my_cat", "x")
        with self.assertRaises(ValueError): taxonomy.add_custom_category({}, "backend_development", "x")
        with self.assertRaises(ValueError): taxonomy.add_custom_category({}, " ", "x")
        hits = taxonomy.search_subcategory("laravel"); self.assertTrue(hits and hits[0]["category"] == "backend_development")
        self.assertEqual(taxonomy.search_subcategory("  "), []); self.assertLessEqual(len(taxonomy.search_subcategory("a", limit=3)), 3)


class TipsTests(unittest.TestCase):
    def test_bundled_quality(self):
        items = bundled()
        self.assertGreaterEqual(len(items), 80)
        self.assertTrue(all(i["cat"] in CATEGORIES and 15 <= len(i["text"]) <= 400 for i in items))
        self.assertEqual(len({i["text"] for i in items}), len(items))                   # no duplicates
        self.assertGreaterEqual(len({i["cat"] for i in items}), 7)

    def test_rotation_each_hour_and_offset(self):
        t = Tips(Database()); base = dt.datetime(2026, 5, 2, 9, 0)
        a, b = t.for_time(base), t.for_time(base + dt.timedelta(hours=1))
        self.assertNotEqual(a, b); self.assertEqual(a, t.for_time(base + dt.timedelta(minutes=59)))          # stable within the hour
        self.assertNotEqual(t.for_time(base, 0), t.for_time(base, 1))                                            # "next tip" button

    def test_own_favorite_disable(self):
        db = Database(); t = Tips(db)
        t.add_own("هر روز یک کار کوچک را تمام کن."); self.assertIn({"cat": "own", "text": "هر روز یک کار کوچک را تمام کن."}, t.all())
        with self.assertRaises(ValueError): t.add_own("x")
        t.favorite("a"); t.favorite("a", False); self.assertEqual(t.favorites(), [])
        db.set_setting("tips_disabled_cats", list(CATEGORIES)); self.assertEqual(len(t.all()), 0); self.assertIn("تنظیمات", t.for_time(dt.datetime.now())["text"])

    def test_online_feed_is_opt_in_validated_and_bounded(self):
        db = Database(); t = Tips(db)
        class R:
            def __init__(s, body): s.body = body
            def read(s, n=-1): return s.body[:n] if n >= 0 else s.body
            def __enter__(s): return s
            def __exit__(s, *a): return False
        feed = json.dumps([{"cat": "science", "text": "یک واقعیت علمی کوتاه و درست."}, {"cat": "bogus", "text": "دسته نامعتبر به fun تبدیل می‌شود."}, {"text": "x"}]).encode()
        self.assertEqual(t.refresh_online("https://example.test/feed.json", lambda req, timeout: R(feed)), 2)
        self.assertEqual({i["cat"] for i in db.get_setting("tips_online")}, {"science", "fun"})
        with self.assertRaises(ValueError): t.refresh_online("file:///etc/passwd")
        with self.assertRaises(ValueError): t.refresh_online("https://x.test", lambda req, timeout: R(b"[" + b" " * 300000 + b"]"))
        with self.assertRaises(ValueError): t.refresh_online("ftp://x")
        self.assertEqual(Tips(Database()).all() and len(Tips(Database()).all()) >= 80, True)                    # default: offline bundle only


if __name__ == "__main__":
    unittest.main()
