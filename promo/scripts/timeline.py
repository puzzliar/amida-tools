"""Single source of truth for the edit (VSE frame numbers, 30 fps, frame 1 = t 0)."""
FPS = 30
TOTAL = 1920  # 64 s

# 3D shots: (name, vse_start, shot_length)  rendered sequences are length+12 for crossfades
SHOTS3D = [
    ("build", 151, 240),
    ("title", 391, 150),
    ("rule", 541, 300),
    ("screens", 841, 90, 160),   # (name, start, length, offset into the rendered sequence)
    ("cards", 1441, 180),
]

D = "PXL_20261017_0"
COLD_OPEN = [(D + "55603782.jpg", 1, 75, (1.00, 1.10), (0.00, -0.03)),   # grandfather clock
             (D + "55648571.jpg", 76, 75, (1.12, 1.02), (0.02, 0.0))]     # crystal chandelier
# live-action chip footage (Drive videos), 0:31-0:45, slowed down with grain/flicker/glitches (prep3.py)
# (name, source video, source start sec, vse_start, length, (scale0, scale1), (dx, dy) drift, speed)
V = "PXL_20261017_0"
CLIPS = [
    ("case_front", V + "40954247.mp4", 9.5, 931, 120, (1.00, 1.08), (0.0, 0.0), 0.6),     # latches undone, lid lifts on the chips
    ("case_angle", V + "41241358.mp4", 12.0, 1051, 90, (1.10, 1.02), (0.02, 0.0), 0.5),   # second angle on the opening case
    ("deal", V + "41614139.mp4", 19.9, 1141, 105, (1.08, 1.16), (-0.02, -0.01), 0.5),     # chips handed across the table
    ("hand_off", V + "42358932.mp4", 9.2, 1246, 105, (1.00, 1.06), (0.0, 0.0), 0.5),      # chips passed hand to hand (FOCUS)
]
# per-clip reframing: crop in on a tracked point, keep an ellipse around it sharp and blur the rest
# track: (clip frame, x, y) in source 1920x1080 pixels; sharp: ellipse half-axes in output pixels
FOCUS = {
    "hand_off": dict(zoom=1.3, sharp=(660, 340), blur=26,
                     track=[(0, 1090, 720), (13, 1060, 740), (26, 1090, 740), (39, 1110, 800), (52, 1090, 790),
                            (65, 1060, 785), (78, 1020, 770), (91, 1010, 740), (104, 980, 720)]),
}
CASE_OPEN = 1025      # frame where the lid comes up (accent hit)
MONTAGE = [  # file, start, length, (scale0, scale1), (dx, dy) drift
    (D + "55553474.jpg", 1351, 30, (1.02, 1.10), (0.0, 0.0)),    # arch into the red room
    (D + "55721011.jpg", 1381, 30, (1.10, 1.02), (0.0, -0.02)),  # throne on the stage
    (D + "55538791.jpg", 1411, 30, (1.02, 1.10), (0.0, 0.0)),    # the black salon
]
END_START = 1621      # key art
END_CARD = 1741       # booking card overlay begins

# (text, start, end, y, size, colour, style)
CAPTIONS = [
    ("集められた、15人。", 22, 72, 0.50, 64, "ivory", "plain"),
    ("生き残るのは──誰だ。", 82, 150, 0.50, 84, "ivory", "plain"),
    ("アミダクジをモチーフにした", 192, 392, 0.255, 44, "ivory", "plain"),
    ("リアル交渉ゲーム", 228, 392, 0.155, 96, "gold", "plain"),
    ("横線を消して、", 556, 718, 0.235, 58, "ivory", "plain"),
    ("中央への〈最短ルート〉を作れ。", 596, 718, 0.140, 72, "gold", "plain"),
    ("最短ルートのプレイヤーの", 736, 842, 0.235, 58, "ivory", "plain"),
    ("メダルを最も多く持つ者が、勝つ。", 752, 842, 0.140, 72, "gold", "plain"),
    ("協力か。　裏切りか。", 850, 930, 0.150, 88, "ivory", "plain"),
    ("嘘と信頼が入り混じる、", 948, 1136, 0.240, 52, "ivory", "plain"),
    ("スリリングな交渉ゲーム。", 962, 1136, 0.145, 80, "gold", "plain"),
    ("その言葉は、真実か。", 1150, 1240, 0.150, 76, "ivory", "plain"),
    ("手を組んだ相手が、最後に裏切る。", 1256, 1346, 0.150, 76, "ivory", "plain"),
    ("疑え。信じろ。──そして、出し抜け。", 1354, 1440, 0.50, 76, "gold", "plain"),
    ("息を呑む駆け引き。張り詰めた沈黙。", 1452, 1534, 0.165, 60, "ivory", "plain"),
    ("騙し合いの頭脳戦を、その身で。", 1540, 1632, 0.165, 72, "gold", "plain"),
]

# sound cues in seconds
HITS = [5.0, 13.0, 18.0, 28.0, (CASE_OPEN - 1) / FPS, 45.0, 48.0, 54.0, 58.0]
RISERS = [(10.6, 13.0), (32.2, (CASE_OPEN - 1) / FPS), (42.8, 45.0), (51.6, 54.0), (56.4, 58.0)]
TICKS = (0.0, 5.0)
OSTINATO = (18.0, 48.0)
HEART = (48.0, 54.0)
SLOWMO = (31.0, 45.0)  # music thins out, static and low pulses take over


def clip_glitches(idx, n):
    """clip-local frames (0-based) where the picture tears for 2 frames"""
    return [0, n // 2 + 7 * idx - 9, n - 4]


GLITCH_TIMES = [(c[3] + f) / FPS for i, c in enumerate(CLIPS) for f in clip_glitches(i, c[4])]
MONTAGE_CUTS = [(c[3] - 1) / FPS for c in CLIPS[1:]] + [(s - 1) / FPS for _, s, *_ in MONTAGE[1:]]
