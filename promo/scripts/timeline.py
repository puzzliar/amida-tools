"""Single source of truth for the edit (VSE frame numbers, 30 fps, frame 1 = t 0)."""
FPS = 30
TOTAL = 1920  # 64 s

# 3D shots: (name, vse_start, shot_length)  rendered sequences are length+12 for crossfades
SHOTS3D = [
    ("build", 151, 240),
    ("title", 391, 150),
    ("rule", 541, 300),
    ("screens", 841, 270),
    ("cards", 1441, 180),
]

D = "PXL_20261017_0"
COLD_OPEN = [(D + "55603782.jpg", 1, 75, (1.00, 1.10), (0.00, -0.03)),   # grandfather clock
             (D + "55648571.jpg", 76, 75, (1.12, 1.02), (0.02, 0.0))]     # crystal chandelier
MONTAGE = [  # file, start, length, (scale0, scale1), (dx, dy) drift
    (D + "55553474.jpg", 1111, 50, (1.02, 1.12), (0.0, 0.0)),    # arch into the red room
    (D + "55614322.jpg", 1161, 30, (1.10, 1.18), (-0.02, 0.0)),  # motion-blurred armchair
    (D + "55547304.jpg", 1191, 45, (1.12, 1.03), (0.03, 0.0)),   # black chair & mirror
    (D + "55721011.jpg", 1236, 45, (1.02, 1.10), (0.0, -0.02)),  # throne on the stage
    (D + "55623591.jpg", 1281, 40, (1.10, 1.02), (-0.03, 0.0)),  # chandelier, red & green
    (D + "55714909.jpg", 1321, 40, (1.03, 1.12), (0.02, 0.01)),  # books & candles
    (D + "55727407.jpg", 1361, 40, (1.12, 1.04), (0.0, 0.02)),   # curtains, leather chair
    (D + "55538791.jpg", 1401, 40, (1.02, 1.10), (0.0, 0.0)),    # the black salon
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
    ("協力か。　裏切りか。", 862, 968, 0.150, 88, "ivory", "plain"),
    ("嘘と信頼が入り混じる、", 980, 1112, 0.240, 52, "ivory", "plain"),
    ("スリリングな交渉ゲーム。", 994, 1112, 0.145, 80, "gold", "plain"),
    ("その言葉は、真実か。", 1118, 1192, 0.50, 76, "ivory", "plain"),
    ("手を組んだ相手が、最後に裏切る。", 1212, 1302, 0.50, 76, "ivory", "plain"),
    ("疑え。信じろ。──そして、出し抜け。", 1326, 1440, 0.50, 76, "gold", "plain"),
    ("息を呑む駆け引き。張り詰めた沈黙。", 1452, 1534, 0.165, 60, "ivory", "plain"),
    ("騙し合いの頭脳戦を、その身で。", 1540, 1632, 0.165, 72, "gold", "plain"),
]

# sound cues in seconds
HITS = [5.0, 13.0, 18.0, 28.0, 37.0, 48.0, 54.0, 58.0]
RISERS = [(10.6, 13.0), (34.8, 37.0), (51.6, 54.0), (56.4, 58.0)]
TICKS = (0.0, 5.0)
OSTINATO = (18.0, 48.0)
HEART = (48.0, 54.0)
MONTAGE_CUTS = [(s - 1) / FPS for _, s, *_ in MONTAGE[1:]]
