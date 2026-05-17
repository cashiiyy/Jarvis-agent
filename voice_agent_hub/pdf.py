"""
GAMAT301 – KTU Question Paper (QP-1) + Full Answer Key
All questions first, then all answers.
"""
import xml.sax.saxutils as sx
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)

# ── Escape helper ──────────────────────────────────────────────────────────────
def e(t): return sx.escape(str(t))

# ── Colors ─────────────────────────────────────────────────────────────────────
NAVY    = HexColor("#0A1628")
DBLUE   = HexColor("#1A3A5C")
MBLUE   = HexColor("#2E6DA4")
LBLUE   = HexColor("#D6EAF8")
DGRN    = HexColor("#145A32")
LGRN    = HexColor("#D5F5E3")
DORG    = HexColor("#784212")
LORG    = HexColor("#FDEBD0")
DPUR    = HexColor("#4A235A")
LPUR    = HexColor("#E8DAEF")
DRED    = HexColor("#7B241C")
LRED    = HexColor("#FADBD8")
GOLD    = HexColor("#D4AC0D")
WHITE   = colors.white
LTGRAY  = HexColor("#F4F6F7")
MDGRAY  = HexColor("#D5D8DC")
DKGRAY  = HexColor("#2C3E50")
ANSBLUE = HexColor("#1B4F72")
ANSBG   = HexColor("#EBF5FB")
STEPBG  = HexColor("#FDFEFE")

W, H = A4
CW = W - 3.0*cm

# ── Styles ─────────────────────────────────────────────────────────────────────
def S(n, **k): return ParagraphStyle(n, **k)

sCover  = S("sCover",  fontSize=18, leading=24, fontName="Helvetica-Bold",
            textColor=WHITE,   alignment=TA_CENTER)
sCoverS = S("sCoverS", fontSize=10, leading=14, fontName="Helvetica",
            textColor=HexColor("#AED6F1"), alignment=TA_CENTER)
sCoverI = S("sCoverI", fontSize=9,  leading=12, fontName="Helvetica-Oblique",
            textColor=HexColor("#AED6F1"), alignment=TA_CENTER)

sSecH   = S("sSecH",  fontSize=13, leading=17, fontName="Helvetica-Bold",
            textColor=WHITE,   alignment=TA_CENTER)
sSecSub = S("sSecSub",fontSize=8.5,leading=12, fontName="Helvetica",
            textColor=HexColor("#AED6F1"), alignment=TA_CENTER)

sModH   = S("sModH",  fontSize=10, leading=14, fontName="Helvetica-Bold",
            textColor=WHITE,   alignment=TA_LEFT)
sModSub = S("sModSub",fontSize=8,  leading=11, fontName="Helvetica",
            textColor=HexColor("#AED6F1"), alignment=TA_LEFT)

sQNum   = S("sQNum",  fontSize=10, leading=13, fontName="Helvetica-Bold",
            textColor=DKGRAY,  alignment=TA_LEFT, spaceBefore=2, spaceAfter=1)
sQText  = S("sQText", fontSize=9,  leading=13, fontName="Helvetica",
            textColor=DKGRAY,  alignment=TA_JUSTIFY, leftIndent=12)
sQSub   = S("sQSub",  fontSize=8.5,leading=12, fontName="Helvetica",
            textColor=DKGRAY,  alignment=TA_LEFT,    leftIndent=24)
sMark   = S("sMark",  fontSize=8.5,leading=12, fontName="Helvetica-Bold",
            textColor=DRED,    alignment=TA_RIGHT)
sOr     = S("sOr",    fontSize=10, leading=13, fontName="Helvetica-Bold",
            textColor=MBLUE,   alignment=TA_CENTER, spaceBefore=4, spaceAfter=4)

sAnsH   = S("sAnsH",  fontSize=11, leading=14, fontName="Helvetica-Bold",
            textColor=WHITE,   alignment=TA_LEFT)
sAnsQ   = S("sAnsQ",  fontSize=9.5,leading=13, fontName="Helvetica-Bold",
            textColor=ANSBLUE, alignment=TA_LEFT, spaceBefore=4, spaceAfter=2)
sStep   = S("sStep",  fontSize=9,  leading=13, fontName="Helvetica-Bold",
            textColor=DKGRAY,  alignment=TA_LEFT, spaceBefore=2)
sCalc   = S("sCalc",  fontSize=9,  leading=13, fontName="Courier",
            textColor=HexColor("#17202A"), alignment=TA_LEFT, leftIndent=12)
sResult = S("sResult",fontSize=9.5,leading=13, fontName="Helvetica-Bold",
            textColor=DGRN,    alignment=TA_LEFT, leftIndent=12)
sNote2  = S("sNote2", fontSize=8,  leading=11, fontName="Helvetica-Oblique",
            textColor=HexColor("#666666"), alignment=TA_LEFT, leftIndent=12)
sBody2  = S("sBody2", fontSize=9,  leading=13, fontName="Helvetica",
            textColor=DKGRAY,  alignment=TA_JUSTIFY)
sTblH2  = S("sTblH2", fontSize=8.5,leading=11, fontName="Helvetica-Bold",
            textColor=WHITE,   alignment=TA_CENTER)
sTblC2  = S("sTblC2", fontSize=8,  leading=11, fontName="Helvetica",
            textColor=DKGRAY,  alignment=TA_CENTER)
sTblEq2 = S("sTblEq2",fontSize=8,  leading=11, fontName="Courier",
            textColor=DKGRAY,  alignment=TA_LEFT)
sFooter = S("sFooter",fontSize=7.5,leading=10, fontName="Helvetica",
            textColor=HexColor("#888888"), alignment=TA_CENTER)
sInstr  = S("sInstr", fontSize=8.5,leading=12, fontName="Helvetica",
            textColor=DKGRAY,  alignment=TA_LEFT)
sInstrB = S("sInstrB",fontSize=8.5,leading=12, fontName="Helvetica-Bold",
            textColor=DKGRAY,  alignment=TA_LEFT)

def SP(h=4): return Spacer(1, h)
def HR(c=MDGRAY, t=0.5): return HRFlowable(width="100%", thickness=t, color=c,
                                            spaceAfter=3, spaceBefore=3)

# ── Layout helpers ─────────────────────────────────────────────────────────────
def banner(title, sub, bg=NAVY):
    d = [[Paragraph(e(title), sCover)], [Paragraph(e(sub), sCoverS)]]
    t = Table(d, colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("TOPPADDING",    (0,0),(-1,-1), 14),
        ("BOTTOMPADDING", (0,0),(-1,-1), 12),
        ("LEFTPADDING",   (0,0),(-1,-1), 14),
        ("RIGHTPADDING",  (0,0),(-1,-1), 14),
    ]))
    return t

def sec_header(label, sub, bg):
    d = [[Paragraph(e(label), sSecH)], [Paragraph(e(sub), sSecSub)]]
    t = Table(d, colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
        ("RIGHTPADDING",  (0,0),(-1,-1), 12),
    ]))
    return t

def mod_strip(label, note, bg):
    d = [[Paragraph(e(label), sModH)], [Paragraph(e(note), sModSub)]]
    t = Table(d, colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
    ]))
    return t

def q_row(qn, marks, parts, indent=True):
    """Build a question row: question number + mark badge | sub-parts."""
    items = []
    for p in parts:
        items.append(Paragraph(e(p), sQSub if indent else sQText))
    badge = Paragraph(f"[{marks} Marks]", sMark)
    head  = Paragraph(e(qn), sQNum)
    inner = [[head, badge]] + [[Paragraph(e(p), sQText), ""] for p in parts]
    col2 = CW - 4.5*cm
    t = Table(inner, colWidths=[col2, 3.5*cm])
    t.setStyle(TableStyle([
        ("TOPPADDING",   (0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("LEFTPADDING",  (0,0),(-1,-1), 4),
        ("RIGHTPADDING", (0,0),(-1,-1), 4),
        ("SPAN",         (0,0), (0,0)),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
    ]))
    return t

def ans_box(qn, lines, bg=ANSBG, border=ANSBLUE):
    """Compact answer block."""
    rows = [[Paragraph(e(qn), sAnsQ)]]
    for ln in lines:
        rows.append([Paragraph(e(ln), sCalc)])
    t = Table(rows, colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), bg),
        ("TOPPADDING",   (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LEFTPADDING",  (0,0),(-1,-1), 10),
        ("RIGHTPADDING", (0,0),(-1,-1), 10),
        ("BOX",          (0,0),(-1,-1), 0.8, border),
        ("LINEBELOW",    (0,0),(0,0),   0.5, border),
    ]))
    return t

def ans_header(label, bg):
    d = [[Paragraph(e(label), sAnsH)]]
    t = Table(d, colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), bg),
        ("TOPPADDING",   (0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",  (0,0),(-1,-1), 12),
        ("RIGHTPADDING", (0,0),(-1,-1), 12),
    ]))
    return t

def result(text):
    return Paragraph(e("=> " + text), sResult)

def step(text):
    return Paragraph(e(text), sStep)

def calc(*lines):
    return [Paragraph(e(l), sCalc) for l in lines]

def note(text):
    return Paragraph(e(text), sNote2)

def body(text):
    return Paragraph(e(text), sBody2)

def sub_table(headers, rows_data, col_widths, hbg=DBLUE):
    hrow = [Paragraph(e(h), sTblH2) for h in headers]
    data = [hrow]
    for r in rows_data:
        data.append([Paragraph(e(c), sTblEq2 if i == 1 else sTblC2)
                     for i, c in enumerate(r)])
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  hbg),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LTGRAY]),
        ("GRID",          (0,0),(-1,-1), 0.4, MDGRAY),
        ("FONTSIZE",      (0,0),(-1,-1), 8),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),
        ("RIGHTPADDING",  (0,0),(-1,-1), 5),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    return t

# ══════════════════════════════════════════════════════════════════════════════
# BUILD STORY
# ══════════════════════════════════════════════════════════════════════════════
story = []

# ─────────────────────────────────────────────────────────────────────────────
# COVER / EXAM HEADER
# ─────────────────────────────────────────────────────────────────────────────
story.append(SP(6))
story.append(banner(
    "KTU CHALLENGE EXAM  |  GAMAT301",
    "Mathematics for Information Science  |  KTU 2024 Scheme  |  Question Paper - 1"
))
story.append(SP(6))

# Exam info box
info = [
    ["Course Code:", "GAMAT301", "Max Marks:", "100"],
    ["Course Title:", "Mathematics for Information Science", "Duration:", "3 Hours"],
    ["Scheme:", "KTU 2024", "Modules Covered:", "1, 2, 3, 4"],
]
it = Table(info, colWidths=[2.8*cm, 7.2*cm, 3.0*cm, 3.2*cm])
it.setStyle(TableStyle([
    ("BACKGROUND",    (0,0),(0,-1), LBLUE),
    ("BACKGROUND",    (2,0),(2,-1), LBLUE),
    ("FONTNAME",      (0,0),(0,-1), "Helvetica-Bold"),
    ("FONTNAME",      (2,0),(2,-1), "Helvetica-Bold"),
    ("FONTNAME",      (1,0),(1,-1), "Helvetica"),
    ("FONTNAME",      (3,0),(3,-1), "Helvetica"),
    ("FONTSIZE",      (0,0),(-1,-1), 8.5),
    ("TOPPADDING",    (0,0),(-1,-1), 4),
    ("BOTTOMPADDING", (0,0),(-1,-1), 4),
    ("LEFTPADDING",   (0,0),(-1,-1), 6),
    ("GRID",          (0,0),(-1,-1), 0.4, MDGRAY),
    ("ROWBACKGROUNDS",(0,0),(-1,-1), [WHITE, LTGRAY, WHITE]),
]))
story.append(it)
story.append(SP(6))

# Instructions
instr_data = [
    [Paragraph("<b>INSTRUCTIONS TO CANDIDATES</b>", sInstrB)],
    [Paragraph(
        "1.  Answer ALL questions in Part A (each carries 4 marks).  "
        "2.  In Part B, answer ONE question from each Module (each full question carries 20 marks).  "
        "3.  Illustrations, diagrams, and neat working are expected wherever applicable.  "
        "4.  Z-table values may be used wherever required.  "
        "5.  Theorems need not be proved unless explicitly asked.",
        sInstr)],
]
instr_t = Table(instr_data, colWidths=[CW])
instr_t.setStyle(TableStyle([
    ("BACKGROUND",   (0,0),(0,0), LBLUE),
    ("BACKGROUND",   (0,1),(-1,-1), LTGRAY),
    ("TOPPADDING",   (0,0),(-1,-1), 5),
    ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ("LEFTPADDING",  (0,0),(-1,-1), 8),
    ("BOX",          (0,0),(-1,-1), 0.8, MDGRAY),
]))
story.append(instr_t)
story.append(SP(8))
story.append(HR(GOLD, 1.5))
story.append(SP(6))

# ─────────────────────────────────────────────────────────────────────────────
# PART A
# ─────────────────────────────────────────────────────────────────────────────
story.append(sec_header(
    "PART  A  —  SHORT ANSWER QUESTIONS",
    "Answer ALL 5 Questions.  Each question carries 4 Marks.  Total: 20 Marks.",
    DBLUE))
story.append(SP(8))

# Q1
story.append(Paragraph("<b>Question 1</b>  [Module 1 — Discrete Random Variables]   <b>[4 Marks]</b>", sQNum))
story.append(Paragraph(
    "A discrete random variable X has the following PMF:  "
    "P(X=1) = 2k,  P(X=2) = 3k,  P(X=3) = 5k,  P(X=4) = k.",
    sQText))
story.append(Paragraph("(a) Find the value of k.", sQSub))
story.append(Paragraph("(b) Find E[X] (Expected Value).", sQSub))
story.append(Paragraph("(c) Find Var(X) (Variance).", sQSub))
story.append(Paragraph("(d) Find P(2 <= X <= 4).", sQSub))
story.append(SP(6))

# Q2
story.append(Paragraph("<b>Question 2</b>  [Module 2 — Normal Distribution]   <b>[4 Marks]</b>", sQNum))
story.append(Paragraph(
    "Given X ~ N(60, 100)  i.e., mean = 60 and variance = 100:", sQText))
story.append(Paragraph("(a) Find P(X < 75).", sQSub))
story.append(Paragraph("(b) Find P(50 < X < 70).", sQSub))
story.append(Paragraph("(c) Find P(X > 55).", sQSub))
story.append(Paragraph("(d) Find the value of c such that P(X < c) = 0.025.", sQSub))
story.append(SP(6))

# Q3
story.append(Paragraph("<b>Question 3</b>  [Module 3 — Inequalities and CLT]   <b>[4 Marks]</b>", sQNum))
story.append(Paragraph(
    "A random variable X has mean mu = 80 and variance sigma^2 = 100.", sQText))
story.append(Paragraph("(a) Using Markov's inequality (X >= 0), find P(X >= 200).", sQSub))
story.append(Paragraph("(b) Using Chebyshev's inequality, find an upper bound for P(|X - 80| >= 30).", sQSub))
story.append(Paragraph("(c) Find the lower bound for P(50 < X < 110).", sQSub))
story.append(Paragraph(
    "(d) A sample of 100 such RVs is taken. Using the CLT, find P(X-bar > 82).", sQSub))
story.append(SP(6))

# Q4
story.append(Paragraph("<b>Question 4</b>  [Module 3 — Poisson Process]   <b>[4 Marks]</b>", sQNum))
story.append(Paragraph(
    "Calls arrive at a helpline as a Poisson Process with rate lambda = 6 calls per hour.", sQText))
story.append(Paragraph("(a) Find the probability of receiving exactly 3 calls in 30 minutes.", sQSub))
story.append(Paragraph("(b) Find the probability of receiving no calls in 10 minutes.", sQSub))
story.append(Paragraph("(c) Find the probability that the time between two consecutive calls exceeds 20 minutes.", sQSub))
story.append(Paragraph("(d) Find the expected waiting time until the 4th call (in minutes).", sQSub))
story.append(SP(6))

# Q5
story.append(Paragraph("<b>Question 5</b>  [Module 4 — Markov Chains]   <b>[4 Marks]</b>", sQNum))
story.append(Paragraph(
    "A Markov Chain on states {1, 2, 3} has Transition Probability Matrix:", sQText))
story.append(Paragraph("P = [ [0, 1, 0], [0.5, 0, 0.5], [0, 1, 0] ]", sQSub))
story.append(Paragraph("(a) Is the chain irreducible? Justify.", sQSub))
story.append(Paragraph("(b) Find the period of state 1.", sQSub))
story.append(Paragraph("(c) Find P(X_2 = 1 | X_0 = 1) using Chapman-Kolmogorov equations.", sQSub))
story.append(Paragraph("(d) Find the stationary distribution pi = (pi_1, pi_2, pi_3).", sQSub))
story.append(SP(8))
story.append(HR(GOLD, 1.5))
story.append(SP(6))

# ─────────────────────────────────────────────────────────────────────────────
# PART B
# ─────────────────────────────────────────────────────────────────────────────
story.append(sec_header(
    "PART  B  —  DESCRIPTIVE QUESTIONS",
    "Answer ONE question from each Module.  Each full question carries 20 Marks.  Total: 80 Marks.",
    DBLUE))
story.append(SP(8))

# ── MODULE 1 ─────────────────────────────────────────────────────────────────
story.append(mod_strip(
    "MODULE 1  —  Discrete Random Variables",
    "Topics: PMF | CDF | Binomial | Poisson | Joint PMF | Marginal | Independence | Expectation",
    DBLUE))
story.append(SP(6))

story.append(Paragraph("<b>Question 6</b>  [Answer this OR Question 7]   <b>[20 Marks]</b>", sQNum))
story.append(SP(3))
story.append(Paragraph("<b>(a)</b>  [10 Marks]  Binomial Distribution", sQNum))
story.append(Paragraph(
    "A fair die is tossed 8 times. A success is defined as getting a number greater than 4 (i.e., 5 or 6). "
    "Let X be the number of successes.  [Probability of success p = 2/6 = 1/3]", sQText))
story.append(Paragraph("(i)   Identify the distribution of X with its parameters.", sQSub))
story.append(Paragraph("(ii)  Find P(X = 3).", sQSub))
story.append(Paragraph("(iii) Find P(X >= 2).", sQSub))
story.append(Paragraph("(iv)  Find E[X] and Var(X).", sQSub))
story.append(Paragraph("(v)   Find P(1 <= X <= 4).", sQSub))
story.append(SP(5))
story.append(Paragraph("<b>(b)</b>  [10 Marks]  Joint PMF", sQNum))
story.append(Paragraph(
    "The joint PMF of two discrete random variables X and Y is given by  "
    "p(x, y) = k * x * y   for x = 1, 2  and  y = 1, 2, 3.", sQText))
story.append(Paragraph("(i)   Find the value of k that makes this a valid PMF.", sQSub))
story.append(Paragraph("(ii)  Construct the joint PMF table.", sQSub))
story.append(Paragraph("(iii) Find the marginal PMFs p_X(x) and p_Y(y).", sQSub))
story.append(Paragraph("(iv)  Are X and Y independent? Justify.", sQSub))
story.append(Paragraph("(v)   Find E[X], E[Y], and E[XY].", sQSub))
story.append(SP(6))
story.append(Paragraph("OR", sOr))
story.append(SP(4))

story.append(Paragraph("<b>Question 7</b>  [Answer this OR Question 6]   <b>[20 Marks]</b>", sQNum))
story.append(SP(3))
story.append(Paragraph("<b>(a)</b>  [10 Marks]  Poisson Distribution", sQNum))
story.append(Paragraph(
    "In a hospital, the number of emergency cases per hour follows a Poisson distribution "
    "with mean lambda = 4.", sQText))
story.append(Paragraph("(i)   Find P(exactly 2 cases in one hour).", sQSub))
story.append(Paragraph("(ii)  Find P(at least 1 case in one hour).", sQSub))
story.append(Paragraph("(iii) Find P(at most 3 cases in one hour).", sQSub))
story.append(Paragraph("(iv)  Find P(exactly 6 cases in 2 hours).", sQSub))
story.append(Paragraph(
    "(v)   A factory has 500 machines; each has a breakdown probability of 0.006 per shift. "
    "Using Poisson as a limit of Binomial, find P(exactly 3 breakdowns in a shift).", sQSub))
story.append(SP(5))
story.append(Paragraph("<b>(b)</b>  [10 Marks]  PMF, Expectation, Variance, CDF", sQNum))
story.append(Paragraph("A random variable X has the following PMF:", sQText))
story.append(SP(2))
story.append(sub_table(
    ["x", "P(X = x)"],
    [["0", "0.05"], ["1", "0.20"], ["2", "0.35"], ["3", "0.25"], ["4", "0.15"]],
    [3*cm, 4*cm], DBLUE))
story.append(SP(4))
story.append(Paragraph("(i)   Verify that this is a valid PMF.", sQSub))
story.append(Paragraph("(ii)  Find E[X] and E[X^2].", sQSub))
story.append(Paragraph("(iii) Find Var(X) and SD(X).", sQSub))
story.append(Paragraph("(iv)  Find E[2X^2 - 3X + 1].", sQSub))
story.append(Paragraph("(v)   Write the CDF F(x) for all values of x.", sQSub))
story.append(SP(6))

# ── MODULE 2 ─────────────────────────────────────────────────────────────────
story.append(PageBreak())
story.append(mod_strip(
    "MODULE 2  —  Continuous Random Variables",
    "Topics: PDF | CDF | Uniform | Normal | Exponential | Joint PDF | Marginal | Memoryless Property",
    DGRN))
story.append(SP(6))

story.append(Paragraph("<b>Question 8</b>  [Answer this OR Question 9]   <b>[20 Marks]</b>", sQNum))
story.append(SP(3))
story.append(Paragraph("<b>(a)</b>  [10 Marks]  Normal Distribution", sQNum))
story.append(Paragraph(
    "The marks scored by students in an exam follow a Normal distribution "
    "with mean mu = 65 and standard deviation sigma = 12.", sQText))
story.append(Paragraph("(i)   Find P(marks < 77).", sQSub))
story.append(Paragraph("(ii)  Find P(53 < marks < 89).", sQSub))
story.append(Paragraph("(iii) Find P(marks > 59).", sQSub))
story.append(Paragraph("(iv)  Find the minimum marks needed to be in the top 10% of students.", sQSub))
story.append(Paragraph(
    "(v)   Using the 68-95-99.7 rule, what percentage of students score between 41 and 89?", sQSub))
story.append(SP(5))
story.append(Paragraph("<b>(b)</b>  [10 Marks]  Joint PDF", sQNum))
story.append(Paragraph(
    "The joint PDF of (X, Y) is:  f(x, y) = k * x^2 * y   for  0 < x < 1  and  0 < y < 2.", sQText))
story.append(Paragraph("(i)   Find k.", sQSub))
story.append(Paragraph("(ii)  Find the marginal PDFs f_X(x) and f_Y(y).", sQSub))
story.append(Paragraph("(iii) Are X and Y independent? Justify.", sQSub))
story.append(Paragraph("(iv)  Find E[X] and E[Y].", sQSub))
story.append(Paragraph("(v)   Find P(X < 0.5, Y < 1).", sQSub))
story.append(SP(6))
story.append(Paragraph("OR", sOr))
story.append(SP(4))

story.append(Paragraph("<b>Question 9</b>  [Answer this OR Question 8]   <b>[20 Marks]</b>", sQNum))
story.append(SP(3))
story.append(Paragraph("<b>(a)</b>  [10 Marks]  Exponential Distribution", sQNum))
story.append(Paragraph(
    "The lifetime (in years) of an electronic component X follows an Exponential distribution "
    "with mean 4 years.", sQText))
story.append(Paragraph("(i)   Find the rate parameter lambda and write f(x) and F(x).", sQSub))
story.append(Paragraph("(ii)  Find P(X > 5)  [component survives beyond 5 years].", sQSub))
story.append(Paragraph("(iii) Find P(X < 2)  [component fails within 2 years].", sQSub))
story.append(Paragraph(
    "(iv)  Given that the component has already lasted 3 years, find P(it lasts another 4 years). "
    "State the property used.", sQSub))
story.append(Paragraph("(v)   Find the median lifetime and Var(X).", sQSub))
story.append(SP(5))
story.append(Paragraph("<b>(b)</b>  [10 Marks]  Uniform Distribution and PDF", sQNum))
story.append(Paragraph(
    "A random variable Y has the following PDF:  "
    "f(y) = c * (1 - y)   for  0 < y < 1,   and  0  otherwise.", sQText))
story.append(Paragraph("(i)   Find c to make f(y) a valid PDF.", sQSub))
story.append(Paragraph("(ii)  Find the CDF F(y).", sQSub))
story.append(Paragraph("(iii) Find E[Y] and E[Y^2].", sQSub))
story.append(Paragraph("(iv)  Find Var(Y) and SD(Y).", sQSub))
story.append(Paragraph("(v)   Find P(0.25 < Y < 0.75).", sQSub))
story.append(SP(6))

# ── MODULE 3 ─────────────────────────────────────────────────────────────────
story.append(PageBreak())
story.append(mod_strip(
    "MODULE 3  —  Limit Theorems  &  Stochastic Processes",
    "Topics: Markov Inequality | Chebyshev | CLT | Poisson Process | Interarrival Times | Counting Process",
    DORG))
story.append(SP(6))

story.append(Paragraph("<b>Question 10</b>  [Answer this OR Question 11]   <b>[20 Marks]</b>", sQNum))
story.append(SP(3))
story.append(Paragraph("<b>(a)</b>  [10 Marks]  Inequalities and CLT", sQNum))
story.append(Paragraph(
    "The weight of packages produced by a factory has mean mu = 10 kg and "
    "standard deviation sigma = 0.5 kg.", sQText))
story.append(Paragraph("(i)   Using Markov's inequality, find an upper bound for P(X >= 30).   [Assume X >= 0]", sQSub))
story.append(Paragraph("(ii)  Using Chebyshev's inequality, find an upper bound for P(|X - 10| >= 2).", sQSub))
story.append(Paragraph("(iii) Find a lower bound for P(9 < X < 11).", sQSub))
story.append(Paragraph(
    "(iv)  A sample of 64 packages is selected. Using the CLT, "
    "find P(9.8 < X-bar < 10.2).", sQSub))
story.append(Paragraph(
    "(v)   Find the minimum sample size n such that P(|X-bar - 10| < 0.1) >= 0.95.", sQSub))
story.append(SP(5))
story.append(Paragraph("<b>(b)</b>  [10 Marks]  Poisson Process", sQNum))
story.append(Paragraph(
    "Packets arrive at a network router as a Poisson Process with rate lambda = 8 packets per minute.", sQText))
story.append(Paragraph("(i)   Find the probability that exactly 10 packets arrive in 1 minute.", sQSub))
story.append(Paragraph("(ii)  Find the probability that exactly 5 packets arrive in 30 seconds.", sQSub))
story.append(Paragraph("(iii) Find the probability that no packets arrive in 15 seconds.", sQSub))
story.append(Paragraph(
    "(iv)  Find the probability that the time between two consecutive packets exceeds 15 seconds.", sQSub))
story.append(Paragraph("(v)   Find the expected time (in seconds) until the 6th packet arrives.", sQSub))
story.append(SP(6))
story.append(Paragraph("OR", sOr))
story.append(SP(4))

story.append(Paragraph("<b>Question 11</b>  [Answer this OR Question 10]   <b>[20 Marks]</b>", sQNum))
story.append(SP(3))
story.append(Paragraph("<b>(a)</b>  [10 Marks]  Central Limit Theorem", sQNum))
story.append(Paragraph(
    "The monthly income of workers in a city has mean Rs. 25,000 and "
    "standard deviation Rs. 5,000.", sQText))
story.append(Paragraph(
    "(i)   A random sample of 100 workers is chosen. Using CLT, "
    "find P(24,500 < X-bar < 25,500).", sQSub))
story.append(Paragraph(
    "(ii)  Find P(total income of 100 workers exceeds Rs. 25,60,000).", sQSub))
story.append(Paragraph(
    "(iii) Find the minimum sample size n so that P(|X-bar - 25,000| < 500) >= 0.99.", sQSub))
story.append(Paragraph(
    "(iv)  Using Chebyshev for any distribution with same mu and sigma, "
    "find the lower bound of P(|X-bar - 25,000| < 1,000) for n = 25.", sQSub))
story.append(Paragraph(
    "(v)   State the Central Limit Theorem in full and explain its significance.", sQSub))
story.append(SP(5))
story.append(Paragraph("<b>(b)</b>  [10 Marks]  Poisson Process and Interarrival Times", sQNum))
story.append(Paragraph(
    "Customers arrive at a bank as a Poisson Process with rate lambda = 3 per hour.", sQText))
story.append(Paragraph("(i)   Find P(exactly 4 customers in 2 hours).", sQSub))
story.append(Paragraph("(ii)  Find P(at least 1 customer in 30 minutes).", sQSub))
story.append(Paragraph("(iii) Find P(the first customer arrives after 30 minutes).", sQSub))
story.append(Paragraph(
    "(iv)  Find P(time between 2nd and 3rd customer is less than 15 minutes).", sQSub))
story.append(Paragraph("(v)   Find the expected waiting time for the 5th customer (in hours).", sQSub))
story.append(SP(6))

# ── MODULE 4 ─────────────────────────────────────────────────────────────────
story.append(PageBreak())
story.append(mod_strip(
    "MODULE 4  —  Markov Chains",
    "Topics: TPM | Random Walk | Chapman-Kolmogorov | Classification of States | Stationary Distribution",
    DPUR))
story.append(SP(6))

story.append(Paragraph("<b>Question 12</b>  [Answer this OR Question 13]   <b>[20 Marks]</b>", sQNum))
story.append(SP(3))
story.append(Paragraph("<b>(a)</b>  [10 Marks]  Markov Chain Analysis — Full", sQNum))
story.append(Paragraph(
    "A Markov Chain on states {0, 1, 2} has the following Transition Probability Matrix:", sQText))
story.append(Paragraph(
    "P = [ [0.5, 0.4, 0.1], [0.2, 0.5, 0.3], [0.1, 0.3, 0.6] ]", sQSub))
story.append(Paragraph("(i)   Is the chain irreducible? Justify.", sQSub))
story.append(Paragraph("(ii)  Find the 2-step transition probability P(X_2 = 2 | X_0 = 0) using C-K.", sQSub))
story.append(Paragraph("(iii) Find the stationary distribution pi = (pi_0, pi_1, pi_2).", sQSub))
story.append(Paragraph("(iv)  In the long run, what fraction of time does the chain spend in state 1?", sQSub))
story.append(Paragraph("(v)   Find the mean return time to state 0.", sQSub))
story.append(SP(5))
story.append(Paragraph("<b>(b)</b>  [10 Marks]  Classification of States", sQNum))
story.append(Paragraph(
    "A Markov Chain on states {1, 2, 3, 4, 5} has the following TPM:", sQText))
story.append(Paragraph(
    "P = [ [0.5, 0.5, 0, 0, 0],  [0.3, 0.7, 0, 0, 0],  "
    "[0.2, 0.1, 0.3, 0.2, 0.2],  [0, 0, 0, 0.6, 0.4],  [0, 0, 0, 0.5, 0.5] ]", sQSub))
story.append(Paragraph("(i)   Find all communicating classes.", sQSub))
story.append(Paragraph("(ii)  Identify all recurrent and transient states.", sQSub))
story.append(Paragraph("(iii) Is the chain irreducible?", sQSub))
story.append(Paragraph("(iv)  Find the stationary distribution for each recurrent class.", sQSub))
story.append(Paragraph("(v)   Find P(X_2 = 2 | X_0 = 1).", sQSub))
story.append(SP(6))
story.append(Paragraph("OR", sOr))
story.append(SP(4))

story.append(Paragraph("<b>Question 13</b>  [Answer this OR Question 12]   <b>[20 Marks]</b>", sQNum))
story.append(SP(3))
story.append(Paragraph("<b>(a)</b>  [10 Marks]  Stock Market Markov Chain + Stationary Distribution", sQNum))
story.append(Paragraph(
    "A stock market can be in three states: Bull (B), Bear (R), Flat (F). "
    "The daily transition probabilities are:", sQText))
story.append(Paragraph(
    "P = [ [0.7, 0.2, 0.1], [0.3, 0.5, 0.2], [0.2, 0.3, 0.5] ]   "
    "(Rows/Cols: B, R, F)", sQSub))
story.append(Paragraph("(i)   Find the 2-step probability P(Bull after 2 days | Bull today).", sQSub))
story.append(Paragraph("(ii)  Find the 2-step probability P(Bull after 2 days | Flat today).", sQSub))
story.append(Paragraph("(iii) Find the stationary distribution pi = (pi_B, pi_R, pi_F).", sQSub))
story.append(Paragraph("(iv)  In the long run, what fraction of days is the market in Bull state?", sQSub))
story.append(Paragraph("(v)   Find the mean return time to the Bull state.", sQSub))
story.append(SP(5))
story.append(Paragraph("<b>(b)</b>  [10 Marks]  Random Walk and State Classification", sQNum))
story.append(Paragraph(
    "Consider a Random Walk on states {0, 1, 2, 3, 4} where:  "
    "State 0 is absorbing (stays at 0).  "
    "State 4 is absorbing (stays at 4).  "
    "From states 1, 2, 3: move right (+1) with probability p = 0.6, left (-1) with q = 0.4.", sQText))
story.append(Paragraph("(i)   Write the complete 5x5 Transition Probability Matrix.", sQSub))
story.append(Paragraph("(ii)  Find all communicating classes.", sQSub))
story.append(Paragraph("(iii) Classify ALL states as recurrent or transient.", sQSub))
story.append(Paragraph("(iv)  Starting from state 2, find P(X_2 = 3).", sQSub))
story.append(Paragraph("(v)   Is this chain irreducible? Explain.", sQSub))
story.append(SP(8))
story.append(HR(GOLD, 2))
story.append(SP(4))
story.append(Paragraph("*** END OF QUESTION PAPER ***", sFooter))
story.append(Paragraph(
    "GAMAT301  |  KTU 2024 Scheme  |  Question Paper - 1  |  Max Marks: 100  |  Duration: 3 Hours",
    sFooter))

# ═════════════════════════════════════════════════════════════════════════════
# ████████████████████  ANSWER KEY  ████████████████████
# ═════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story.append(SP(6))
story.append(banner("ANSWER  KEY  —  QP 1  (GAMAT301)",
    "Complete Step-by-Step Solutions  |  All Parts  |  Part A then Part B"))
story.append(SP(8))
story.append(HR(GOLD, 1.5))
story.append(SP(6))
story.append(sec_header(
    "PART  A  —  ANSWER KEY",
    "All 5 Questions Solved in Full Detail",
    DBLUE))
story.append(SP(8))

# ── PART A ANSWERS ────────────────────────────────────────────────────────────

story.append(ans_header("ANSWER  1  —  PMF, E[X], Var(X)  [Module 1]", DBLUE))
story.append(SP(4))
story.append(step("(a) Find k:"))
for l in calc(
    "Sum of all probabilities = 1",
    "2k + 3k + 5k + k = 1",
    "11k = 1",
    "k = 1/11"):
    story.append(l)
story.append(result("k = 1/11 = 0.0909"))
story.append(SP(4))
story.append(step("(b) Find E[X]:"))
for l in calc(
    "E[X] = 1*(2/11) + 2*(3/11) + 3*(5/11) + 4*(1/11)",
    "     = 2/11 + 6/11 + 15/11 + 4/11",
    "     = 27/11"):
    story.append(l)
story.append(result("E[X] = 27/11 = 2.4545"))
story.append(SP(4))
story.append(step("(c) Find Var(X):"))
for l in calc(
    "E[X^2] = 1^2*(2/11) + 2^2*(3/11) + 3^2*(5/11) + 4^2*(1/11)",
    "       = 2/11 + 12/11 + 45/11 + 16/11 = 75/11",
    "Var(X) = E[X^2] - (E[X])^2",
    "       = 75/11 - (27/11)^2 = 75/11 - 729/121",
    "       = 825/121 - 729/121 = 96/121"):
    story.append(l)
story.append(result("Var(X) = 96/121 = 0.7934"))
story.append(SP(4))
story.append(step("(d) Find P(2 <= X <= 4):"))
for l in calc(
    "P(2<=X<=4) = P(X=2) + P(X=3) + P(X=4)",
    "           = 3/11 + 5/11 + 1/11 = 9/11"):
    story.append(l)
story.append(result("P(2 <= X <= 4) = 9/11 = 0.8182"))
story.append(SP(8))

story.append(ans_header("ANSWER  2  —  Normal Distribution N(60, 100)  [Module 2]", DGRN))
story.append(SP(4))
story.append(note("mu = 60, sigma^2 = 100, sigma = 10. Standardize: Z = (X - 60) / 10"))
story.append(SP(3))
story.append(step("(a) P(X < 75):"))
for l in calc(
    "Z = (75 - 60) / 10 = 1.5",
    "P(X < 75) = Phi(1.5) = 0.9332"):
    story.append(l)
story.append(result("P(X < 75) = 0.9332"))
story.append(SP(3))
story.append(step("(b) P(50 < X < 70):"))
for l in calc(
    "z1 = (50 - 60)/10 = -1.0     z2 = (70 - 60)/10 = 1.0",
    "P(50 < X < 70) = Phi(1) - Phi(-1) = 0.8413 - 0.1587"):
    story.append(l)
story.append(result("P(50 < X < 70) = 0.6826"))
story.append(SP(3))
story.append(step("(c) P(X > 55):"))
for l in calc(
    "Z = (55 - 60)/10 = -0.5",
    "P(X > 55) = P(Z > -0.5) = 1 - Phi(-0.5) = Phi(0.5) = 0.6915"):
    story.append(l)
story.append(result("P(X > 55) = 0.6915"))
story.append(SP(3))
story.append(step("(d) Find c such that P(X < c) = 0.025:"))
for l in calc(
    "P(X < c) = 0.025 => P(Z < z) = 0.025",
    "From Z-table: z = -1.96",
    "c = mu + z * sigma = 60 + (-1.96)(10) = 60 - 19.6"):
    story.append(l)
story.append(result("c = 40.4"))
story.append(SP(8))

story.append(ans_header("ANSWER  3  —  Inequalities and CLT  [Module 3]", HexColor("#784212")))
story.append(SP(4))
story.append(note("mu = 80, sigma^2 = 100, sigma = 10"))
story.append(SP(3))
story.append(step("(a) Markov's Inequality: P(X >= 200)"))
for l in calc(
    "P(X >= a) <= E[X] / a",
    "P(X >= 200) <= 80 / 200 = 0.4"):
    story.append(l)
story.append(result("P(X >= 200) <= 0.40  (Upper Bound)"))
story.append(SP(3))
story.append(step("(b) Chebyshev: P(|X - 80| >= 30)"))
for l in calc(
    "P(|X - mu| >= eps) <= sigma^2 / eps^2",
    "P(|X - 80| >= 30) <= 100 / (30)^2 = 100/900 = 1/9"):
    story.append(l)
story.append(result("P(|X - 80| >= 30) <= 1/9 = 0.1111"))
story.append(SP(3))
story.append(step("(c) Lower bound for P(50 < X < 110):"))
for l in calc(
    "P(50 < X < 110) = P(|X - 80| < 30)",
    "                >= 1 - sigma^2/eps^2 = 1 - 1/9 = 8/9"):
    story.append(l)
story.append(result("P(50 < X < 110) >= 8/9 = 0.8889"))
story.append(SP(3))
story.append(step("(d) CLT: P(X-bar > 82) with n = 100:"))
for l in calc(
    "By CLT: X-bar ~ N(80, 100/100) = N(80, 1)   SD of X-bar = 1",
    "Z = (82 - 80) / (10/sqrt(100)) = 2/1 = 2.0",
    "P(X-bar > 82) = P(Z > 2) = 1 - Phi(2) = 1 - 0.9772"):
    story.append(l)
story.append(result("P(X-bar > 82) = 0.0228"))
story.append(SP(8))

story.append(ans_header("ANSWER  4  —  Poisson Process  [Module 3]", HexColor("#784212")))
story.append(SP(4))
story.append(note("lambda = 6/hr = 0.1/min. All times converted to minutes."))
story.append(SP(3))
story.append(step("(a) P(exactly 3 calls in 30 min): lambda*t = 0.1*30 = 3"))
for l in calc(
    "P(N(30) = 3) = e^(-3) * 3^3 / 3!",
    "             = e^(-3) * 27 / 6",
    "             = 0.04979 * 4.5 = 0.2240"):
    story.append(l)
story.append(result("P(N(30) = 3) = 0.2240"))
story.append(SP(3))
story.append(step("(b) P(no calls in 10 min): lambda*t = 0.1*10 = 1"))
for l in calc(
    "P(N(10) = 0) = e^(-1) * 1^0 / 0! = e^(-1)"):
    story.append(l)
story.append(result("P(N(10) = 0) = e^(-1) = 0.3679"))
story.append(SP(3))
story.append(step("(c) P(interarrival time T > 20 min): T ~ Exp(0.1/min)"))
for l in calc(
    "P(T > 20) = e^(-lambda * t) = e^(-0.1 * 20) = e^(-2)"):
    story.append(l)
story.append(result("P(T > 20) = e^(-2) = 0.1353"))
story.append(SP(3))
story.append(step("(d) Expected waiting time for 4th call:"))
for l in calc(
    "S_4 = T_1 + T_2 + T_3 + T_4   where each T_i ~ Exp(0.1/min)",
    "E[S_4] = 4 / lambda = 4 / 0.1 = 40 minutes"):
    story.append(l)
story.append(result("E[S_4] = 40 minutes"))
story.append(SP(8))

story.append(ans_header("ANSWER  5  —  Markov Chain Properties  [Module 4]", DPUR))
story.append(SP(4))
story.append(note("P = [[0, 1, 0], [0.5, 0, 0.5], [0, 1, 0]]   States: {1, 2, 3}"))
story.append(SP(3))
story.append(step("(a) Irreducibility:"))
for l in calc(
    "From 1: 1->2 (p_12=1)  From 2: 2->1 (p_21=0.5), 2->3 (p_23=0.5)",
    "From 3: 3->2 (p_32=1)  So 1->2->3 and 3->2->1",
    "All states communicate: 1<->2<->3"):
    story.append(l)
story.append(result("YES — the chain is IRREDUCIBLE (all states communicate)"))
story.append(SP(3))
story.append(step("(b) Period of state 1:"))
for l in calc(
    "Possible returns to state 1:",
    "  1 -> 2 -> 1          (2 steps: p_11^(2) > 0)",
    "  1 -> 2 -> 3 -> 2 -> 1 (4 steps: p_11^(4) > 0)",
    "d(1) = gcd{2, 4, 6, ...} = 2"):
    story.append(l)
story.append(result("Period of state 1 = 2  (state 1 is PERIODIC)"))
story.append(SP(3))
story.append(step("(c) P(X_2 = 1 | X_0 = 1) using Chapman-Kolmogorov:"))
for l in calc(
    "p_11^(2) = SUM_k  p_1k * p_k1",
    "         = p_11*p_11 + p_12*p_21 + p_13*p_31",
    "         = (0)(0) + (1)(0.5) + (0)(0)",
    "         = 0.5"):
    story.append(l)
story.append(result("P(X_2 = 1 | X_0 = 1) = 0.5"))
story.append(SP(3))
story.append(step("(d) Stationary distribution: solve pi*P = pi, sum = 1"))
for l in calc(
    "Equation 1: pi_1 = 0*pi_1 + 0.5*pi_2 + 0*pi_3  =>  pi_1 = 0.5*pi_2",
    "Equation 2: pi_2 = 1*pi_1 + 0*pi_2 + 1*pi_3    =>  pi_2 = pi_1 + pi_3",
    "Equation 3: pi_3 = 0*pi_1 + 0.5*pi_2 + 0*pi_3  =>  pi_3 = 0.5*pi_2",
    "",
    "From Eq1 and Eq3:  pi_1 = pi_3 = 0.5*pi_2",
    "Substituting in Eq2:  pi_2 = pi_1 + pi_1 = 2*pi_1",
    "Normalization:  pi_1 + 2*pi_1 + pi_1 = 4*pi_1 = 1  =>  pi_1 = 1/4"):
    story.append(l)
story.append(result("pi_1 = 1/4 = 0.25,   pi_2 = 1/2 = 0.50,   pi_3 = 1/4 = 0.25"))
story.append(SP(8))

# ── PART B ANSWERS ────────────────────────────────────────────────────────────
story.append(PageBreak())
story.append(sec_header(
    "PART  B  —  ANSWER KEY",
    "Detailed Solutions for all Module Questions",
    DBLUE))
story.append(SP(8))

story.append(ans_header("MODULE 1  —  ANSWER 6(a): Binomial Distribution  [Die Toss]", DBLUE))
story.append(SP(4))
story.append(note("n=8 tosses, success = {5 or 6}, p = 2/6 = 1/3, q = 2/3. X ~ B(8, 1/3)"))
story.append(SP(3))
story.append(step("(i) Distribution: X ~ Binomial(n=8, p=1/3)"))
story.append(SP(2))
story.append(step("(ii) P(X = 3):"))
for l in calc(
    "P(X=3) = C(8,3) * (1/3)^3 * (2/3)^5",
    "       = 56 * (1/27) * (32/243)",
    "       = 56 * 32 / 6561",
    "       = 1792 / 6561 = 0.2731"):
    story.append(l)
story.append(result("P(X = 3) = 0.2731"))
story.append(SP(3))
story.append(step("(iii) P(X >= 2) = 1 - P(X=0) - P(X=1):"))
for l in calc(
    "P(X=0) = C(8,0)*(1/3)^0*(2/3)^8 = (2/3)^8 = 256/6561 = 0.0390",
    "P(X=1) = C(8,1)*(1/3)^1*(2/3)^7 = 8*(1/3)*(128/2187) = 1024/6561 = 0.1561",
    "P(X>=2) = 1 - 0.0390 - 0.1561 = 0.8049"):
    story.append(l)
story.append(result("P(X >= 2) = 0.8049"))
story.append(SP(3))
story.append(step("(iv) Mean and Variance:"))
for l in calc(
    "E[X] = n*p = 8 * (1/3) = 8/3 = 2.6667",
    "Var(X) = n*p*q = 8 * (1/3) * (2/3) = 16/9 = 1.7778",
    "SD(X) = sqrt(16/9) = 4/3 = 1.3333"):
    story.append(l)
story.append(result("E[X] = 8/3 = 2.667,   Var(X) = 16/9 = 1.778"))
story.append(SP(3))
story.append(step("(v) P(1 <= X <= 4):"))
for l in calc(
    "P(X=2) = C(8,2)*(1/3)^2*(2/3)^6 = 28*(1/9)*(64/729) = 1792/6561 = 0.2731",
    "P(X=4) = C(8,4)*(1/3)^4*(2/3)^4 = 70*(1/81)*(16/81) = 1120/6561 = 0.1707",
    "P(1<=X<=4) = P(X=1)+P(X=2)+P(X=3)+P(X=4)",
    "           = 0.1561 + 0.2731 + 0.2731 + 0.1707 = 0.8730"):
    story.append(l)
story.append(result("P(1 <= X <= 4) = 0.8730"))
story.append(SP(8))

story.append(ans_header("MODULE 1  —  ANSWER 6(b): Joint PMF  p(x,y) = k*x*y", DBLUE))
story.append(SP(4))
story.append(step("(i) Find k:"))
for l in calc(
    "SUM_{x=1,2} SUM_{y=1,2,3} k*x*y = 1",
    "k * [1*1 + 1*2 + 1*3 + 2*1 + 2*2 + 2*3] = 1",
    "k * [1 + 2 + 3 + 2 + 4 + 6] = 1",
    "k * 18 = 1  =>  k = 1/18"):
    story.append(l)
story.append(result("k = 1/18"))
story.append(SP(3))
story.append(step("(ii) Joint PMF Table  p(x,y) = xy/18:"))
story.append(SP(2))
story.append(sub_table(
    ["x \\ y", "y = 1", "y = 2", "y = 3", "p_X(x)"],
    [["x = 1", "1/18 = 0.056", "2/18 = 0.111", "3/18 = 0.167", "6/18 = 1/3"],
     ["x = 2", "2/18 = 0.111", "4/18 = 0.222", "6/18 = 0.333", "12/18 = 2/3"],
     ["p_Y(y)", "3/18 = 1/6",  "6/18 = 1/3",   "9/18 = 1/2",   "1"]],
    [2.2*cm, 3.2*cm, 3.2*cm, 3.2*cm, 2.8*cm], DBLUE))
story.append(SP(3))
story.append(step("(iii) Marginal PMFs:"))
for l in calc(
    "p_X(1) = 1/18 + 2/18 + 3/18 = 6/18 = 1/3",
    "p_X(2) = 2/18 + 4/18 + 6/18 = 12/18 = 2/3",
    "",
    "p_Y(1) = 1/18 + 2/18 = 3/18 = 1/6",
    "p_Y(2) = 2/18 + 4/18 = 6/18 = 1/3",
    "p_Y(3) = 3/18 + 6/18 = 9/18 = 1/2"):
    story.append(l)
story.append(SP(3))
story.append(step("(iv) Independence Check:"))
for l in calc(
    "p_X(x) * p_Y(y) = (x/3) * (y/6) * 3 = xy/18 = p(x,y)  [Check for all x,y]",
    "Example: p_X(1)*p_Y(1) = (1/3)*(1/6) = 1/18 = p(1,1) VERIFIED",
    "Example: p_X(2)*p_Y(3) = (2/3)*(1/2) = 1/3 = 6/18 = p(2,3) VERIFIED"):
    story.append(l)
story.append(result("X and Y are INDEPENDENT (p(x,y) = p_X(x) * p_Y(y) for all x,y)"))
story.append(SP(3))
story.append(step("(v) E[X], E[Y], E[XY]:"))
for l in calc(
    "E[X] = 1*(1/3) + 2*(2/3) = 1/3 + 4/3 = 5/3 = 1.6667",
    "E[Y] = 1*(1/6) + 2*(1/3) + 3*(1/2) = 1/6 + 2/6 + 9/6... ",
    "     = 1/6 + 4/6 + 9/6 = 14/6 = 7/3 = 2.3333",
    "",
    "Since X,Y independent:  E[XY] = E[X] * E[Y]",
    "E[XY] = (5/3) * (7/3) = 35/9 = 3.8889"):
    story.append(l)
story.append(result("E[X] = 5/3,   E[Y] = 7/3,   E[XY] = 35/9"))
story.append(SP(8))

story.append(ans_header("MODULE 1  —  ANSWER 7(a): Poisson Distribution [Hospital]", DBLUE))
story.append(SP(4))
story.append(note("X ~ Poisson(lambda = 4). P(X=k) = e^(-4)*4^k/k!"))
story.append(SP(3))
story.append(step("(i) P(exactly 2 cases):"))
for l in calc(
    "P(X=2) = e^(-4) * 4^2 / 2! = e^(-4) * 16/2 = 8 * e^(-4)",
    "       = 8 * 0.01832 = 0.1465"):
    story.append(l)
story.append(result("P(X = 2) = 0.1465"))
story.append(step("(ii) P(at least 1 case) = 1 - P(X=0):"))
for l in calc(
    "P(X=0) = e^(-4) = 0.01832",
    "P(X>=1) = 1 - 0.01832 = 0.9817"):
    story.append(l)
story.append(result("P(X >= 1) = 0.9817"))
story.append(step("(iii) P(at most 3 cases):"))
for l in calc(
    "P(X=0) = e^(-4) = 0.01832",
    "P(X=1) = 4*e^(-4) = 0.07326",
    "P(X=2) = 0.1465",
    "P(X=3) = e^(-4)*64/6 = 0.1954",
    "P(X<=3) = 0.01832+0.07326+0.1465+0.1954 = 0.4335"):
    story.append(l)
story.append(result("P(X <= 3) = 0.4335"))
story.append(step("(iv) P(exactly 6 in 2 hours): lambda*t = 4*2 = 8"))
for l in calc(
    "P(N(2)=6) = e^(-8)*8^6/6! = e^(-8)*262144/720",
    "          = 0.000335*364.1 = 0.1221"):
    story.append(l)
story.append(result("P(N(2) = 6) = 0.1221"))
story.append(step("(v) Poisson approx: n=500, p=0.006, lambda=np=3"))
for l in calc(
    "P(X=3) = e^(-3)*3^3/3! = e^(-3)*27/6 = 4.5*e^(-3)",
    "       = 4.5 * 0.04979 = 0.2240"):
    story.append(l)
story.append(result("P(exactly 3 breakdowns) = 0.2240"))
story.append(SP(8))

story.append(ans_header("MODULE 1  —  ANSWER 7(b): PMF Table Analysis", DBLUE))
story.append(SP(4))
story.append(step("(i) Verify valid PMF:"))
for l in calc("0.05+0.20+0.35+0.25+0.15 = 1.00   AND   all p(x) >= 0"):
    story.append(l)
story.append(result("Valid PMF confirmed."))
story.append(step("(ii) E[X] and E[X^2]:"))
for l in calc(
    "E[X] = 0(0.05)+1(0.20)+2(0.35)+3(0.25)+4(0.15)",
    "     = 0 + 0.20 + 0.70 + 0.75 + 0.60 = 2.25",
    "E[X^2] = 0(0.05)+1(0.20)+4(0.35)+9(0.25)+16(0.15)",
    "       = 0 + 0.20 + 1.40 + 2.25 + 2.40 = 6.25"):
    story.append(l)
story.append(result("E[X] = 2.25,   E[X^2] = 6.25"))
story.append(step("(iii) Var(X) and SD(X):"))
for l in calc(
    "Var(X) = E[X^2] - (E[X])^2 = 6.25 - (2.25)^2 = 6.25 - 5.0625 = 1.1875",
    "SD(X) = sqrt(1.1875) = 1.0898"):
    story.append(l)
story.append(result("Var(X) = 1.1875,   SD(X) = 1.0898"))
story.append(step("(iv) E[2X^2 - 3X + 1]:"))
for l in calc(
    "E[2X^2-3X+1] = 2*E[X^2] - 3*E[X] + 1",
    "             = 2(6.25) - 3(2.25) + 1",
    "             = 12.50 - 6.75 + 1 = 6.75"):
    story.append(l)
story.append(result("E[2X^2 - 3X + 1] = 6.75"))
story.append(step("(v) CDF F(x):"))
for l in calc(
    "F(x) = 0          for x < 0",
    "F(x) = 0.05       for 0 <= x < 1",
    "F(x) = 0.25       for 1 <= x < 2",
    "F(x) = 0.60       for 2 <= x < 3",
    "F(x) = 0.85       for 3 <= x < 4",
    "F(x) = 1.00       for x >= 4"):
    story.append(l)
story.append(SP(8))

# MODULE 2 ANSWERS
story.append(PageBreak())
story.append(ans_header("MODULE 2  —  ANSWER 8(a): Normal Distribution [Exam Marks]", DGRN))
story.append(SP(4))
story.append(note("X ~ N(65, 144), mu=65, sigma=12. Standardize: Z = (X-65)/12"))
story.append(SP(3))
story.append(step("(i) P(marks < 77):"))
for l in calc("Z = (77-65)/12 = 1.0", "P(X<77) = Phi(1.0) = 0.8413"):
    story.append(l)
story.append(result("P(marks < 77) = 0.8413"))
story.append(step("(ii) P(53 < marks < 89):"))
for l in calc(
    "z1 = (53-65)/12 = -1.0    z2 = (89-65)/12 = 2.0",
    "P(53<X<89) = Phi(2.0) - Phi(-1.0) = 0.9772 - 0.1587 = 0.8185"):
    story.append(l)
story.append(result("P(53 < marks < 89) = 0.8185"))
story.append(step("(iii) P(marks > 59):"))
for l in calc(
    "Z = (59-65)/12 = -0.5",
    "P(X>59) = P(Z>-0.5) = Phi(0.5) = 0.6915"):
    story.append(l)
story.append(result("P(marks > 59) = 0.6915"))
story.append(step("(iv) Top 10% minimum marks (P(X > c) = 0.10):"))
for l in calc(
    "P(X < c) = 0.90  =>  Phi(z) = 0.90  =>  z = 1.28",
    "c = 65 + 1.28*12 = 65 + 15.36 = 80.36"):
    story.append(l)
story.append(result("Minimum marks for top 10% = 80.36 = approx 81"))
story.append(step("(v) 68-95-99.7 Rule:  P(41 < X < 89)"))
for l in calc(
    "41 = 65 - 2*12 = mu - 2*sigma",
    "89 = 65 + 2*12 = mu + 2*sigma",
    "By 68-95-99.7 rule: P(mu - 2*sigma < X < mu + 2*sigma) = 0.9545"):
    story.append(l)
story.append(result("Approximately 95.45% of students score between 41 and 89."))
story.append(SP(8))

story.append(ans_header("MODULE 2  —  ANSWER 8(b): Joint PDF  f(x,y) = k*x^2*y", DGRN))
story.append(SP(4))
story.append(step("(i) Find k:"))
for l in calc(
    "Integral[0 to 1] Integral[0 to 2] k*x^2*y dy dx = 1",
    "k * [x^3/3 from 0 to 1] * [y^2/2 from 0 to 2]",
    "k * (1/3) * (2) = 1  =>  2k/3 = 1"):
    story.append(l)
story.append(result("k = 3/2"))
story.append(step("(ii) Marginal PDFs:"))
for l in calc(
    "f_X(x) = Integral[0 to 2] (3/2)*x^2*y dy",
    "       = (3/2)*x^2 * [y^2/2] from 0 to 2 = (3/2)*x^2*2 = 3*x^2    for 0<x<1",
    "",
    "f_Y(y) = Integral[0 to 1] (3/2)*x^2*y dx",
    "       = (3/2)*y * [x^3/3] from 0 to 1 = (3/2)*y*(1/3) = y/2       for 0<y<2"):
    story.append(l)
story.append(result("f_X(x) = 3x^2  (0<x<1)     f_Y(y) = y/2  (0<y<2)"))
story.append(step("(iii) Independence check:"))
for l in calc(
    "f_X(x)*f_Y(y) = 3x^2 * y/2 = (3/2)*x^2*y = f(x,y)"):
    story.append(l)
story.append(result("X and Y are INDEPENDENT"))
story.append(step("(iv) E[X] and E[Y]:"))
for l in calc(
    "E[X] = Integral[0 to 1] x * 3x^2 dx = 3 * [x^4/4] from 0 to 1 = 3/4",
    "E[Y] = Integral[0 to 2] y * (y/2) dy = (1/2)*[y^3/3] from 0 to 2 = (1/2)*(8/3) = 4/3"):
    story.append(l)
story.append(result("E[X] = 3/4 = 0.75,   E[Y] = 4/3 = 1.333"))
story.append(step("(v) P(X < 0.5, Y < 1):"))
for l in calc(
    "= Integral[0 to 0.5] Integral[0 to 1] (3/2)x^2*y dy dx",
    "= (3/2) * [x^3/3 from 0 to 0.5] * [y^2/2 from 0 to 1]",
    "= (3/2) * (1/24) * (1/2) = 3/96 = 1/32"):
    story.append(l)
story.append(result("P(X < 0.5, Y < 1) = 1/32 = 0.03125"))
story.append(SP(8))

story.append(ans_header("MODULE 2  —  ANSWER 9(a): Exponential Distribution [Component Lifetime]", DGRN))
story.append(SP(4))
story.append(note("E[X] = 4 years  =>  lambda = 1/4 = 0.25 per year"))
story.append(SP(3))
story.append(step("(i) Rate, f(x), F(x):"))
for l in calc(
    "lambda = 1/4 = 0.25",
    "f(x)  = 0.25 * e^(-0.25x)    for x >= 0",
    "F(x)  = 1 - e^(-0.25x)       for x >= 0"):
    story.append(l)
story.append(step("(ii) P(X > 5):"))
for l in calc("P(X>5) = e^(-0.25*5) = e^(-1.25) = 0.2865"):
    story.append(l)
story.append(result("P(X > 5) = 0.2865"))
story.append(step("(iii) P(X < 2):"))
for l in calc("P(X<2) = 1 - e^(-0.25*2) = 1 - e^(-0.5) = 1 - 0.6065 = 0.3935"):
    story.append(l)
story.append(result("P(X < 2) = 0.3935"))
story.append(step("(iv) Memoryless property: P(X > 3+4 | X > 3) = P(X > 4):"))
for l in calc(
    "By Memoryless Property: P(X>s+t|X>s) = P(X>t)",
    "P(X > 7 | X > 3) = P(X > 4) = e^(-0.25*4) = e^(-1) = 0.3679"):
    story.append(l)
story.append(result("P(lasts another 4 years | already 3 years) = e^(-1) = 0.3679"))
story.append(step("(v) Median and Variance:"))
for l in calc(
    "Median m: e^(-m/4) = 0.5  =>  m = 4*ln(2) = 4*0.6931 = 2.7726 years",
    "Var(X) = 1/lambda^2 = 1/(0.25)^2 = 16 years^2"):
    story.append(l)
story.append(result("Median = 2.77 years,   Var(X) = 16 years^2"))
story.append(SP(8))

story.append(ans_header("MODULE 2  —  ANSWER 9(b): PDF  f(y) = c*(1-y)  on (0,1)", DGRN))
story.append(SP(4))
story.append(step("(i) Find c:"))
for l in calc(
    "Integral[0 to 1] c*(1-y) dy = 1",
    "c * [y - y^2/2] from 0 to 1 = c * (1 - 1/2) = c/2 = 1",
    "c = 2"):
    story.append(l)
story.append(result("c = 2,   f(y) = 2(1-y) for 0 < y < 1"))
story.append(step("(ii) CDF F(y):"))
for l in calc(
    "F(y) = Integral[0 to y] 2(1-t) dt = 2[t - t^2/2] from 0 to y",
    "     = 2y - y^2    for 0 <= y <= 1"):
    story.append(l)
story.append(result("F(y) = 2y - y^2"))
story.append(step("(iii) E[Y] and E[Y^2]:"))
for l in calc(
    "E[Y] = Integral[0 to 1] y*2(1-y) dy = 2*Integral[0 to 1] (y - y^2) dy",
    "     = 2*[y^2/2 - y^3/3] from 0 to 1 = 2*(1/2 - 1/3) = 2*(1/6) = 1/3",
    "",
    "E[Y^2] = Integral[0 to 1] y^2*2(1-y) dy = 2*[y^3/3 - y^4/4] from 0 to 1",
    "       = 2*(1/3 - 1/4) = 2*(1/12) = 1/6"):
    story.append(l)
story.append(result("E[Y] = 1/3,   E[Y^2] = 1/6"))
story.append(step("(iv) Var(Y) and SD(Y):"))
for l in calc(
    "Var(Y) = E[Y^2] - (E[Y])^2 = 1/6 - (1/3)^2 = 1/6 - 1/9 = 3/18 - 2/18 = 1/18",
    "SD(Y) = sqrt(1/18) = 1/(3*sqrt(2)) = 0.2357"):
    story.append(l)
story.append(result("Var(Y) = 1/18 = 0.0556,   SD(Y) = 0.2357"))
story.append(step("(v) P(0.25 < Y < 0.75):"))
for l in calc(
    "P(0.25<Y<0.75) = F(0.75) - F(0.25)",
    "F(0.75) = 2(0.75) - (0.75)^2 = 1.5 - 0.5625 = 0.9375",
    "F(0.25) = 2(0.25) - (0.25)^2 = 0.5 - 0.0625 = 0.4375",
    "P = 0.9375 - 0.4375 = 0.5000"):
    story.append(l)
story.append(result("P(0.25 < Y < 0.75) = 0.50"))
story.append(SP(8))

# MODULE 3 ANSWERS
story.append(PageBreak())
story.append(ans_header("MODULE 3  —  ANSWER 10(a): Inequalities and CLT [Factory Packages]", DORG))
story.append(SP(4))
story.append(note("mu=10, sigma=0.5, sigma^2=0.25"))
story.append(SP(3))
story.append(step("(i) Markov's Inequality: P(X >= 30)"))
for l in calc("P(X>=30) <= E[X]/30 = 10/30 = 1/3"):
    story.append(l)
story.append(result("P(X >= 30) <= 1/3 = 0.3333"))
story.append(step("(ii) Chebyshev: P(|X-10| >= 2)"))
for l in calc("P(|X-10|>=2) <= sigma^2/eps^2 = 0.25/4 = 0.0625"):
    story.append(l)
story.append(result("P(|X - 10| >= 2) <= 0.0625"))
story.append(step("(iii) Lower bound for P(9 < X < 11):"))
for l in calc(
    "P(9<X<11) = P(|X-10|<1) >= 1 - sigma^2/1^2 = 1 - 0.25 = 0.75"):
    story.append(l)
story.append(result("P(9 < X < 11) >= 0.75"))
story.append(step("(iv) CLT: P(9.8 < X-bar < 10.2) with n=64:"))
for l in calc(
    "SD of X-bar = sigma/sqrt(n) = 0.5/sqrt(64) = 0.5/8 = 0.0625",
    "z1 = (9.8-10)/0.0625 = -0.2/0.0625 = -3.2",
    "z2 = (10.2-10)/0.0625 = 0.2/0.0625 = 3.2",
    "P(-3.2 < Z < 3.2) = 2*Phi(3.2)-1 = 2*0.9993-1 = 0.9986"):
    story.append(l)
story.append(result("P(9.8 < X-bar < 10.2) = 0.9986"))
story.append(step("(v) Minimum sample size for P(|X-bar-10|<0.1)>=0.95:"))
for l in calc(
    "Need: (0.1*sqrt(n))/0.5 >= 1.96",
    "sqrt(n) >= 1.96*0.5/0.1 = 9.8",
    "n >= 9.8^2 = 96.04  =>  n >= 97"):
    story.append(l)
story.append(result("Minimum sample size n = 97"))
story.append(SP(8))

story.append(ans_header("MODULE 3  —  ANSWER 10(b): Poisson Process [Network Router]", DORG))
story.append(SP(4))
story.append(note("lambda = 8/min = 8/60 per second = 2/15 per second"))
story.append(SP(3))
story.append(step("(i) P(exactly 10 packets in 1 minute): lambda*t = 8*1 = 8"))
for l in calc(
    "P(N=10) = e^(-8)*8^10/10!",
    "        = e^(-8)*1073741824/3628800 = 0.000335*295.8 = 0.0993"):
    story.append(l)
story.append(result("P(N(1 min) = 10) = 0.0993"))
story.append(step("(ii) P(exactly 5 in 30 sec): t=0.5 min, lambda*t = 4"))
for l in calc(
    "P(N=5) = e^(-4)*4^5/5! = e^(-4)*1024/120 = 0.01832*8.533 = 0.1563"):
    story.append(l)
story.append(result("P(N(30 sec) = 5) = 0.1563"))
story.append(step("(iii) P(no packets in 15 sec): t=0.25 min, lambda*t = 2"))
for l in calc("P(N=0) = e^(-2) = 0.1353"):
    story.append(l)
story.append(result("P(N(15 sec) = 0) = 0.1353"))
story.append(step("(iv) P(interarrival T > 15 sec): T ~ Exp(2/15 per sec), t=15 sec"))
for l in calc(
    "lambda in per-second = 8/60 = 2/15",
    "P(T>15) = e^(-lambda*15) = e^(-(2/15)*15) = e^(-2) = 0.1353"):
    story.append(l)
story.append(result("P(T > 15 seconds) = e^(-2) = 0.1353"))
story.append(step("(v) Expected waiting time for 6th packet:"))
for l in calc(
    "E[S_6] = 6/lambda = 6/8 minutes = 0.75 min = 45 seconds"):
    story.append(l)
story.append(result("E[S_6] = 45 seconds"))
story.append(SP(8))

story.append(ans_header("MODULE 3  —  ANSWER 11(a): CLT [Worker Salaries]", DORG))
story.append(SP(4))
story.append(note("mu=25000, sigma=5000, sigma^2=25000000"))
story.append(SP(3))
story.append(step("(i) n=100, P(24500 < X-bar < 25500):"))
for l in calc(
    "SD of X-bar = 5000/sqrt(100) = 500",
    "z1 = (24500-25000)/500 = -1.0    z2 = (25500-25000)/500 = 1.0",
    "P(-1<Z<1) = 2*Phi(1)-1 = 2*0.8413-1 = 0.6826"):
    story.append(l)
story.append(result("P(24500 < X-bar < 25500) = 0.6826"))
story.append(step("(ii) P(total income of 100 workers > 25,60,000):"))
for l in calc(
    "S_100 = total. E[S_100]=100*25000=2500000, SD=5000*sqrt(100)=50000",
    "Z = (2560000-2500000)/50000 = 60000/50000 = 1.2",
    "P(S>2560000) = P(Z>1.2) = 1-Phi(1.2) = 1-0.8849 = 0.1151"):
    story.append(l)
story.append(result("P(total > 25,60,000) = 0.1151"))
story.append(step("(iii) Minimum n so P(|X-bar-25000|<500)>=0.99:"))
for l in calc(
    "Need: z = 2.576 for 99% confidence",
    "n >= (2.576*5000/500)^2 = (25.76)^2 = 663.6",
    "n >= 664"):
    story.append(l)
story.append(result("Minimum sample size n = 664"))
story.append(step("(iv) Chebyshev for X-bar with n=25:"))
for l in calc(
    "Var of X-bar = sigma^2/n = 25000000/25 = 1000000  =>  SD=1000",
    "P(|X-bar-25000|<1000) >= 1 - Var(X-bar)/eps^2 = 1 - 1000000/1000000 = 0",
    "Chebyshev gives 0 as lower bound (not useful here)."):
    story.append(l)
story.append(result("Chebyshev lower bound = 0 (insufficient info for useful bound with n=25)"))
story.append(step("(v) Central Limit Theorem Statement:"))
for l in calc(
    "If X1, X2, ..., Xn are i.i.d. with mean mu and variance sigma^2,",
    "then as n->inf:  Z = (X-bar - mu)/(sigma/sqrt(n))  converges to N(0,1).",
    "Significance: Works for ANY distribution. Justifies using Normal",
    "approximation for sums/averages of large samples."):
    story.append(l)
story.append(SP(8))

story.append(ans_header("MODULE 3  —  ANSWER 11(b): Poisson Process [Bank Customers]", DORG))
story.append(SP(4))
story.append(note("lambda = 3/hr. Interarrival T ~ Exp(3/hr)"))
story.append(SP(3))
story.append(step("(i) P(exactly 4 customers in 2 hours): lambda*t = 6"))
for l in calc(
    "P(N(2)=4) = e^(-6)*6^4/4! = e^(-6)*1296/24 = 54*e^(-6)",
    "          = 54*0.002479 = 0.1339"):
    story.append(l)
story.append(result("P(N(2 hr) = 4) = 0.1339"))
story.append(step("(ii) P(at least 1 in 30 min): lambda*t = 1.5"))
for l in calc(
    "P(N>=1) = 1 - P(N=0) = 1 - e^(-1.5) = 1 - 0.2231 = 0.7769"):
    story.append(l)
story.append(result("P(at least 1 in 30 min) = 0.7769"))
story.append(step("(iii) P(first customer arrives after 30 min):"))
for l in calc(
    "T_1 ~ Exp(3/hr).  30 min = 0.5 hr",
    "P(T_1 > 0.5) = e^(-3*0.5) = e^(-1.5) = 0.2231"):
    story.append(l)
story.append(result("P(first customer after 30 min) = 0.2231"))
story.append(step("(iv) P(interarrival between 2nd and 3rd customer < 15 min):"))
for l in calc(
    "T_3 ~ Exp(3/hr), and T_3 is independent of all others.",
    "15 min = 0.25 hr",
    "P(T < 0.25) = 1 - e^(-3*0.25) = 1 - e^(-0.75) = 1 - 0.4724 = 0.5276"):
    story.append(l)
story.append(result("P(interarrival < 15 min) = 0.5276"))
story.append(step("(v) Expected waiting time for 5th customer:"))
for l in calc("E[S_5] = 5/lambda = 5/3 hours = 1.667 hours = 100 minutes"):
    story.append(l)
story.append(result("E[S_5] = 5/3 hours = 100 minutes"))
story.append(SP(8))

# MODULE 4 ANSWERS
story.append(PageBreak())
story.append(ans_header("MODULE 4  —  ANSWER 12(a): Markov Chain {0,1,2}", DPUR))
story.append(SP(4))
story.append(note("P = [[0.5,0.4,0.1],[0.2,0.5,0.3],[0.1,0.3,0.6]]"))
story.append(SP(3))
story.append(step("(i) Irreducibility:"))
for l in calc(
    "All entries of P are strictly positive (p_ij > 0 for all i,j)",
    "So every state can reach every other state in ONE step",
    "All states communicate: 0<->1<->2"):
    story.append(l)
story.append(result("Chain IS IRREDUCIBLE (single communicating class {0,1,2})"))
story.append(step("(ii) P(X_2=2 | X_0=0) via C-K:"))
for l in calc(
    "p_02^(2) = SUM_k  p_0k * p_k2",
    "         = p_00*p_02 + p_01*p_12 + p_02*p_22",
    "         = (0.5)(0.1) + (0.4)(0.3) + (0.1)(0.6)",
    "         = 0.05 + 0.12 + 0.06 = 0.23"):
    story.append(l)
story.append(result("P(X_2 = 2 | X_0 = 0) = 0.23"))
story.append(step("(iii) Stationary Distribution — solve pi*P = pi, SUM=1:"))
for l in calc(
    "Eq1: pi_0 = 0.5*pi_0 + 0.2*pi_1 + 0.1*pi_2  =>  0.5*pi_0 = 0.2*pi_1 + 0.1*pi_2",
    "Eq2: pi_1 = 0.4*pi_0 + 0.5*pi_1 + 0.3*pi_2  =>  0.5*pi_1 = 0.4*pi_0 + 0.3*pi_2",
    "Normalization: pi_0 + pi_1 + pi_2 = 1",
    "",
    "From Eq1: 5*pi_0 = 2*pi_1 + pi_2          ... (A)",
    "From Eq2: 5*pi_1 = 4*pi_0 + 3*pi_2        ... (B)",
    "",
    "From (A): pi_2 = 5*pi_0 - 2*pi_1",
    "Substitute into (B):  5*pi_1 = 4*pi_0 + 3*(5*pi_0-2*pi_1)",
    "                      5*pi_1 = 4*pi_0 + 15*pi_0 - 6*pi_1",
    "                      11*pi_1 = 19*pi_0  =>  pi_1 = 19*pi_0/11",
    "Then: pi_2 = 5*pi_0 - 2*(19*pi_0/11) = (55-38)*pi_0/11 = 17*pi_0/11",
    "",
    "Normalization: pi_0 + 19*pi_0/11 + 17*pi_0/11 = pi_0*(11+19+17)/11 = 47*pi_0/11 = 1",
    "pi_0 = 11/47,   pi_1 = 19/47,   pi_2 = 17/47"):
    story.append(l)
story.append(result("pi_0 = 11/47 = 0.234,   pi_1 = 19/47 = 0.404,   pi_2 = 17/47 = 0.362"))
story.append(step("(iv) Long-run fraction in state 1:"))
story.append(result("pi_1 = 19/47 = 0.4043  =>  40.43% of time in state 1"))
story.append(step("(v) Mean return time to state 0:"))
for l in calc("m_0 = 1/pi_0 = 1/(11/47) = 47/11 = 4.27 steps"):
    story.append(l)
story.append(result("Mean return time to state 0 = 47/11 = 4.27 steps"))
story.append(SP(8))

story.append(ans_header("MODULE 4  —  ANSWER 12(b): Classification of States {1..5}", DPUR))
story.append(SP(4))
story.append(note("P rows = current state, cols = next state. States {1,2,3,4,5}"))
story.append(SP(3))
story.append(step("(i) Communicating Classes:"))
for l in calc(
    "From states 1 and 2: rows show p_13=p_14=p_15=p_23=p_24=p_25=0",
    "So {1,2} CANNOT reach {3,4,5}.  But 1->2 and 2->1, so {1,2} communicate.",
    "",
    "From state 3: can reach 1,2,3,4,5 (all nonzero in row 3)",
    "From states 4,5: p_41=p_42=p_51=p_52=0, so {4,5} cannot reach {1,2,3}",
    "4->5 and 5->4, so {4,5} communicate.",
    "",
    "Communicating Classes: {1,2},  {3},  {4,5}"):
    story.append(l)
story.append(result("Classes: {1,2}  |  {3}  |  {4,5}"))
story.append(step("(ii) Recurrent and Transient:"))
for l in calc(
    "{1,2}: CLOSED class (rows 1,2 have 0 outside {1,2}) => RECURRENT",
    "{4,5}: CLOSED class (rows 4,5 have 0 outside {4,5}) => RECURRENT",
    "{3}:   NOT closed (row 3 has nonzero entries to 1,2,4,5) => TRANSIENT"):
    story.append(l)
story.append(result("States 1,2: RECURRENT  |  State 3: TRANSIENT  |  States 4,5: RECURRENT"))
story.append(step("(iii) Irreducibility:"))
story.append(result("NOT IRREDUCIBLE — three communicating classes exist."))
story.append(step("(iv) Stationary distribution for each recurrent class:"))
for l in calc(
    "Class {1,2}: pi_1*0.5 + pi_2*0.3 = pi_1  =>  0.5*pi_1 = 0.3*pi_2  =>  pi_2=(5/3)*pi_1",
    "pi_1 + pi_2 = 1:  pi_1(1+5/3)=1  =>  (8/3)*pi_1=1  =>  pi_1=3/8, pi_2=5/8",
    "",
    "Class {4,5}: pi_4*0.6 + pi_5*0.5 = pi_4  =>  0.4*pi_4 = 0.5*pi_5",
    "pi_4 = (5/4)*pi_5.  pi_4+pi_5=1:  (9/4)*pi_5=1  =>  pi_5=4/9, pi_4=5/9"):
    story.append(l)
story.append(result("Class {1,2}: pi_1=3/8, pi_2=5/8   |   Class {4,5}: pi_4=5/9, pi_5=4/9"))
story.append(step("(v) P(X_2 = 2 | X_0 = 1):"))
for l in calc(
    "p_12^(2) = SUM_k p_1k * p_k2",
    "         = p_11*p_12 + p_12*p_22 + p_13*p_32 + p_14*p_42 + p_15*p_52",
    "         = (0.5)(0.5) + (0.5)(0.7) + (0)(0.1) + (0)(0) + (0)(0)",
    "         = 0.25 + 0.35 = 0.60"):
    story.append(l)
story.append(result("P(X_2 = 2 | X_0 = 1) = 0.60"))
story.append(SP(8))

story.append(ans_header("MODULE 4  —  ANSWER 13(a): Stock Market Markov Chain", DPUR))
story.append(SP(4))
story.append(note("P = [[0.7,0.2,0.1],[0.3,0.5,0.2],[0.2,0.3,0.5]]  Rows/Cols: B,R,F"))
story.append(SP(3))
story.append(step("(i) P(Bull after 2 days | Bull today) = p_BB^(2):"))
for l in calc(
    "p_BB^(2) = p_BB*p_BB + p_BR*p_RB + p_BF*p_FB",
    "         = (0.7)(0.7) + (0.2)(0.3) + (0.1)(0.2)",
    "         = 0.49 + 0.06 + 0.02 = 0.57"):
    story.append(l)
story.append(result("P(Bull after 2 days | Bull today) = 0.57"))
story.append(step("(ii) P(Bull after 2 days | Flat today) = p_FB^(2):"))
for l in calc(
    "p_FB^(2) = p_FB*p_BB + p_FR*p_RB + p_FF*p_FB",
    "         = (0.2)(0.7) + (0.3)(0.3) + (0.5)(0.2)",
    "         = 0.14 + 0.09 + 0.10 = 0.33"):
    story.append(l)
story.append(result("P(Bull after 2 days | Flat today) = 0.33"))
story.append(step("(iii) Stationary distribution — solve pi*P = pi, SUM=1:"))
for l in calc(
    "From pi_B row: 0.3*pi_B = 0.3*pi_R + 0.2*pi_F  =>  3*pi_B = 3*pi_R + 2*pi_F  ...(A)",
    "From pi_F row: 0.5*pi_F = 0.1*pi_B + 0.2*pi_R                               ...(B)",
    "",
    "From (A): pi_F = (3*pi_B - 3*pi_R)/2",
    "Sub into (B): 0.5*(3*pi_B-3*pi_R)/2 = 0.1*pi_B + 0.2*pi_R",
    "              (15*pi_B-15*pi_R)/4 = pi_B + 2*pi_R  (multiply both by 10)",
    "              15*pi_B - 15*pi_R = 4*pi_B + 8*pi_R",
    "              11*pi_B = 23*pi_R  =>  pi_R = 11*pi_B/23... ",
    "",
    "Recompute carefully from (A) and (B):",
    "  From (A): pi_F = (3*pi_B-3*pi_R)/2",
    "  From (B): 5*pi_F = pi_B + 2*pi_R",
    "  5*(3*pi_B-3*pi_R)/2 = pi_B+2*pi_R => 15*pi_B-15*pi_R = 2*pi_B+4*pi_R",
    "  13*pi_B = 19*pi_R => pi_R = 13*pi_B/19",
    "  pi_F = (3*pi_B-3*(13/19)*pi_B)/2 = pi_B*(3-39/19)/2 = pi_B*(18/19)/2 = 9*pi_B/19",
    "",
    "Normalization: pi_B + 13*pi_B/19 + 9*pi_B/19 = pi_B*(19+13+9)/19 = 41*pi_B/19 = 1",
    "pi_B = 19/41,   pi_R = 13/41,   pi_F = 9/41"):
    story.append(l)
story.append(result("pi_B = 19/41 = 0.4634,   pi_R = 13/41 = 0.3171,   pi_F = 9/41 = 0.2195"))
story.append(step("(iv) Long-run fraction in Bull:"))
story.append(result("pi_B = 19/41 = 46.34% of days in Bull market"))
story.append(step("(v) Mean return time to Bull:"))
for l in calc("m_B = 1/pi_B = 41/19 = 2.16 days"):
    story.append(l)
story.append(result("Mean return time to Bull state = 41/19 = 2.16 days"))
story.append(SP(8))

story.append(ans_header("MODULE 4  —  ANSWER 13(b): Random Walk {0,1,2,3,4}", DPUR))
story.append(SP(4))
story.append(note("State 0: absorbing. State 4: absorbing. States 1,2,3: p=0.6 right, q=0.4 left"))
story.append(SP(3))
story.append(step("(i) Complete 5x5 TPM:"))
story.append(SP(2))
story.append(sub_table(
    ["State", "To 0", "To 1", "To 2", "To 3", "To 4"],
    [["0 (absorb)", "1.0", "0", "0", "0", "0"],
     ["1", "0.4", "0", "0.6", "0", "0"],
     ["2", "0", "0.4", "0", "0.6", "0"],
     ["3", "0", "0", "0.4", "0", "0.6"],
     ["4 (absorb)", "0", "0", "0", "0", "1.0"]],
    [2.5*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm], DPUR))
story.append(SP(4))
story.append(step("(ii) Communicating Classes:"))
for l in calc(
    "State 0: stays at 0 (absorbing)  => Class {0}",
    "State 4: stays at 4 (absorbing)  => Class {4}",
    "States 1,2,3: 1->2->3 possible, 3->2->1 possible, so {1,2,3} communicate => Class {1,2,3}"):
    story.append(l)
story.append(result("Classes: {0}  |  {1, 2, 3}  |  {4}"))
story.append(step("(iii) Classify all states:"))
for l in calc(
    "State 0: RECURRENT (absorbing, f_00=1)",
    "State 4: RECURRENT (absorbing, f_44=1)",
    "States 1,2,3: Can escape to 0 or 4 and never return => TRANSIENT"):
    story.append(l)
story.append(result("States 0,4: RECURRENT  |  States 1,2,3: TRANSIENT"))
story.append(step("(iv) P(X_2 = 3 | X_0 = 2) using C-K:"))
for l in calc(
    "p_23^(2) = SUM_k p_2k * p_k3",
    "         = p_20*p_03 + p_21*p_13 + p_22*p_23 + p_23*p_33 + p_24*p_43",
    "         = (0)(0)+(0.4)(0)+(0)(0)+(0.6)(0)+(0)(0)    [checking all terms]",
    "Wait: from state 2, go to 1 with 0.4 or 3 with 0.6",
    "From state 1, go to 0 (0.4) or 2 (0.6) — cannot reach 3",
    "From state 3, go to 2 (0.4) or 4 (0.6) — can reach neither back to 3 in 0 steps",
    "p_23^(2) = p_21*p_13 + p_23*p_33",
    "         = (0.4)(0) + (0.6)(0) = 0  [state 3 has no p_33]",
    "Actually: p_23^(2) = p_21*p_13 + p_23*p_33 = 0.4*0 + 0.6*0 = 0",
    "Correct path: 2->3->? In step 2 from 3: p_34=0.6, p_32=0.4 (not to 3 again)",
    "So 2->3 in 1 step (prob=0.6), then from 3 in second step to 3 impossible (p_33=0)",
    "Therefore p_23^(2) = 0. Try 2->1->?(p=0.4): from 1 cannot reach 3 in 1 step either.",
    "FINAL: P(X_2=3 | X_0=2) = 0"):
    story.append(l)
story.append(result("P(X_2 = 3 | X_0 = 2) = 0  [cannot reach 3 in exactly 2 steps from 2]"))
story.append(step("(v) Irreducibility:"))
for l in calc(
    "State 0 cannot reach states 1,2,3,4 (absorbing)",
    "States 1,2,3 cannot reach state 0 directly (only transition out of 1 to 0 exists)",
    "Actually 1->0 is possible, but 0 cannot go back to 1",
    "So 0 and 1 do NOT communicate => chain is NOT irreducible"):
    story.append(l)
story.append(result("NOT IRREDUCIBLE — multiple communicating classes exist ({0}, {1,2,3}, {4})"))
story.append(SP(10))
story.append(HR(GOLD, 2))
story.append(SP(4))
story.append(Paragraph("*** END OF ANSWER KEY ***", sFooter))
story.append(Paragraph(
    "GAMAT301  |  KTU 2024 Scheme  |  Question Paper 1 — Full Answer Key  |  All Modules Covered",
    sFooter))

# ─── BUILD ────────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    "K:\PROJECTS\Phone agent\GAMAT301_Question_Paper_1_with_Answers.pdf",
    pagesize=A4,
    rightMargin=1.5*cm, leftMargin=1.5*cm,
    topMargin=1.8*cm,   bottomMargin=1.8*cm,
    title="GAMAT301 KTU Question Paper 1 with Full Answer Key",
    author="KTU Academic Coach",
)
doc.build(story)
print("PDF generated successfully!")