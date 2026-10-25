import os
import re
import io
import json
import time
import base64
import pickle
import socket
import html as H
import cv2
import numpy as np
import torch
from PIL import Image
import gradio as gr
from ultralytics import YOLO
from rembg import remove, new_session

from ocean_bg import HEAD, BG_HTML, EXTRA_CSS

MODEL_PATH = "cls_best.pt"
DATASET_DIR = "new_shell_images_2nd"
PRICES_FILE = "prices.json"
INDEX_CACHE = ".ref_index.pkl"
EMB_CACHE = ".dino_emb.npy"
EMB_PATHS_CACHE = ".dino_paths.pkl"
PART_EMB = ".dino_partial.npy"
PART_PATHS = ".dino_partial_paths.pkl"
SAVE_EVERY = 50
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

USE_KNN = True
EMB_MODEL = "./dinov2-small"
REMBG_MODEL = "isnet-general-use"
SHELL_FRAC = 0.80
W_YOLO = 0.5
LOW_CONF = 0.30

PORT = 7860
SHARE = os.environ.get("SHARE", "0") == "1"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
torch.set_num_threads(os.cpu_count() or 4)
print(f" Device: {DEVICE}")

model = YOLO(MODEL_PATH)
CLASS_NAMES = model.names
print(f" Model ready - classes: {len(CLASS_NAMES)}")
model.predict(np.zeros((224, 224, 3), np.uint8), verbose=False)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


DIR = {"ar": "rtl", "en": "ltr"}

TX = {
    "ar": dict(
        tag="قم بتصوير الصدفة لمعرفة نوعها وسعرها التقديري",
        btn="تحليل الصدفة",
        seg="الصدفة بعد العزل",
        gal="أقرب عيّنات مرجعية",
        empty_t="التقرير",
        empty_p="ارفع صورة صدفة أو قم بتصويرها، وخلال لحظات سيظهر تقرير تعريف كامل",
        rep_title="تقرير تعريف عيّنة",
        brand="ShellVis · مختبر الصدفات",
        sci="الاسم العلمي",
        genus="الجنس",
        conf="الثقة",
        price="السعر التقديري",
        p_manual="مُدخَل يدوياً",
        p_genus="تقدير حسب الجنس",
        p_general="تقدير عام",
        iso="عزل الصدفة",
        iso_ok="تم بنجاح",
        iso_fail="فشل (تم استخدام الصورة الأصلية)",
        agree="توافق النماذج",
        agree_yes="اتفقوا ✓",
        agree_no="اختلفوا",
        top5="أعلى 5 احتمالات",
        notes="ملاحظات الفحص",
        no_notes="ما في ملاحظات. الصورة واضحة والنماذج متوافقة.",
        n_iso="تعذّر عزل الصدفة عن الخلفية، فالنتيجة أقل دقة. جرّبي خلفية أبسط وإضاءة أوضح.",
        n_dis="موديل التصنيف وموديل التشابه رشّحوا صنفين مختلفين. قارني الصورة بالعيّنات المرجعية تحت.",
        n_low="الثقة منخفضة. أقرب 3 احتمالات: {alts}",
        foot="الأسعار تقديرية وبتتغيّر حسب الحجم والحالة والندرة. عدّلي prices.json للأسعار الدقيقة.",
        st_ok="تعريف مؤكّد",
        st_mid="يحتاج مراجعة",
        st_low="ثقة منخفضة",
        sim="تشابه {p}%",
        ref="مرجع",
        qr_title="للفتح على الهاتف",
        qr_scan="قم بمسح الباركود بكاميرا الهاتف.",
        qr_pub="رابط عام (https)،الكاميرا تقوم بفتح.",
        qr_lan="يجب ان يكون الهاتف على نفس الشبكة",
        qr_install="لتفعيل الباركود: pip install qrcode[pil]",
        sep="، ",
    ),
    "en": dict(
        tag="Snap a shell, get an ID report - from the beach to the lab",
        btn=" Identify the shell",
        seg="Isolated shell (what the model sees)",
        gal="Closest reference samples from the dataset",
        empty_t="Your report appears here",
        empty_p="Upload or take a photo of a shell and a full identification report shows up in seconds.",
        rep_title="Specimen Identification Report",
        brand="ShellVis · Shell Lab",
        sci="Scientific name",
        genus="Genus",
        conf="Confidence",
        price="Estimated price",
        p_manual="manual entry",
        p_genus="genus-based estimate",
        p_general="general estimate",
        iso="Shell isolation",
        iso_ok="Succeeded",
        iso_fail="Failed (original image used)",
        agree="Model agreement",
        agree_yes="Agree ✓",
        agree_no="Disagree",
        top5="Top 5 candidates",
        notes="Inspection notes",
        no_notes="No notes. The photo is clear and the models agree.",
        n_iso="Could not isolate the shell from the background, so accuracy is lower. Try a plainer background and better light.",
        n_dis="The classifier and the similarity model picked different species. Compare your photo with the reference samples below.",
        n_low="Low confidence. Top 3 candidates: {alts}",
        foot="Prices are estimates and vary with size, condition and rarity. Edit prices.json for exact prices.",
        st_ok="CONFIRMED ID",
        st_mid="NEEDS REVIEW",
        st_low="LOW CONFIDENCE",
        sim="Match {p}%",
        ref="Reference",
        qr_title="📱 Open it on your phone",
        qr_scan="Scan the QR code with your phone camera.",
        qr_pub="Public https link - the camera works.",
        qr_lan="Your phone must be on the same Wi-Fi.",
        qr_install="To enable the QR code: pip install qrcode[pil]",
        sep=", ",
    ),
}

def load_prices() -> dict:
    prices = {}
    if os.path.exists(PRICES_FILE):
        with open(PRICES_FILE, "r", encoding="utf-8") as f:
            prices = json.load(f)
    changed = False
    for name in CLASS_NAMES.values():
        if name not in prices:
            prices[name] = ""
            changed = True
    if changed:
        with open(PRICES_FILE, "w", encoding="utf-8") as f:
            json.dump(prices, f, ensure_ascii=False, indent=2)
    return prices


PRICES = load_prices()

GENUS_PRICES = {
    "conus": (5, 40), "cypraea": (3, 30), "cowrie": (3, 30), "murex": (5, 30),
    "chicoreus": (5, 30), "hexaplex": (4, 20), "strombus": (5, 35), "lambis": (6, 35),
    "lobatus": (5, 25), "cassis": (10, 50), "cypraecassis": (10, 50),
    "haliotis": (10, 60), "nautilus": (15, 60), "turbo": (3, 25), "trochus": (3, 15),
    "tectus": (3, 15), "oliva": (2, 10), "terebra": (2, 10), "pecten": (3, 20),
    "chlamys": (3, 20), "mimachlamys": (3, 15), "spondylus": (15, 80),
    "tonna": (8, 30), "charonia": (30, 150), "cymatium": (5, 25), "fusinus": (5, 30),
    "fasciolaria": (5, 30), "pleuroploca": (10, 40), "voluta": (15, 100),
    "cymbiola": (15, 100), "melo": (20, 80), "harpa": (10, 40), "mitra": (3, 20),
    "volva": (3, 15), "ovula": (3, 15), "natica": (2, 8), "polinices": (2, 8),
    "nerita": (1, 5), "cerithium": (1, 8), "telescopium": (3, 10),
    "architectonica": (3, 12), "bursa": (5, 20), "epitonium": (5, 25),
    "cardium": (2, 10), "tellina": (2, 10), "tridacna": (20, 120),
    "lopha": (3, 12), "ostrea": (2, 8), "pinna": (5, 25), "turritella": (2, 10),
    "bolinus": (4, 15), "cypholophus": (3, 10),
}
DEFAULT_RANGE = (3, 20)


def get_price(name: str):
    manual = PRICES.get(name, "")
    if manual:
        return manual, "p_manual"
    n = norm(name)
    best = None
    for genus, rng in GENUS_PRICES.items():
        if genus in n and (best is None or len(genus) > len(best[0])):
            best = (genus, rng)
    if best:
        lo, hi = best[1]
        return f"${lo} – ${hi}", "p_genus"
    lo, hi = DEFAULT_RANGE
    return f"${lo} – ${hi}", "p_general"


def hist_of(bgr: np.ndarray) -> np.ndarray:
    bgr = cv2.resize(bgr, (128, 128))
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256])
    cv2.normalize(h, h, 0, 1, cv2.NORM_MINMAX)
    return h


def class_of_path(path: str, class_norms: dict):
    rel = os.path.relpath(path, DATASET_DIR)
    target = norm(rel)
    best, best_len = None, 0
    for cname, cn in class_norms.items():
        if cn and cn in target and len(cn) > best_len:
            best, best_len = cname, len(cn)
    return best


def build_index():
    files = []
    for root, _, names in os.walk(DATASET_DIR):
        for n in names:
            if n.lower().endswith(IMG_EXT):
                files.append(os.path.join(root, n))
    files.sort()

    if os.path.exists(INDEX_CACHE):
        try:
            with open(INDEX_CACHE, "rb") as f:
                cached = pickle.load(f)
            if cached.get("n") == len(files):
                print(" dataset index loaded from cache")
                return cached["index"]
        except Exception:
            pass

    class_norms = {c: norm(c) for c in CLASS_NAMES.values()}
    index = {c: [] for c in CLASS_NAMES.values()}
    unmatched = 0
    for p in files:
        c = class_of_path(p, class_norms)
        if c is None:
            unmatched += 1
            continue
        img = cv2.imread(p)
        if img is None:
            continue
        index[c].append((p, hist_of(img)))

    print(f" indexed {len(files) - unmatched} images, skipped {unmatched} without class")
    with open(INDEX_CACHE, "wb") as f:
        pickle.dump({"n": len(files), "index": index}, f)
    return index


REF_INDEX = build_index() if os.path.isdir(DATASET_DIR) else {}

print(" Loading isolation model (first run downloads ~170MB)...")
SESSION = new_session(REMBG_MODEL)


def isolate(pil: Image.Image):
    rgba = np.array(remove(pil.convert("RGB"), session=SESSION))
    alpha = rgba[..., 3]
    m = (alpha > 40).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n <= 1:
        return None
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    if stats[k, cv2.CC_STAT_AREA] < 0.01 * m.size:
        return None
    rgb = rgba[..., :3].astype(np.float32) * (alpha[..., None] / 255.0)
    rgb[lab != k] = 0
    return rgb.astype(np.uint8)


def tight_square(rgb_black: np.ndarray, frac: float = SHELL_FRAC, size: int = 384) -> Image.Image:
    ys, xs = np.where(rgb_black.max(axis=2) > 12)
    if len(xs) == 0:
        return Image.fromarray(rgb_black).resize((size, size))
    crop = rgb_black[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = crop.shape[:2]
    side = int(max(h, w) / frac)
    canvas = np.zeros((side, side, 3), np.uint8)
    y0, x0 = (side - h) // 2, (side - w) // 2
    canvas[y0:y0 + h, x0:x0 + w] = crop
    return Image.fromarray(canvas).resize((size, size), Image.LANCZOS)


def pad_square(pil: Image.Image, size: int = 384) -> Image.Image:
    a = np.array(pil.convert("RGB"))
    h, w = a.shape[:2]
    s = max(h, w)
    canvas = np.zeros((s, s, 3), np.uint8)
    canvas[(s - h) // 2:(s - h) // 2 + h, (s - w) // 2:(s - w) // 2 + w] = a
    return Image.fromarray(canvas).resize((size, size))

MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)
EMB, LABELS, PATHS, CLASS_IDX = None, [], [], {}

if USE_KNN and REF_INDEX:
    from transformers import AutoModel
    DINO = AutoModel.from_pretrained(EMB_MODEL).to(DEVICE).eval()

    @torch.no_grad()
    def embed(pils):
        arr = np.stack([
            (np.asarray(p.convert("RGB").resize((224, 224)), dtype=np.float32) / 255.0 - MEAN) / STD
            for p in pils
        ])
        x = torch.from_numpy(arr).permute(0, 3, 1, 2).to(DEVICE)
        h = DINO(pixel_values=x).last_hidden_state
        f = torch.cat([h[:, 0], h[:, 1:].mean(1)], dim=1)
        return torch.nn.functional.normalize(f, dim=1).cpu().numpy().astype(np.float32)

    def _load_img(p):
        try:
            return tight_square(np.array(Image.open(p).convert("RGB")))
        except Exception:
            return Image.new("RGB", (384, 384))

    def build_embeddings():
        from concurrent.futures import ThreadPoolExecutor
        paths, labels = [], []
        for c, items in REF_INDEX.items():
            for p, _ in items:
                paths.append(p)
                labels.append(c)

        if os.path.exists(EMB_CACHE) and os.path.exists(EMB_PATHS_CACHE):
            with open(EMB_PATHS_CACHE, "rb") as f:
                if pickle.load(f) == paths:
                    print("⚡ dataset embeddings loaded from cache")
                    return np.load(EMB_CACHE), labels, paths

        out, start = [], 0
        if os.path.exists(PART_EMB) and os.path.exists(PART_PATHS):
            with open(PART_PATHS, "rb") as f:
                if pickle.load(f) == paths:
                    P = np.load(PART_EMB)
                    out, start = [P], len(P)
                    print(f"↩️ resuming from saved progress: {start}/{len(paths)}")

        print(f"🧬 embedding {len(paths) - start} remaining images (progress is saved)...")
        t0, B = time.time(), 64
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
            for n, i in enumerate(range(start, len(paths), B)):
                batch = list(ex.map(_load_img, paths[i:i + B]))
                out.append(embed(batch))
                done = i + len(batch)
                if n % SAVE_EVERY == 0 and n > 0:
                    E_part = np.concatenate(out)
                    out = [E_part]
                    np.save(".tmp_partial.npy", E_part)
                    os.replace(".tmp_partial.npy", PART_EMB)
                    with open(PART_PATHS, "wb") as f:
                        pickle.dump(paths, f)
                    el = time.time() - t0
                    rate = (done - start) / el
                    print(f"   {done}/{len(paths)}  (~{(len(paths) - done) / rate / 60:.0f} min left) 💾")

        E = np.concatenate(out)
        np.save(EMB_CACHE, E)
        with open(EMB_PATHS_CACHE, "wb") as f:
            pickle.dump(paths, f)
        for fn in (PART_EMB, PART_PATHS):
            if os.path.exists(fn):
                os.remove(fn)
        return E, labels, paths

    EMB, LABELS, PATHS = build_embeddings()
    for i, c in enumerate(LABELS):
        CLASS_IDX.setdefault(c, []).append(i)
    CLASS_IDX = {c: np.array(v) for c, v in CLASS_IDX.items()}
else:
    USE_KNN = False


def knn_scores(q_emb: np.ndarray, k: int = 30, T: float = 0.05):
    sims = EMB @ q_emb
    idx = np.argpartition(-sims, k)[:k]
    idx = idx[np.argsort(-sims[idx])]
    w = np.exp((sims[idx] - sims[idx[0]]) / T)
    scores = {}
    for i, wi in zip(idx, w):
        scores[LABELS[i]] = scores.get(LABELS[i], 0.0) + float(wi)
    s = sum(scores.values())
    return {c: v / s for c, v in scores.items()}, sims


def yolo_scores(variants, topn: int = 30):
    acc = None
    for im in variants:
        p = model.predict(im, verbose=False)[0].probs.data.cpu().numpy()
        acc = p if acc is None else acc + p
    acc = acc / len(variants)
    order = np.argsort(acc)[::-1][:topn]
    return {model.names[int(i)]: float(acc[i]) for i in order}


def fuse(y: dict, k: dict, w: float = W_YOLO):
    names = set(y) | set(k)
    f = {n: w * y.get(n, 0.0) + (1 - w) * k.get(n, 0.0) for n in names}
    return sorted(f.items(), key=lambda x: -x[1])[:5]


def find_references(best: str, sims, k: int = 3):
    """بيرجع [(path, similarity أو None)] - الكابشن بيتولّد حسب اللغة."""
    if USE_KNN and sims is not None and best in CLASS_IDX:
        ids = CLASS_IDX[best]
        ids = ids[np.argsort(-sims[ids])][:k]
        return [(PATHS[i], float(sims[i])) for i in ids]
    items = REF_INDEX.get(best, [])[:k]
    return [(p, None) for p, _ in items]


def gallery_items(refs, lang):
    L = TX[lang]
    out = []
    for p, s in refs:
        try:
            cap = L["sim"].format(p=f"{s * 100:.0f}") if s is not None else L["ref"]
            out.append((Image.open(p).convert("RGB"), cap))
        except Exception:
            pass
    return out

def pretty(name: str):
    parts = [p for p in re.split(r"[_\-\s]+", name.strip()) if p]
    if not parts:
        return name, ""
    return parts[0].capitalize(), " ".join(parts[1:]).lower()


def sci(name: str) -> str:
    g, s = pretty(name)
    return H.escape(f"{g} {s}".strip())


def empty_report(lang="ar") -> str:
    L = TX[lang]
    return (f"<div class='report empty' dir='{DIR[lang]}'><div class='empty-ico'>🐚</div>"
            f"<h3>{L['empty_t']}</h3><p>{L['empty_p']}</p></div>")


def hero_html(lang="ar") -> str:
    return (f"<div class='hero'><h1><span>🐚</span> ShellVis</h1><p>{TX[lang]['tag']}</p></div>")


def build_report(top5, y, k_scores, iso_ok, lang="ar"):
    L = TX[lang]
    best, conf = top5[0]
    pct = conf * 100
    genus, species = pretty(best)
    price, price_key = get_price(best)

    y_top = max(y, key=y.get)
    agree, k_top = None, None
    if USE_KNN and k_scores:
        k_top = max(k_scores, key=k_scores.get)
        agree = (y_top == k_top)

    if pct >= 60 and agree is not False and iso_ok:
        stamp, stamp_cls = L["st_ok"], "ok"
    elif pct >= LOW_CONF * 100:
        stamp, stamp_cls = L["st_mid"], "mid"
    else:
        stamp, stamp_cls = L["st_low"], "low"

    ref_no = "SV-" + time.strftime("%y%m%d-%H%M%S")
    date = time.strftime("%Y/%m/%d  %H:%M")

    bars = ""
    for n, c in top5:
        bars += (
            f"<div class='bar'><span class='bn'>{sci(n)}</span>"
            f"<span class='bt'><i style='width:{max(c * 100, 1.5):.1f}%'></i></span>"
            f"<span class='bv'>{c * 100:.1f}%</span></div>"
        )

    if agree is None:
        agree_txt = "—"
    elif agree:
        agree_txt = L["agree_yes"]
    else:
        agree_txt = f"{L['agree_no']}: <i>{sci(y_top)}</i> ↔ <i>{sci(k_top)}</i>"

    notes = []
    if not iso_ok:
        notes.append(L["n_iso"])
    if agree is False:
        notes.append(L["n_dis"])
    if conf < LOW_CONF:
        alts = L["sep"].join(sci(n) for n, _ in top5[:3])
        notes.append(L["n_low"].format(alts=alts))
    notes_html = "".join(f"<li>{n}</li>" for n in notes) or f"<li>{L['no_notes']}</li>"

    return f"""
<div class='report' dir='{DIR[lang]}'>
  <div class='stamp {stamp_cls}'>{stamp}</div>
  <div class='r-head'>
    <div><b>{L['rep_title']}</b><small>{L['brand']}</small></div>
    <div class='r-meta'><span>{ref_no}</span><span>{date}</span></div>
  </div>

  <div class='r-main'>
    <div class='r-name'>
      <small>{L['sci']}</small>
      <h2><em>{H.escape(genus)}</em> <em>{H.escape(species)}</em></h2>
      <small>{L['genus']}: <i>{H.escape(genus)}</i></small>
    </div>
    <div class='ring' style='--p:{pct:.1f}'><div><b>{pct:.0f}%</b><small>{L['conf']}</small></div></div>
  </div>

  <table class='r-tab'>
    <tr><th>{L['price']}</th><td><b>{H.escape(price)}</b> <small>({L[price_key]})</small></td></tr>
    <tr><th>{L['iso']}</th><td>{L['iso_ok'] if iso_ok else L['iso_fail']}</td></tr>
    <tr><th>{L['agree']}</th><td>{agree_txt}</td></tr>
  </table>

  <div class='r-sec'>{L['top5']}</div>
  <div class='bars'>{bars}</div>

  <div class='r-sec'>{L['notes']}</div>
  <ul class='notes'>{notes_html}</ul>

  <div class='r-foot'>{L['foot']}</div>
</div>
"""

def pipeline(input_image, lang):
    if input_image is None:
        return None, empty_report(lang), [], None

    pil = input_image.convert("RGB")
    black = isolate(pil)
    iso_ok = black is not None
    if iso_ok:
        variants = [tight_square(black, 0.80), tight_square(black, 0.92)]
    else:
        variants = [pad_square(pil)]
    shown = variants[0]

    y = yolo_scores(variants)
    sims, k_scores = None, {}
    if USE_KNN:
        q = embed(variants).mean(0)
        q /= np.linalg.norm(q)
        k_scores, sims = knn_scores(q)
        top5 = fuse(y, k_scores)
    else:
        top5 = sorted(y.items(), key=lambda x: -x[1])[:5]

    refs = find_references(top5[0][0], sims)
    state = dict(top5=top5, y=y, k=k_scores, iso=iso_ok, refs=refs)
    return shown, build_report(top5, y, k_scores, iso_ok, lang), gallery_items(refs, lang), state


def relang(lang, state):
    L = TX[lang]
    if state:
        rep = build_report(state["top5"], state["y"], state["k"], state["iso"], lang)
        gal = gallery_items(state["refs"], lang)
    else:
        rep, gal = empty_report(lang), []
    return (hero_html(lang),
            gr.update(value=L["btn"]),
            gr.update(label=L["seg"]),
            rep,
            gr.update(label=L["gal"], value=gal),
            qr_html(lang))


CSS = """
:root {
  --deep:#0a3d4d; --sea:#117a8b; --turq:#25b9b1; --foam:#f3fbf8;
  --sand:#e8cf9e; --ink:#16282c; --coral:#e2725b;
}
html, body { background:#0a3d4d !important; }
html[dir=rtl] .gradio-container { direction: rtl; }
html[dir=ltr] .gradio-container { direction: ltr; }
.gradio-container {
  background: transparent !important;
  font-family: 'Cairo', 'Segoe UI', Tahoma, 'Noto Naskh Arabic', sans-serif !important;
  max-width: 1100px !important; position: relative; z-index: 2;
}
footer { display:none !important; }

/* ===== مبدّل اللغة ===== */
#lang { max-width: 260px; margin: 10px auto 0 !important; background:transparent !important; border:none !important; }
#lang .wrap { display:flex !important; gap:0 !important; padding:3px !important; border-radius:999px !important;
  background: rgba(6,45,58,.6) !important; border:1px solid rgba(255,255,255,.4) !important;
  backdrop-filter: blur(10px); justify-content:center; }
#lang label { flex:1; justify-content:center; border-radius:999px !important; padding:6px 16px !important;
  background:transparent !important; border:none !important; box-shadow:none !important;
  color:#fff !important; cursor:pointer; font-weight:700; }
#lang label.selected { background: var(--turq) !important; color:#05303a !important; }
#lang input { display:none !important; }
#lang label span { color:inherit !important; }

/* ===== الهيدر ===== */
.hero { text-align:center; padding: 18px 10px 6px; color:#fff; }
.hero h1 { margin:0; font-size: clamp(2.4rem, 7vw, 4rem); font-weight:800; letter-spacing:.02em; direction:ltr;
  text-shadow: 0 4px 22px rgba(0,40,50,.55); }
.hero h1 span { display:inline-block; animation: sway 5s ease-in-out infinite; transform-origin:50% 90%; }
@keyframes sway { 50% { transform: rotate(-9deg) translateY(-3px); } }
.hero p { margin:6px 0 0; font-size:1.15rem; color:#e3f8f5; text-shadow:0 2px 12px rgba(0,40,50,.7); }

/* ===== الزجاج ===== */
.glass { background: rgba(6,42,54,.55) !important; backdrop-filter: blur(14px) saturate(1.3);
  -webkit-backdrop-filter: blur(14px) saturate(1.3);
  border:1px solid rgba(255,255,255,.35) !important; border-radius:24px !important;
  box-shadow: 0 14px 40px rgba(0,40,55,.4); padding:16px !important; }
.glass .block, .glass .form { background:transparent !important; border:none !important; box-shadow:none !important; }
.glass label span, .glass .label-wrap span { color:#fff !important; }

/* ===== منطقة الرفع ===== */
#scan { position:relative; border:2px dashed rgba(255,255,255,.65) !important; border-radius:20px !important;
  background: rgba(255,255,255,.08) !important; min-height: 340px; }
#scan::before, #scan::after { content:""; position:absolute; width:34px; height:34px; z-index:5; pointer-events:none;
  border:3px solid #fff; opacity:.95; }
#scan::before { top:8px; inset-inline-end:8px; border-inline-start:none; border-bottom:none; border-radius:0 12px 0 0; }
#scan::after { bottom:8px; inset-inline-start:8px; border-inline-end:none; border-top:none; border-radius:0 0 0 12px; }
#scan button, #scan .wrap { border:none !important; background:transparent !important; color:#fff !important; }
/* نص الرفع مترجم (بدل Drop Image Here) */
#scan button > .wrap { font-size:0 !important; }
#scan button > .wrap .icon-wrap { font-size:1rem; }
#scan button > .wrap::after { font-size:1.05rem; font-weight:600; color:#eafffb; display:block; margin-top:10px; }
html[lang=ar] #scan button > .wrap::after { content:"اسحب صورة الصدفة هنا أو اضغط للرفع"; }
html[lang=en] #scan button > .wrap::after { content:"Drop a shell photo here or click to upload"; }

#go { background: linear-gradient(135deg,#ff8a5c,#e2725b) !important; border:none !important; color:#fff !important;
  font-weight:700; border-radius:16px !important; box-shadow:0 8px 20px rgba(226,114,91,.45); }
#go:hover { transform: translateY(-1px); filter:brightness(1.05); }
#seg img { border-radius:16px; background:#000; }

/* ===== التقرير ===== */
.report { position:relative; background:linear-gradient(180deg,#fdfefd,#f1f8f5); color:var(--ink);
  border-radius:20px; padding:22px 24px 16px;
  box-shadow: 0 18px 44px rgba(0,35,45,.4), inset 0 0 0 1px rgba(17,122,139,.15);
  background-image: repeating-linear-gradient(0deg, transparent 0 31px, rgba(17,122,139,.05) 31px 32px); }
.report::before { content:""; position:absolute; top:0; inset-inline-end:24px; width:46px; height:10px;
  background:var(--turq); border-radius:0 0 8px 8px; }
.report.empty { text-align:center; padding:46px 20px; }
.report.empty .empty-ico { font-size:3rem; display:inline-block; animation: sway 4s ease-in-out infinite; }
.report.empty h3 { margin:8px 0 4px; }
.report.empty p { margin:0; opacity:.7; }
.r-head { display:flex; justify-content:space-between; align-items:flex-start; gap:12px;
  border-bottom:2px solid var(--ink); padding-bottom:10px; }
.r-head b { font-size:1.25rem; display:block; }
.r-head small { opacity:.65; }
.r-meta { display:flex; flex-direction:column; align-items:flex-end; font-size:.8rem; opacity:.7;
  font-family: Consolas, monospace; direction:ltr; }
.r-main { display:flex; justify-content:space-between; align-items:center; gap:16px; margin:18px 0 12px; }
.r-name small { opacity:.6; display:block; }
.r-name h2 { margin:2px 0 4px; font-size:clamp(1.5rem,4.6vw,2.2rem); line-height:1.15; direction:ltr;
  font-family: Georgia, 'Times New Roman', serif; color:var(--deep); }
.report[dir=rtl] .r-name h2 { text-align:right; }
.report[dir=ltr] .r-name h2 { text-align:left; }
.r-name h2 em:first-child { font-weight:700; }
.ring { --p:0; flex:none; width:104px; height:104px; border-radius:50%;
  background: conic-gradient(var(--turq) calc(var(--p) * 1%), #dbe9e6 0);
  display:grid; place-items:center; animation: fill 1.2s ease-out; }
.ring > div { width:78px; height:78px; border-radius:50%; background:#fff; display:grid; place-content:center; text-align:center; }
.ring b { font-size:1.5rem; color:var(--deep); line-height:1; }
.ring small { font-size:.72rem; opacity:.6; }
@property --p { syntax:'<number>'; inherits:false; initial-value:0; }
@keyframes fill { from { --p:0; } }
.r-tab { width:100%; border-collapse:collapse; margin:4px 0 8px; }
.r-tab th { text-align:start; font-weight:600; width:38%; padding:8px 0; opacity:.7; border-bottom:1px dashed #b9cfca; }
.r-tab td { padding:8px 0; border-bottom:1px dashed #b9cfca; }
.r-tab small { opacity:.6; }
.r-sec { margin:14px 0 6px; font-weight:700; color:var(--sea); }
.bar { display:grid; grid-template-columns: 1fr 1.4fr 3.4em; gap:8px; align-items:center; margin:5px 0; font-size:.92rem; }
.bn { direction:ltr; font-family:Georgia,serif; font-style:italic; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.report[dir=rtl] .bn { text-align:right; }
.report[dir=ltr] .bn { text-align:left; }
.bt { height:9px; background:#dbe9e6; border-radius:9px; overflow:hidden; direction:ltr; }
.bt i { display:block; height:100%; border-radius:9px; background:linear-gradient(90deg,var(--turq),var(--sea)); }
.bv { font-family:Consolas,monospace; direction:ltr; text-align:end; opacity:.8; }
.notes { margin:0; padding:0; padding-inline-start:20px; font-size:.93rem; line-height:1.7; }
.r-foot { margin-top:12px; padding-top:8px; border-top:1px solid #cfe0dc; font-size:.78rem; opacity:.6; }
.stamp { position:absolute; inset-inline-start:20px; bottom:46px; transform: rotate(-12deg); padding:4px 14px; border:3px solid;
  border-radius:10px; font-weight:800; letter-spacing:.03em; opacity:.85; pointer-events:none; background:rgba(255,255,255,.5); }
.stamp.ok { color:#12805c; } .stamp.mid { color:#c27a12; } .stamp.low { color:#c0392b; }

/* ===== QR ===== */
.qr { display:flex; align-items:center; gap:14px; color:#fff; }
.qr img { width:108px; height:108px; border-radius:12px; background:#fff; padding:6px; }
.qr b { display:block; margin-bottom:4px; }
.qr code { direction:ltr; display:inline-block; background:rgba(0,0,0,.3); padding:2px 8px; border-radius:8px; font-size:.8rem; word-break:break-all; }

@media (max-width: 700px) {
  .glass { padding:10px !important; border-radius:20px !important; }
  .report { padding:18px 14px 12px; }
  .ring { width:86px; height:86px; } .ring > div { width:64px; height:64px; } .ring b { font-size:1.2rem; }
  .stamp { bottom:40px; font-size:.85rem; }
}
@media (prefers-reduced-motion: reduce) {
  .hero h1 span, .empty-ico { animation: none !important; }
}
@media print {
  .sea, .shells, #glsea, #snd, .hero, #lang, .glass:not(.rep) { display:none !important; }
  html, body { background:#fff !important; }
}
""" + EXTRA_CSS

QR_URL, QR_B64 = "", ""     


def qr_html(lang="ar") -> str:
    if not QR_URL:
        return ""
    L = TX[lang]
    note = L["qr_pub"] if SHARE else L["qr_lan"]
    if QR_B64:
        img = f"<img src='data:image/png;base64,{QR_B64}' alt='QR'>"
        scan = f"{L['qr_scan']}<br>"
    else:
        img, scan = "", ""
    return (f"<div class='qr' dir='{DIR[lang]}'>{img}<div><b>{L['qr_title']}</b>{scan}"
            f"<small>{note}</small><br><code>{QR_URL}</code></div></div>")


SET_LANG_JS = """(l, s) => {
  const ar = (l === 'ar');
  document.documentElement.lang = ar ? 'ar' : 'en';
  document.documentElement.dir = ar ? 'rtl' : 'ltr';
  return [l, s];
}"""

with gr.Blocks(title="ShellVis") as demo:
    gr.HTML(BG_HTML)
    lang = gr.Radio(choices=[("العربية", "ar"), ("English", "en")], value="ar",
                    show_label=False, container=False, elem_id="lang")
    hero = gr.HTML(hero_html("ar"))
    state = gr.State(None)

    with gr.Row(equal_height=False):
        with gr.Column(scale=5, elem_classes="glass"):
            inp = gr.Image(type="pil", show_label=False, height=360,
                           sources=["upload", "webcam", "clipboard"], elem_id="scan")
            btn = gr.Button(TX["ar"]["btn"], elem_id="go", size="lg")
            seg = gr.Image(type="pil", label=TX["ar"]["seg"],
                           height=240, interactive=False, elem_id="seg")
        with gr.Column(scale=6, elem_classes="glass rep"):
            report = gr.HTML(empty_report("ar"))
            gal = gr.Gallery(label=TX["ar"]["gal"], columns=3, height=190)

    with gr.Row():
        with gr.Column(elem_classes="glass"):
            qr_box = gr.HTML()

    run_outputs = [seg, report, gal, state]
    btn.click(pipeline, inputs=[inp, lang], outputs=run_outputs)
    inp.change(pipeline, inputs=[inp, lang], outputs=run_outputs)

    lang.change(relang, inputs=[lang, state],
                outputs=[hero, btn, seg, report, gal, qr_box], js=SET_LANG_JS)
    demo.load(qr_html, inputs=lang, outputs=qr_box)

def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def make_qr(url: str) -> str:
    try:
        import qrcode
    except ImportError:
        print("ℹ️ " + TX["en"]["qr_install"])
        return ""
    qr = qrcode.QRCode(border=1, box_size=8)
    qr.add_data(url)
    qr.make(fit=True)
    print("\n📱 Scan from your phone:")
    qr.print_ascii(invert=True)
    buf = io.BytesIO()
    qr.make_image(fill_color="#0a3d4d", back_color="white").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


if __name__ == "__main__":
    kw = dict(
        server_name="127.0.0.1" if SHARE else "0.0.0.0",
        server_port=PORT, share=SHARE,
        theme=gr.themes.Soft(primary_hue="teal"), css=CSS,
        prevent_thread_lock=True,
    )
    try:
        _, local_url, share_url = demo.launch(head=HEAD, **kw)
    except TypeError:             
        demo.head = HEAD
        kw.pop("theme"), kw.pop("css")
        demo.theme, demo.css = gr.themes.Soft(primary_hue="teal"), CSS
        _, local_url, share_url = demo.launch(**kw)
    QR_URL = share_url or f"http://{lan_ip()}:{PORT}"
    print(f"🔗 {QR_URL}")
    QR_B64 = make_qr(QR_URL)
    demo.block_thread()