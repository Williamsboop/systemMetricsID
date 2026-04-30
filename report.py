from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Flowable

# ── Colour palette ──────────────────────────────────────────────────────────
BG_DARK      = colors.HexColor("#0F1117")
BG_CARD      = colors.HexColor("#1A1D27")
BG_CODE      = colors.HexColor("#12151E")
ACCENT_BLUE  = colors.HexColor("#4F8EF7")
ACCENT_CYAN  = colors.HexColor("#00D4FF")
ACCENT_GREEN = colors.HexColor("#39D98A")
ACCENT_PURP  = colors.HexColor("#A78BFA")
ACCENT_ORG   = colors.HexColor("#FB923C")
TEXT_WHITE   = colors.HexColor("#F1F5F9")
TEXT_MUTED   = colors.HexColor("#94A3B8")
TEXT_DIM     = colors.HexColor("#64748B")
BORDER       = colors.HexColor("#2D3348")

def split_code_block(lines, max_lines=40):
    """Split a large code block into multiple smaller CodeBlocks."""
    chunks = []
    for i in range(0, len(lines), max_lines):
        chunk = lines[i:i + max_lines]
        chunks.append(CodeBlock(chunk))
    return chunks

class CalloutBox(Flowable):
    def __init__(self, text, bar_color=ACCENT_BLUE, width=None):
        super().__init__()
        self.text = text
        self.bar_color = bar_color
        self.box_width = width or (letter[0] - 1.4*inch)
        self.style = ParagraphStyle("callout", fontName="Helvetica", fontSize=10, textColor=TEXT_WHITE, leading=14)
        self._para = Paragraph(text, self.style)

    def wrap(self, aW, aH):
        # We tell the paragraph it has slightly less width to account for our padding/bar
        # The 28 represents: 4 (bar) + 12 (left gap) + 12 (right gap)
        w, h = self._para.wrap(self.box_width - 28, aH)
        self.height = h + 16  # Add 8pt padding to top and bottom
        return self.box_width, self.height

    def draw(self):
        c = self.canv
        # Background
        c.setFillColor(BG_CARD)
        c.roundRect(0, 0, self.box_width, self.height, 6, stroke=0, fill=1)
        # Left Bar
        c.setFillColor(self.bar_color)
        c.roundRect(0, 0, 4, self.height, 2, stroke=0, fill=1)
        # Border
        c.setStrokeColor(BORDER)
        c.roundRect(0, 0, self.box_width, self.height, 6, stroke=1, fill=0)
        # Text (y-offset is half of our padding)
        self._para.drawOn(c, 16, 8) 

class CodeBlock(Flowable):
    def __init__(self, lines, width=None):
        super().__init__()
        self.lines = lines
        self.box_width = width or (letter[0] - 1.4*inch)
        self.line_h = 13  # The "leading" (space between lines)
        self.v_pad = 10   # Padding top and bottom

    def wrap(self, aW, aH):
        """
        REPORTLAB ENGINE: 'How much space do you need?'
        THIS METHOD: 'Exactly this much.'
        """
        # Height is (number of lines * line height) + (padding * 2)
        self.height = (len(self.lines) * self.line_h) + (self.v_pad * 2)
        return self.box_width, self.height

    # --- Syntax Highlighter Logic (Must be inside the class) ---
    _KW = {"import","from","def","class","if","else","elif","while","for",
           "in","return","not","and","or","True","False","None","break",
           "continue","pass","with","as","try","except","raise","lambda",
           "yield","global","nonlocal"}

    def _tokenize(self, line):
        """Return list of (text, color) for one line."""
        stripped = line.lstrip()
        if stripped.startswith("#"):
            return [(line, TEXT_DIM)]

        tokens = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "#":
                tokens.append((line[i:], TEXT_DIM))
                break
            if ch in ('"', "'"):
                q = ch
                j = i + 1
                if line[i:i+3] in ('"""', "'''"):
                    q = line[i:i+3]; j = i + 3
                end = line.find(q, j)
                end = end + len(q) if end != -1 else len(line)
                tokens.append((line[i:end], ACCENT_GREEN))
                i = end
                continue
            if ch.isalpha() or ch == "_":
                j = i
                while j < len(line) and (line[j].isalnum() or line[j] == "_"):
                    j += 1
                word = line[i:j]
                col = ACCENT_PURP if word in self._KW else TEXT_WHITE
                tokens.append((word, col))
                i = j
                continue
            if ch.isdigit() or (ch == "0" and i+1 < len(line) and line[i+1] in "xXbBoO"):
                j = i
                while j < len(line) and (line[j].isalnum() or line[j] in "._"):
                    j += 1
                tokens.append((line[i:j], ACCENT_ORG))
                i = j
                continue
            if ch in "()[]{}=<>!+-*/%&|^~,.;:":
                tokens.append((ch, ACCENT_CYAN))
                i += 1
                continue
            tokens.append((ch, TEXT_WHITE))
            i += 1
        return tokens

    def draw(self):
        """Draw the box based on the height determined in wrap()."""
        c = self.canv
        w, h = self.box_width, self.height

        # Background + Border
        c.setFillColor(BG_CODE)
        c.roundRect(0, 0, w, h, 6, stroke=0, fill=1)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 6, stroke=1, fill=0)

        c.setFont("Courier", 8.5)
        # Vertical cursor starts at the top, minus padding and a small font offset
        y_cursor = h - self.v_pad - 9 

        for line in self.lines:
            tokens = self._tokenize(line)
            x_cursor = self.v_pad # horizontal padding
            for txt, col in tokens:
                c.setFillColor(col)
                c.drawString(x_cursor, y_cursor, txt)
                x_cursor += c.stringWidth(txt, "Courier", 8.5)
            y_cursor -= self.line_h

class SectionBanner(Flowable):
    def __init__(self, number, title, width=None):
        super().__init__()
        self.number = number
        self.title = title
        self.box_width = width or (letter[0] - 1.4*inch)
        self.height = 30 # Reduced from 36 to be more compact

    def wrap(self, aW, aH):
        return self.box_width, self.height

    def draw(self):
        c, w, h = self.canv, self.box_width, self.height
        c.setFillColor(BG_CARD)
        c.roundRect(0, 0, w, h, 4, stroke=0, fill=1)
        c.setFillColor(ACCENT_BLUE)
        c.rect(0, h-2, w, 2, stroke=0, fill=1) # Top accent bar
        c.setStrokeColor(BORDER)
        c.roundRect(0, 0, w, h, 4, stroke=1, fill=0)
        # Badge
        c.setFillColor(ACCENT_BLUE)
        c.circle(20, h/2, 9, stroke=0, fill=1)
        c.setFillColor(TEXT_WHITE)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(20, h/2 - 3.5, str(self.number))
        # Title
        c.setFont("Helvetica-Bold", 12)
        c.drawString(38, h/2 - 4, self.title)

# ── Page canvas callbacks ────────────────────────────────────────────────────
def _bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG_DARK)
    canvas.rect(0, 0, letter[0], letter[1], stroke=0, fill=1)
    canvas.restoreState()

def _header_footer(canvas, doc):
    _bg(canvas, doc)
    if doc.page == 1:
        return
    W, H = letter
    canvas.saveState()
    # header line
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(0.7*inch, H - 0.55*inch, W - 0.7*inch, H - 0.55*inch)
    canvas.setFillColor(TEXT_DIM)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.7*inch, H - 0.45*inch, "DXGI GPU Info — Python ctypes Guide")
    canvas.drawRightString(W - 0.7*inch, H - 0.45*inch, f"Page {doc.page}")
    # footer line
    canvas.line(0.7*inch, 0.55*inch, W - 0.7*inch, 0.55*inch)
    canvas.setFillColor(TEXT_DIM)
    canvas.drawCentredString(W/2, 0.35*inch, "For personal/educational use")
    canvas.restoreState()


# ── Style helpers ────────────────────────────────────────────────────────────
def _s(name, **kw):
    base = getSampleStyleSheet()["Normal"]
    return ParagraphStyle(name, parent=base, **kw)

H1   = _s("h1", fontName="Helvetica-Bold",  fontSize=26, textColor=TEXT_WHITE,  leading=32, spaceAfter=6)
H2   = _s("h2", fontName="Helvetica-Bold",  fontSize=14, textColor=ACCENT_CYAN, leading=18, spaceAfter=4, spaceBefore=10)
BODY = _s("body", fontName="Helvetica",     fontSize=10, textColor=TEXT_WHITE,  leading=16, spaceAfter=4, alignment=TA_JUSTIFY)
MUTED= _s("muted",fontName="Helvetica",     fontSize=9,  textColor=TEXT_MUTED,  leading=14, spaceAfter=2)
MONO = _s("mono", fontName="Courier",       fontSize=9,  textColor=ACCENT_CYAN, leading=13)
LABEL= _s("label",fontName="Helvetica-Bold",fontSize=10, textColor=ACCENT_PURP, leading=14, spaceAfter=2)
SUB  = _s("sub",  fontName="Helvetica-Bold",fontSize=11, textColor=ACCENT_GREEN,leading=16, spaceAfter=3, spaceBefore=8)

def sp(n=8): return Spacer(1, n)
def hr():    return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=8, spaceBefore=8)

def body(txt):  return Paragraph(txt, BODY)
def muted(txt): return Paragraph(txt, MUTED)
def label(txt): return Paragraph(txt, LABEL)
def sub(txt):   return Paragraph(txt, SUB)
def mono(txt):  return Paragraph(f'<font name="Courier" color="#00D4FF">{txt}</font>', MUTED)

def inline_code(txt):
    return f'<font name="Courier" color="#00D4FF" size="9">{txt}</font>'


# ── Concept table ────────────────────────────────────────────────────────────
from typing import List, Any # Add this import at the top

def concept_table(rows):
    cell_style = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=9,
        textColor=TEXT_WHITE,
        leading=12,
        alignment=TA_LEFT
    )

    # FIX: Explicitly tell the type checker this is a list of lists 
    # that can contain Any type (Strings OR Paragraphs)
    data: List[List[Any]] = [["Term", "Plain English"]]
    
    for row in rows:
        term = row[0]
        explanation = Paragraph(row[1], cell_style)
        data.append([term, explanation])

    usable_width = letter[0] - 1.4*inch
    col_w = [usable_width * 0.28, usable_width * 0.72]
    
    t = Table(data, colWidths=col_w)
    
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  ACCENT_BLUE),
        ("TEXTCOLOR",     (0,0), (-1,0),  TEXT_WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0),  9),
        ("BACKGROUND",    (0,1), (-1,-1), BG_CARD),
        ("TEXTCOLOR",     (0,1), (0,-1),  ACCENT_CYAN),
        ("FONTNAME",      (0,1), (0,-1),  "Courier"),
        ("FONTSIZE",      (0,1), (0,-1),  8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [BG_CARD, colors.HexColor("#1E2235")]),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("GRID",          (0,0), (-1,-1), 0.4, BORDER),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    
    return t


# ── BUILD ────────────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        "dxgi_gpu_guide.pdf",
        pagesize=letter,
        leftMargin=0.7*inch, rightMargin=0.7*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch,
    )

    story = []

    # ── COVER PAGE ────────────────────────────────────────────────────────────
    story += [Spacer(1, 1.1*inch)]

    # 1. Create a specific style for the Cover Title to force alignment
    title_style = ParagraphStyle(
        "TitleStyle",
        fontName="Helvetica-Bold",
        fontSize=32,
        textColor=TEXT_WHITE,
        alignment=TA_CENTER,  # Crucial for centering the text
        leftIndent=0,
        rightIndent=0,
        leading=38,
    )

    # 2. Use a Paragraph instead of raw text
    title_p = Paragraph("DXGI GPU INFO", title_style)

    # 3. Define the Table to span the full usable width
    usable_width = letter[0] - 1.4*inch
    tt = Table([[title_p]], colWidths=[usable_width])

    tt.setStyle(TableStyle([
        ("BACKGROUND",      (0, 0), (-1, -1), ACCENT_BLUE),
        ("ROUNDEDCORNERS",  (0, 0), (-1, -1), 8),
        ("ALIGN",           (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",          (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",     (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",    (0, 0), (-1, -1), 0),
        ("TOPPADDING",      (0, 0), (-1, -1), 20),
        ("BOTTOMPADDING",   (0, 0), (-1, -1), 20),
    ]))

    # Force the Table object itself to align center on the page
    tt.hAlign = 'CENTER'

    story.append(tt)
    story.append(sp(12))

    story.append(Paragraph("A Plain-English Guide to Querying GPU Memory<br/>on Windows Using Python <font name='Courier' color='#00D4FF'>ctypes</font>", _s("cov_sub", fontName="Helvetica", fontSize=14, textColor=TEXT_MUTED, leading=20, alignment=TA_CENTER)))
    story.append(sp(40))

    # quick-stats row
    stats = [["No extra libraries", "Windows only", "AMD · NVIDIA · Intel", "Pure Python"]]
    st = Table(stats, colWidths=[(letter[0]-1.4*inch)/4]*4)
    st.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), BG_CARD),
        ("TEXTCOLOR",    (0,0),(-1,-1), ACCENT_GREEN),
        ("FONTNAME",     (0,0),(-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0),(-1,-1), 9),
        ("ALIGN",        (0,0),(-1,-1), "CENTER"),
        ("TOPPADDING",   (0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("GRID",         (0,0),(-1,-1), 0.4, BORDER),
    ]))
    story.append(st)
    story.append(sp(50))

    story.append(Paragraph("What you will learn", _s("wyl", fontName="Helvetica-Bold", fontSize=12, textColor=ACCENT_CYAN, alignment=TA_CENTER)))
    story.append(sp(8))
    learns = [
        "What COM and DXGI are and why we need them",
        "How vtables let Python call Windows C++ interfaces",
        "Every line of the final script, explained simply",
        "How to reuse this pattern for your own projects",
    ]
    for l in learns:
        story.append(Paragraph(f"<font color='#39D98A'>✓</font>  {l}", _s("lrn", fontName="Helvetica", fontSize=10, textColor=TEXT_WHITE, leading=16, leftIndent=20)))
    story.append(PageBreak())

    # ── SECTION 1 – Background ────────────────────────────────────────────────
    story += [SectionBanner(1, "Background — What Are We Even Doing?"), sp(10)]

    story.append(body(
        "Windows keeps track of every graphics card in your PC. To ask Windows "
        '"how much VRAM does my GPU have?", we have to speak its language — a system '
        "called <b>COM</b> (Component Object Model) exposed through an API called "
        "<b>DXGI</b> (DirectX Graphics Infrastructure). Python's built-in "
        f"{inline_code('ctypes')} library lets us call these Windows interfaces "
        "directly, with zero extra installs."
    ))
    story.append(sp(8))

    story.append(concept_table([
        ["COM",   "A Windows system that lets programs talk to each other using agreed-upon rules (interfaces). Think of it like a universal plug socket."],
        ["DXGI",  "Microsoft's graphics layer. It knows about all your GPUs and can report their memory, names, and capabilities."],
        ["ctypes","A Python module that lets you call raw C/C++ Windows functions as if they were normal Python functions."],
        ["HRESULT","A number Windows returns from every COM call. 0x0 means success. Anything else is an error code."],
        ["vtable", "A lookup table of function pointers inside a COM object. We find the right slot number to call the right method."],
        ["IID",   "A unique ID (GUID) that identifies a specific COM interface, like IDXGIFactory1 or IDXGIAdapter3."],
    ]))
    story.append(sp(10))

    story.append(CalloutBox(
        "<b>Analogy:</b> Imagine DXGI is a hotel front desk. COM is the intercom "
        "system you use to call them. The vtable is the hotel's internal phone "
        "directory — each room (method) has a slot number. We dial the right slot "
        "to get the information we want.",
        bar_color=ACCENT_PURP
    ))
    story.append(PageBreak())

    # ── SECTION 2 – The Full Script ───────────────────────────────────────────
    story += [SectionBanner(2, "The Complete Script"), sp(10)]
    story.append(body("Here is the entire working script. The sections that follow break down every piece."))
    story.append(sp(8))

    full_code = [
        "import ctypes",
        "",
        "DXGI_MEMORY_SEGMENT_GROUP_LOCAL = 0",
        "VENDOR_AMD    = 0x1002",
        "VENDOR_NVIDIA = 0x10DE",
        "VENDOR_INTEL  = 0x8086",
        "",
        "class DXGI_QUERY_VIDEO_MEMORY_INFO(ctypes.Structure):",
        '    _fields_ = [',
        '        ("Budget",                  ctypes.c_uint64),',
        '        ("CurrentUsage",            ctypes.c_uint64),',
        '        ("AvailableForReservation", ctypes.c_uint64),',
        '        ("CurrentReservation",      ctypes.c_uint64),',
        "    ]",
        "",
        "class DXGI_ADAPTER_DESC(ctypes.Structure):",
        '    _fields_ = [',
        '        ("Description",           ctypes.c_wchar * 128),',
        '        ("VendorId",              ctypes.c_uint),',
        '        ("DedicatedVideoMemory",  ctypes.c_size_t),',
        '        # ... (other fields omitted for brevity)',
        "    ]",
        "",
        "IID_IDXGIFactory1 = (ctypes.c_byte * 16)(",
        "    0x78, 0xae, 0x0a, 0x77, 0x6f, 0xf2, 0xba, 0x4d,",
        "    0xa8, 0x29, 0x25, 0x3c, 0x83, 0xd1, 0xb3, 0x87",
        ")",
        "IID_IDXGIAdapter3 = (ctypes.c_byte * 16)(",
        "    0xA4, 0x67, 0x59, 0x64, 0x92, 0x13, 0x10, 0x43,",
        "    0xA7, 0x98, 0x80, 0x53, 0xCE, 0x3E, 0x93, 0xFD",
        ")",
        "",
        "def _vtable_fn(obj, slot, restype, *argtypes):",
        "    vtable = ctypes.cast(obj, ctypes.POINTER(ctypes.c_void_p))",
        "    fn_ptr = ctypes.cast(vtable[0], ctypes.POINTER(ctypes.c_void_p))[slot]",
        "    return ctypes.cast(fn_ptr, ctypes.CFUNCTYPE(restype, ctypes.c_void_p, *argtypes))",
        "",
        "def _release(obj):",
        "    _vtable_fn(obj, 2, ctypes.c_ulong)(obj)",
        "",
        "def _query_interface(obj, iid, out):",
        "    fn = _vtable_fn(obj, 0, ctypes.c_long,",
        "                    ctypes.POINTER(ctypes.c_byte * 16),",
        "                    ctypes.POINTER(ctypes.c_void_p))",
        "    return fn(obj, iid, out)",
        "",
        "def get_dxgi_gpu_info() -> dict:",
        "    ctypes.windll.ole32.CoInitialize(None)   # start COM",
        "    factory = ctypes.c_void_p()",
        "    if ctypes.windll.dxgi.CreateDXGIFactory1(",
        "            ctypes.byref(IID_IDXGIFactory1), ctypes.byref(factory)) != 0:",
        "        ctypes.windll.ole32.CoUninitialize()",
        "        return {}",
        "    enum_adapters = _vtable_fn(factory, 12, ctypes.c_long,",
        "                               ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p))",
        "    gpus = {}",
        "    index = 0",
        "    while True:",
        "        adapter1 = ctypes.c_void_p()",
        "        if ctypes.c_uint32(enum_adapters(factory, index,",
        "                ctypes.byref(adapter1))).value != 0: break",
        "        adapter3 = ctypes.c_void_p()",
        "        qi_hr = _query_interface(adapter1,",
        "                    ctypes.byref(IID_IDXGIAdapter3), ctypes.byref(adapter3))",
        "        _release(adapter1)",
        "        if ctypes.c_uint32(qi_hr).value != 0:",
        "            index += 1; continue",
        "        desc     = DXGI_ADAPTER_DESC()",
        "        mem_info = DXGI_QUERY_VIDEO_MEMORY_INFO()",
        "        _vtable_fn(adapter3, 8,  ctypes.c_long,",
        "                   ctypes.POINTER(DXGI_ADAPTER_DESC))(adapter3, ctypes.byref(desc))",
        "        _vtable_fn(adapter3, 14, ctypes.c_long,",
        "                   ctypes.c_uint, ctypes.c_uint,",
        "                   ctypes.POINTER(DXGI_QUERY_VIDEO_MEMORY_INFO))(",
        "                       adapter3, 0, 0, ctypes.byref(mem_info))",
        "        total = desc.DedicatedVideoMemory // (1024 ** 3)",
        "        free  = (mem_info.Budget - mem_info.CurrentUsage) // (1024 ** 3)",
        "        if total > 0 and desc.VendorId in (0x1002, 0x10DE, 0x8086)",
        "                     and free <= total:",
        "            gpus[index] = {'name': desc.Description,",
        "                           'totalMem': total, 'freeMem': free}",
        "        _release(adapter3)",
        "        index += 1",
        "    _release(factory)",
        "    ctypes.windll.ole32.CoUninitialize()",
        "    return gpus",
    ]
    story.extend(split_code_block(full_code, max_lines=38))
    story.append(PageBreak())

    # ── SECTION 3 – Structures ────────────────────────────────────────────────
    story += [SectionBanner(3, "Step 1 — Defining C Structures"), sp(10)]

    story.append(body(
        "Windows functions pass data around using <b>C structs</b> — fixed memory layouts "
        "where each field lives at a known byte offset. We mirror those layouts in Python "
        f"using {inline_code('ctypes.Structure')} so Python and Windows agree on exactly "
        "where each piece of data lives in memory."
    ))
    story.append(sp(8))

    story.append(sub("DXGI_QUERY_VIDEO_MEMORY_INFO"))
    story.append(CodeBlock([
        "class DXGI_QUERY_VIDEO_MEMORY_INFO(ctypes.Structure):",
        '    _fields_ = [',
        '        ("Budget",                  ctypes.c_uint64),  # total VRAM OS allows us',
        '        ("CurrentUsage",            ctypes.c_uint64),  # VRAM in use right now',
        '        ("AvailableForReservation", ctypes.c_uint64),  # we can reserve this much',
        '        ("CurrentReservation",      ctypes.c_uint64),  # we have reserved this much',
        "    ]",
    ]))
    story.append(sp(6))
    story.append(CalloutBox(
        f"<b>Budget</b> is the key field. Think of it as your weekly allowance — "
        "the OS decides how much VRAM your process is allowed to use. "
        f"<b>CurrentUsage</b> is how much you've already spent. "
        f"Free memory = Budget − CurrentUsage.",
        bar_color=ACCENT_GREEN
    ))
    story.append(sp(10))

    story.append(sub("DXGI_ADAPTER_DESC"))
    story.append(CodeBlock([
        "class DXGI_ADAPTER_DESC(ctypes.Structure):",
        '    _fields_ = [',
        '        ("Description",           ctypes.c_wchar * 128), # GPU name string',
        '        ("VendorId",              ctypes.c_uint),        # maker: AMD/NVIDIA/Intel',
        '        ("DeviceId",              ctypes.c_uint),        # specific model number',
        '        ("SubSysId",              ctypes.c_uint),        # sub-system ID',
        '        ("Revision",              ctypes.c_uint),        # hardware revision',
        '        ("DedicatedVideoMemory",  ctypes.c_size_t),      # total VRAM in bytes',
        '        ("DedicatedSystemMemory", ctypes.c_size_t),      # system RAM used as VRAM',
        '        ("SharedSystemMemory",    ctypes.c_size_t),      # shared RAM available',
        '        ("AdapterLuid",           ctypes.c_byte * 8),    # unique adapter ID',
        "    ]",
    ]))
    story.append(sp(6))
    story.append(CalloutBox(
        f"<b>DedicatedVideoMemory</b> is the physical VRAM soldered onto your GPU. "
        "This is the 'true' total — not shared or borrowed system memory. "
        f"<b>VendorId</b> lets us filter out iGPUs and software renderers.",
        bar_color=ACCENT_BLUE
    ))
    story.append(PageBreak())

    # ── SECTION 4 – IIDs ─────────────────────────────────────────────────────
    story += [SectionBanner(4, "Step 2 — Interface IDs (GUIDs)"), sp(10)]

    story.append(body(
        "Every COM interface has a globally unique 16-byte ID called a <b>GUID</b> "
        "(or <b>IID</b> when identifying an interface). We use these to ask Windows "
        '"give me THIS specific interface". The bytes look cryptic but they are just '
        "fixed constants from Microsoft's documentation — you never have to calculate them."
    ))
    story.append(sp(8))

    story.append(CodeBlock([
        "# IDXGIFactory1  {770AAE78-F26F-4DBA-A829-253C83D1B387}",
        "IID_IDXGIFactory1 = (ctypes.c_byte * 16)(",
        "    0x78, 0xae, 0x0a, 0x77,   # first chunk,  little-endian",
        "    0x6f, 0xf2,               # second chunk, little-endian",
        "    0xba, 0x4d,               # third chunk,  little-endian",
        "    0xa8, 0x29,               # remaining bytes, big-endian",
        "    0x25, 0x3c, 0x83, 0xd1, 0xb3, 0x87",
        ")",
        "",
        "# IDXGIAdapter3  {645967A4-1392-4310-A798-8053CE3E93FD}",
        "IID_IDXGIAdapter3 = (ctypes.c_byte * 16)(",
        "    0xA4, 0x67, 0x59, 0x64,",
        "    0x92, 0x13,",
        "    0x10, 0x43,",
        "    0xA7, 0x98,",
        "    0x80, 0x53, 0xCE, 0x3E, 0x93, 0xFD",
        ")",
    ]))
    story.append(sp(8))

    story.append(CalloutBox(
        "<b>Endianness gotcha:</b> GUIDs are written as "
        "{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}. The first three groups are "
        "stored in little-endian order (bytes reversed). The last two groups are "
        "big-endian (bytes as-is). This is a well-known COM convention and the "
        "source of many subtle bugs.",
        bar_color=ACCENT_ORG
    ))
    story.append(sp(10))

    story.append(concept_table([
        ["IDXGIFactory1", "The 'factory' interface — creates and enumerates adapters"],
        ["IDXGIAdapter1", "A basic adapter handle returned by EnumAdapters1"],
        ["IDXGIAdapter3", "An upgraded adapter handle that adds QueryVideoMemoryInfo"],
    ]))
    story.append(PageBreak())

    # ── SECTION 5 – vtable helper ─────────────────────────────────────────────
    story += [SectionBanner(5, "Step 3 — The vtable Helper Function"), sp(10)]

    story.append(body(
        "COM interfaces are C++ objects. In C++, every object has a hidden pointer "
        "called a <b>vtable</b> (virtual function table) — it's a list of function "
        "pointers, one for each method. To call a method, we look up its slot number "
        "in that table and call the function at that address."
    ))
    story.append(sp(8))

    story.append(CodeBlock([
        "def _vtable_fn(obj, slot, restype, *argtypes):",
        "    # Step 1: treat the COM object pointer as a pointer-to-pointer.",
        "    #   The first pointer points to the vtable.",
        "    vtable = ctypes.cast(obj, ctypes.POINTER(ctypes.c_void_p))",
        "",
        "    # Step 2: dereference vtable[0] to get the vtable address,",
        "    #   then index into it at [slot] to get the function pointer.",
        "    fn_ptr = ctypes.cast(vtable[0], ctypes.POINTER(ctypes.c_void_p))[slot]",
        "",
        "    # Step 3: cast that raw address into a typed callable so ctypes",
        "    #   knows how to marshal arguments and the return value.",
        "    return ctypes.cast(fn_ptr,",
        "        ctypes.CFUNCTYPE(restype, ctypes.c_void_p, *argtypes))",
    ]))
    story.append(sp(8))

    story.append(CalloutBox(
        "<b>Memory diagram:</b>\n"
        "COM object → [vtable ptr] → [fn0, fn1, fn2, fn3, ...]\n"
        "                                 ↑              ↑\n"
        "                           slot 0 (QueryInterface)   slot 2 (Release)\n\n"
        "We read vtable[0] to get the address of the vtable, then index into "
        "that array to get the specific function we want to call.",
        bar_color=ACCENT_PURP
    ))
    story.append(sp(10))

    story.append(sub("Slot numbers used in this script"))
    story.append(concept_table([
        ["slot 0",  "QueryInterface — ask the object to give us a different interface version"],
        ["slot 2",  "Release — tell COM we're done with this object (memory management)"],
        ["slot 8",  "GetDesc — get the adapter description (name, VRAM total, vendor ID)"],
        ["slot 12", "EnumAdapters1 — list all GPUs (called on the factory object)"],
        ["slot 14", "QueryVideoMemoryInfo — get budget and current usage (IDXGIAdapter3 only)"],
    ]))
    story.append(PageBreak())

    # ── SECTION 6 – helper functions ─────────────────────────────────────────
    story += [SectionBanner(6, "Step 4 — Small Helper Functions"), sp(10)]

    story.append(sub("_release(obj)"))
    story.append(CodeBlock([
        "def _release(obj):",
        "    _vtable_fn(obj, 2, ctypes.c_ulong)(obj)",
    ]))
    story.append(sp(4))
    story.append(body(
        f"COM objects must be manually released when you're done with them. "
        f"Slot 2 is always {inline_code('Release')} on every COM interface "
        "(inherited from IUnknown). Forgetting to call this leaks memory."
    ))
    story.append(sp(10))

    story.append(sub("_query_interface(obj, iid, out)"))
    story.append(CodeBlock([
        "def _query_interface(obj, iid, out):",
        "    fn = _vtable_fn(obj, 0, ctypes.c_long,",
        "                    ctypes.POINTER(ctypes.c_byte * 16),",
        "                    ctypes.POINTER(ctypes.c_void_p))",
        "    return fn(obj, iid, out)",
    ]))
    story.append(sp(4))
    story.append(body(
        f"Slot 0 is always {inline_code('QueryInterface')}. It lets you ask a COM "
        "object: <i>\"Can you also act as this other interface?\"</i> We use this to "
        f"upgrade an {inline_code('IDXGIAdapter1')} (basic) into an "
        f"{inline_code('IDXGIAdapter3')} (has QueryVideoMemoryInfo). "
        "The IID tells it which interface we want. The result comes back via the "
        f"{inline_code('out')} pointer."
    ))
    story.append(sp(8))
    story.append(CalloutBox(
        f"<b>Why upgrade from Adapter1 to Adapter3?</b>  "
        f"{inline_code('EnumAdapters1')} returns {inline_code('IDXGIAdapter1')} objects. "
        f"But {inline_code('QueryVideoMemoryInfo')} only exists on "
        f"{inline_code('IDXGIAdapter3')} (added in DXGI 1.4). "
        "QueryInterface is the COM way to ask for the upgraded version of the same object.",
        bar_color=ACCENT_CYAN
    ))
    story.append(PageBreak())

    # ── SECTION 7 – main function ─────────────────────────────────────────────
    story += [SectionBanner(7, "Step 5 — The Main Function, Line by Line"), sp(10)]

    chunks = [
        (
            "Initialize COM",
            ["ctypes.windll.ole32.CoInitialize(None)"],
            "COM must be initialized before any COM calls are made. Without this, "
            "methods like QueryVideoMemoryInfo silently return zeros. "
            f"{inline_code('CoUninitialize()')} is called at the end to clean up."
        ),
        (
            "Create the DXGI Factory",
            [
                "factory = ctypes.c_void_p()",
                "hr = ctypes.windll.dxgi.CreateDXGIFactory1(",
                "    ctypes.byref(IID_IDXGIFactory1), ctypes.byref(factory))",
                "if hr != 0:",
                "    ctypes.windll.ole32.CoUninitialize()",
                "    return {}",
            ],
            f"We call {inline_code('CreateDXGIFactory1')} from dxgi.dll. It gives us a "
            f"factory object — think of it as the directory of all GPUs. "
            f"We pass the {inline_code('IID_IDXGIFactory1')} so Windows knows what kind "
            "of factory interface to give back. If it fails (hr != 0) we bail out early."
        ),
        (
            "Get the EnumAdapters1 function",
            [
                "enum_adapters = _vtable_fn(factory, 12, ctypes.c_long,",
                "                           ctypes.c_uint,",
                "                           ctypes.POINTER(ctypes.c_void_p))",
            ],
            f"We look up slot 12 on the factory — that's {inline_code('EnumAdapters1')}. "
            "We describe its signature: returns a c_long (HRESULT), "
            "takes a c_uint (index) and a pointer for the output adapter."
        ),
        (
            "Loop through all adapters",
            [
                "index = 0",
                "while True:",
                "    adapter1 = ctypes.c_void_p()",
                "    hr = enum_adapters(factory, index, ctypes.byref(adapter1))",
                "    if ctypes.c_uint32(hr).value != 0:",
                "        break   # no more adapters",
            ],
            "We keep asking for adapter 0, 1, 2... until Windows returns a non-zero "
            "HRESULT meaning 'no more adapters'. We cast hr to uint32 first because "
            "Python can interpret the same bit pattern as a negative signed integer — "
            "uint32 gives us the true Windows error code."
        ),
        (
            "Upgrade to IDXGIAdapter3",
            [
                "    adapter3 = ctypes.c_void_p()",
                "    qi_hr = _query_interface(adapter1,",
                "                ctypes.byref(IID_IDXGIAdapter3),",
                "                ctypes.byref(adapter3))",
                "    _release(adapter1)   # always release what we no longer need",
                "    if ctypes.c_uint32(qi_hr).value != 0:",
                "        index += 1; continue",
            ],
            f"We try to upgrade {inline_code('adapter1')} to {inline_code('adapter3')} "
            "via QueryInterface. We immediately release adapter1 — we only needed it "
            "to get adapter3. If the upgrade fails (e.g. very old driver), we skip "
            "this adapter and move on."
        ),
        (
            "Read GPU description and memory info",
            [
                "    desc     = DXGI_ADAPTER_DESC()",
                "    mem_info = DXGI_QUERY_VIDEO_MEMORY_INFO()",
                "    # slot 8 = GetDesc",
                "    _vtable_fn(adapter3, 8, ctypes.c_long,",
                "               ctypes.POINTER(DXGI_ADAPTER_DESC))",
                "              (adapter3, ctypes.byref(desc))",
                "    # slot 14 = QueryVideoMemoryInfo",
                "    _vtable_fn(adapter3, 14, ctypes.c_long,",
                "               ctypes.c_uint, ctypes.c_uint,",
                "               ctypes.POINTER(DXGI_QUERY_VIDEO_MEMORY_INFO))",
                "              (adapter3, 0, 0, ctypes.byref(mem_info))",
            ],
            "We allocate empty C structs, then pass them by reference (byref) to the "
            "Windows functions, which fill them in. Slot 8 fills in the name and total "
            "VRAM. Slot 14 fills in the budget and current usage. The two zeros are "
            "NodeIndex (0 = first GPU node) and MemorySegmentGroup (0 = local/dedicated VRAM)."
        ),
        (
            "Filter and store results",
            [
                "    total = desc.DedicatedVideoMemory // (1024 ** 3)",
                "    free  = (mem_info.Budget - mem_info.CurrentUsage) // (1024 ** 3)",
                "    if total > 0",
                "       and desc.VendorId in (0x1002, 0x10DE, 0x8086)",
                "       and free <= total:",
                "        gpus[index] = {",
                "            'name':     desc.Description,",
                "            'totalMem': total,",
                "            'freeMem':  free,",
                "        }",
                "    _release(adapter3)",
                "    index += 1",
            ],
            "We convert bytes to GB (divide by 1024 three times). The three filter "
            "conditions drop: software renderers with no real VRAM (total == 0), "
            "unknown vendors, and iGPUs whose 'budget' is inflated shared system RAM "
            "(free > total is a dead giveaway). Always release adapter3 at the end of "
            "each loop iteration."
        ),
    ]

    for title, code, explanation in chunks:
        story.append(KeepTogether([
            label(f"▸  {title}"),
            CodeBlock(code),
            sp(4),
            body(explanation),
            sp(10),
        ]))

    story.append(PageBreak())

    # ── SECTION 8 – Reuse guide ───────────────────────────────────────────────
    story += [SectionBanner(8, "How to Reuse This Pattern"), sp(10)]

    story.append(body(
        "The vtable pattern here works for <i>any</i> COM interface on Windows. "
        "Here is the recipe to follow for your own project:"
    ))
    story.append(sp(8))

    steps = [
        ("1", ACCENT_BLUE,  "Find the interface in Microsoft Docs",
         "Search 'IDXGIWhatever site:learn.microsoft.com'. The docs list every method in order — that order is your vtable slot index (starting from 0, including inherited methods)."),
        ("2", ACCENT_CYAN,  "Count inherited slots",
         "COM interfaces inherit from each other. Count all methods from IUnknown (3) + IDXGIObject (4) + IDXGIAdapter (3) + ... then add the new methods. The first new method starts at the sum."),
        ("3", ACCENT_GREEN, "Mirror the C structs",
         "Any struct passed to/from the function needs a matching ctypes.Structure subclass with _fields_ in the exact same order and types as the C definition."),
        ("4", ACCENT_PURP,  "Get the IID bytes right",
         "Copy the GUID from docs. The first 3 groups are little-endian (reverse each group's bytes). The last 2 groups are big-endian (copy as-is)."),
        ("5", ACCENT_ORG,   "Always call CoInitialize first",
         "Without CoInitialize, many COM methods silently fail or return zeroed structs. Always uninitialize at the end too."),
        ("6", ACCENT_BLUE,  "Always Release what you're done with",
         "Every COM object is reference-counted. Call Release (slot 2) when you're finished with each object or you will leak memory."),
    ]

    for num, col, title, desc_text in steps:
        row_data = [[
            Paragraph(f'<font color="{col.hexval()}" name="Helvetica-Bold" size="14"><b>{num}</b></font>', _s("sn", fontName="Helvetica-Bold", fontSize=16, textColor=col, alignment=TA_CENTER, leading=20)),
            [Paragraph(title, _s("st", fontName="Helvetica-Bold", fontSize=10, textColor=col, leading=14)),
             Paragraph(desc_text, _s("sd", fontName="Helvetica", fontSize=9, textColor=TEXT_WHITE, leading=14))]
        ]]
        t = Table(row_data, colWidths=[0.45*inch, letter[0]-1.4*inch-0.45*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(-1,-1), BG_CARD),
            ("VALIGN",       (0,0),(-1,-1), "TOP"),
            ("TOPPADDING",   (0,0),(-1,-1), 10),
            ("BOTTOMPADDING",(0,0),(-1,-1), 10),
            ("LEFTPADDING",  (0,0),(-1,-1), 10),
            ("RIGHTPADDING", (0,0),(-1,-1), 10),
            ("GRID",         (0,0),(-1,-1), 0.4, BORDER),
        ]))
        story.append(t)
        story.append(sp(4))

    story.append(sp(10))
    story.append(CalloutBox(
        "<b>Finding slot numbers reliably:</b>  The safest way is to look at the "
        "C++ header file directly. Search GitHub for the interface name in "
        "<font name='Courier'>dxgi.h</font>, <font name='Courier'>dxgi1_2.h</font>, "
        "<font name='Courier'>dxgi1_4.h</font> etc. Count the virtual methods in "
        "order — each one is a slot.",
        bar_color=ACCENT_GREEN
    ))
    story.append(PageBreak())

    # ── SECTION 9 – Quick reference ───────────────────────────────────────────
    story += [SectionBanner(9, "Quick Reference"), sp(10)]

    story.append(sub("Vendor IDs"))
    story.append(concept_table([
        ["0x1002", "AMD  — includes all Radeon discrete and integrated GPUs"],
        ["0x10DE", "NVIDIA — all GeForce and Quadro GPUs"],
        ["0x8086", "Intel — integrated graphics (UHD, Iris, Arc)"],
    ]))
    story.append(sp(10))

    story.append(sub("Common HRESULT codes"))
    story.append(concept_table([
        ["0x00000000", "S_OK — success"],
        ["0x80004002", "E_NOINTERFACE — wrong IID, interface not supported"],
        ["0x80004001", "E_NOTIMPL — wrong vtable slot, method not implemented"],
        ["0x887A0002", "DXGI_ERROR_NOT_FOUND — no more adapters to enumerate"],
    ]))
    story.append(sp(10))

    story.append(sub("ctypes type cheat-sheet"))
    story.append(concept_table([
        ["c_uint32",   "Unsigned 32-bit integer — use for HRESULT comparisons"],
        ["c_uint64",   "Unsigned 64-bit integer — VRAM sizes in bytes"],
        ["c_size_t",   "Pointer-sized integer — correct for DedicatedVideoMemory"],
        ["c_void_p",   "Generic pointer — used for COM object handles"],
        ["c_wchar*128","Fixed-length wide string — GPU name from DXGI_ADAPTER_DESC"],
        ["byref(x)",   "Pass x by pointer — lets C code write back into x"],
        ["CFUNCTYPE",  "Declares a C function signature Python can call safely"],
    ]))
    story.append(sp(10))

    story.append(CalloutBox(
        "<b>Tip — refreshing free memory:</b>  To get a live freeMem reading, just "
        "call get_dxgi_gpu_info() again. The Budget and CurrentUsage values are "
        "always current as of the moment the call is made. For real-time monitoring, "
        "call it on a timer in a background thread.",
        bar_color=ACCENT_BLUE
    ))

    doc.build(story, onFirstPage=_bg, onLaterPages=_header_footer)
    print("Done.")

build()