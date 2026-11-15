"""Draw original explanatory README graphics; these are not product screenshots."""

import math
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/assets"
COLORS = ["#42e4c0", "#57c8ff", "#ac91ff", "#ffd278"]


def font(size: int, bold: bool = False):
    candidates = [
        f"C:/Windows/Fonts/{'seguisb' if bold else 'segoeui'}.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size=size)


def icon(draw, kind, x, y, color, scale=1):
    def line(points):
        draw.line(
            [(x + a * scale, y + b * scale) for a, b in points],
            fill=color,
            width=max(2, round(3 * scale)),
            joint="curve",
        )

    if kind == 0:
        line([(0, 0), (28, 0), (40, 12), (40, 48), (0, 48), (0, 0)])
        line([(28, 0), (28, 12), (40, 12)])
        for row in (22, 31, 40):
            line([(9, row), (29, row)])
    elif kind == 1:
        draw.ellipse(
            (x, y, x + 34 * scale, y + 34 * scale), outline=color, width=max(2, round(3 * scale))
        )
        line([(28, 29), (43, 46)])
        line([(10, 18), (15, 23), (26, 11)])
    elif kind == 2:
        for index, height in enumerate((16, 29, 42)):
            left = x + index * 15 * scale
            draw.rounded_rectangle(
                (left, y + (48 - height) * scale, left + 8 * scale, y + 48 * scale),
                radius=2,
                fill=color,
            )
    else:
        line([(20, 0), (20, 31), (8, 19)])
        line([(20, 31), (32, 19)])
        line([(0, 35), (0, 48), (40, 48), (40, 35)])


def features():
    image = Image.new("RGB", (1400, 620), "#0c1728")
    draw = ImageDraw.Draw(image)
    cards = [
        ("Parse with context", "PDF / DOCX / TXT", "Names, email, skills and dated employment"),
        (
            "Explain every point",
            "TRANSPARENT MATCHING",
            "Weighted requirements with source evidence",
        ),
        ("Audit the details", "RECRUITER REVIEW", "Overlap-aware dates and visible skill gaps"),
        ("Keep your evidence", "PORTABLE REPORTS", "Validated JSON, printable HTML and safe CSV"),
    ]
    for index, (title, label, subtitle) in enumerate(cards):
        x, y = 35 + (index % 2) * 685, 30 + (index // 2) * 290
        color = COLORS[index]
        draw.rounded_rectangle(
            (x, y, x + 650, y + 260), radius=22, fill="#142238", outline="#2b3c56", width=2
        )
        draw.rounded_rectangle((x + 25, y + 26, x + 100, y + 104), radius=18, fill="#1e3246")
        icon(draw, index, x + 43, y + 42, color)
        draw.text((x + 125, y + 38), label, font=font(15, True), fill=color)
        draw.text((x + 125, y + 65), title, font=font(30, True), fill="#f1f6ff")
        draw.text((x + 30, y + 149), subtitle, font=font(22), fill="#b7c7db")
        draw.line((x + 30, y + 208, x + 610, y + 208), fill="#2b3c56", width=1)
        draw.text((x + 30, y + 220), f"0{index + 1}  /  ROLELENS", font=font(13, True), fill=color)
    image.save(OUT / "feature-cards.png")


def workflow():
    frames = []
    labels = [
        ("PARSE", "Extract text"),
        ("MATCH", "Apply the rubric"),
        ("INSPECT", "Review evidence"),
        ("EXPORT", "Save the report"),
    ]
    for frame in range(64):
        image = Image.new("RGB", (1200, 350), "#0c1728")
        draw = ImageDraw.Draw(image)
        draw.text((35, 20), "THE ROLELENS WORKFLOW", font=font(18, True), fill="#d9e5f4")
        draw.text(
            (35, 309),
            "Animated pipeline illustration  |  Python engine  |  Human review",
            font=font(15),
            fill="#9aadc7",
        )
        active = frame // 16
        for index, (title, detail) in enumerate(labels):
            x = 35 + index * 295
            color = COLORS[index]
            border = color if active == index else "#2b3c56"
            draw.rounded_rectangle(
                (x, 78, x + 245, 276),
                radius=20,
                fill="#142238",
                outline=border,
                width=3 if active == index else 1,
            )
            icon(draw, index, x + 30, 102, color, 0.9)
            draw.text((x + 30, 169), title, font=font(25, True), fill=color)
            draw.text((x + 30, 213), detail, font=font(17), fill="#cfdaeb")
            if index < 3:
                start = x + 253
                draw.line((start, 177, start + 33, 177), fill="#3b4b64", width=2)
                draw.polygon(
                    [(start + 34, 177), (start + 26, 172), (start + 26, 182)], fill="#3b4b64"
                )
                offset = ((frame % 16) / 15) * 29
                if active == index:
                    px = start + offset
                    radius = 4 + math.sin(frame / 3) * 0.8
                    draw.ellipse((px - radius, 177 - radius, px + radius, 177 + radius), fill=color)
        frames.append(image.convert("P", palette=Image.Palette.ADAPTIVE, colors=128))
    frames[0].save(
        OUT / "workflow.gif",
        save_all=True,
        append_images=frames[1:],
        duration=85,
        loop=0,
        disposal=2,
        optimize=True,
    )


def journey():
    """Animate the implemented ten-stage document-to-review pipeline."""
    stages = [
        ("Define the role", "Skills, priorities and", "experience target.", "INPUTS", 2),
        ("Add a resume", "PDF, DOCX, TXT", "or pasted text.", "INPUTS", 0),
        ("Validate input", "Size, format, pages", "and readable content.", "VALIDATION", 1),
        ("Extract text", "Paragraphs, tables", "and document headers.", "EXTRACTION", 0),
        ("Parse evidence", "Names, email, skills", "and source line context.", "PROVENANCE", 1),
        ("Merge dates", "Unify dated roles;", "remove overlap.", "DATE INTERVALS", 2),
        ("Calculate match", "Weighted skill factors", "plus capped experience.", "0–100 RUBRIC", 2),
        ("Flag skill gaps", "Separate requirements", "from partial evidence.", "FOLLOW-UP", 1),
        ("Save reports", "Validated JSON,", "HTML and safe CSV.", "PORTABLE FILES", 3),
        ("Recruiter review", "Inspect evidence;", "verify candidate claims.", "HUMAN JUDGMENT", 1),
    ]
    palette = [
        "#51bfff",
        "#58d9ff",
        "#41e0ce",
        "#62e7b2",
        "#a1e77b",
        "#69d5f2",
        "#b092ff",
        "#e08dd9",
        "#ffd075",
        "#9edc88",
    ]
    base = Image.new("RGB", (1600, 970), "#07101e")
    draw = ImageDraw.Draw(base)
    draw.text(
        (42, 26),
        "From Resume to Evidence-Led Recruiter Review",
        font=font(41, True),
        fill="#f3f7ff",
    )
    draw.text(
        (44, 86),
        "RoleLens  /  The complete Python document-analysis journey",
        font=font(22),
        fill="#a1b5cc",
    )
    draw.text(
        (44, 137), "01—05  /  INPUT, VALIDATION & EXTRACTION", font=font(16, True), fill="#51d7ee"
    )
    draw.text(
        (350, 537),
        "06—10  /  MATCHING, REPORTS & HUMAN REVIEW",
        font=font(16, True),
        fill="#c1a4ff",
    )
    boxes = []
    for index, (title, first, second, tag, symbol) in enumerate(stages):
        x, y = 40 + index % 5 * 308, 170 + index // 5 * 400
        color = palette[index]
        boxes.append((x, y, x + 286, y + 280))
        draw.rounded_rectangle(boxes[-1], radius=20, fill="#112139", outline="#29435f", width=2)
        draw.ellipse((x + 18, y + 18, x + 64, y + 64), fill="#17324c", outline=color, width=2)
        draw.text((x + 27, y + 25), f"{index + 1:02}", font=font(20, True), fill=color)
        icon(draw, symbol, x + 211, y + 28, color, 1.02)
        if index == 5:
            # Concurrent employment intervals converge into a single union.
            draw.line((x + 100, y + 32, x + 180, y + 32), fill="#67a9ff", width=6)
            draw.line((x + 130, y + 48, x + 195, y + 48), fill="#a894ff", width=6)
            draw.line((x + 100, y + 65, x + 195, y + 65), fill=color, width=6)
        elif index == 8:
            draw.text((x + 94, y + 41), "{ JSON }", font=font(16, True), fill=color)
        elif index == 9:
            draw.ellipse((x + 122, y + 22, x + 144, y + 44), outline=color, width=3)
            draw.arc((x + 108, y + 43, x + 158, y + 77), 180, 360, fill=color, width=3)
        draw.text((x + 18, y + 106), title, font=font(26, True), fill="#f1f6ff")
        draw.text((x + 18, y + 163), first, font=font(20), fill="#baccdf")
        draw.text((x + 18, y + 194), second, font=font(20), fill="#baccdf")
        draw.line((x + 18, y + 239, x + 265, y + 239), fill="#29435f", width=1)
        draw.text((x + 18, y + 251), tag, font=font(12, True), fill=color)
    routes = []
    for index in range(9):
        if index == 4:
            route = [(1415, 453), (1415, 515), (183, 515), (183, 567)]
        else:
            x, y, right, _ = boxes[index]
            route = [(right + 2, y + 138), (right + 20, y + 138)]
        routes.append(route)
        draw.line(route, fill="#35516c", width=3, joint="curve")
        endx, endy = route[-1]
        if index == 4:
            draw.polygon(
                [(endx, endy), (endx - 6, endy - 10), (endx + 6, endy - 10)], fill="#61daca"
            )
        else:
            draw.polygon([(endx, endy), (endx - 8, endy - 5), (endx - 8, endy + 5)], fill="#76afd2")
    draw.text(
        (445, 478),
        "DOCUMENT FACTS → AUDITABLE DECISION SUPPORT",
        font=font(19, True),
        fill="#b8c8dd",
    )
    draw.rounded_rectangle(
        (40, 879, 1558, 944), radius=15, fill="#12253a", outline="#33516a", width=1
    )
    draw.text(
        (64, 900),
        "Review → refine the job rubric → rerun analysis",
        font=font(20, True),
        fill="#78dfc2",
    )
    draw.text(
        (850, 903),
        "Animated illustration · Actual implemented stages",
        font=font(16),
        fill="#a1b5cc",
    )
    frames = []
    shared_palette = base.quantize(colors=192)
    for frame_number in range(100):
        active = frame_number // 10
        glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
        glow_pen = ImageDraw.Draw(glow)
        color = ImageColor.getrgb(palette[active])
        strength = round(110 + 45 * math.sin((frame_number % 10) / 9 * math.pi))
        glow_pen.rounded_rectangle(boxes[active], radius=20, outline=(*color, strength), width=10)
        frame = Image.alpha_composite(
            base.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(8))
        ).convert("RGB")
        pen = ImageDraw.Draw(frame)
        pen.rounded_rectangle(boxes[active], radius=20, outline=palette[active], width=4)
        if active < len(routes):
            route = routes[active]
            distances = [math.dist(a, b) for a, b in zip(route, route[1:], strict=False)]
            travel = (frame_number % 10) / 9 * sum(distances)
            for index, distance in enumerate(distances):
                if travel <= distance:
                    a, b = route[index], route[index + 1]
                    ratio = travel / distance
                    px, py = a[0] + (b[0] - a[0]) * ratio, a[1] + (b[1] - a[1]) * ratio
                    pen.ellipse((px - 6, py - 6, px + 6, py + 6), fill=palette[active])
                    break
                travel -= distance
        frames.append(frame.quantize(palette=shared_palette, dither=Image.Dither.NONE))
    base.save(OUT / "journey-poster.png")
    frames[0].save(
        OUT / "rolelens-journey.gif",
        save_all=True,
        append_images=frames[1:],
        duration=[6000 if index % 10 == 0 else 100 for index in range(len(frames))],
        loop=0,
        disposal=1,
        optimize=True,
    )


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    features()
    workflow()
    journey()
    print("Created feature cards, workflow.gif, journey poster and rolelens-journey.gif")
