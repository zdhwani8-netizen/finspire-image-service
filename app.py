from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import os, base64, textwrap
from io import BytesIO

app = Flask(__name__)
API_KEY = os.environ.get("IMAGE_SERVICE_KEY", "finspire2025")

# Font paths - DejaVu available on all Linux systems
FB  = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FO  = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"

W, H = 1080, 1080

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def make_gradient(draw, color1, color2):
    for y in range(H):
        t = y / H
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

def add_decorative_circles(img, primary_rgb):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([580, -220, 1220, 420], fill=(*primary_rgb, 20))
    od.ellipse([660, -140, 1160, 360], fill=(*primary_rgb, 12))
    od.ellipse([-120, 740, 240, 1100], fill=(*primary_rgb, 15))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def draw_text_wrapped(draw, text, x, y, font, color, max_width, line_spacing=8):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    
    current_y = y
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=color)
        bbox = draw.textbbox((0, 0), line, font=font)
        current_y += (bbox[3] - bbox[1]) + line_spacing
    return current_y

def make_base(slide_num, total, primary_rgb, brand_name, footer_ig):
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    
    # Dark gradient background
    bg1 = (12, 14, 35)
    bg2 = (6, 8, 20)
    make_gradient(draw, bg1, bg2)
    
    # Decorative circles
    img = add_decorative_circles(img, primary_rgb)
    draw = ImageDraw.Draw(img)
    
    # Gold top bar
    GOLD = (201, 168, 76)
    draw.rectangle([0, 0, W, 7], fill=GOLD)
    
    # Footer
    draw.rectangle([0, H-95, W, H], fill=(0, 0, 0))
    draw.line([(0, H-95), (W, H-95)], fill=(*GOLD, 100), width=1)
    
    # Footer text
    try:
        fb_footer = ImageFont.truetype(FB, 18)
        fr_footer = ImageFont.truetype(FR, 14)
    except:
        fb_footer = fr_footer = ImageFont.load_default()
    
    draw.text((56, H-73), brand_name.upper(), font=fb_footer, fill=(*GOLD, 220))
    draw.text((56, H-47), f"Follow {footer_ig} for daily insights", font=fr_footer, fill=(150, 150, 150))
    
    # Slide dots
    dot_area_x = W - 160
    for i in range(total):
        x = dot_area_x + i * 20
        if i == slide_num - 1:
            draw.rounded_rectangle([x, H-62, x+28, H-54], radius=4, fill=GOLD)
        else:
            draw.ellipse([x, H-62, x+10, H-54], fill=(80, 80, 80))
    
    return img, draw

def slide_hook(slide, brand_name, footer_ig, primary_rgb, total):
    GOLD = (201, 168, 76)
    WHITE = (255, 255, 255)
    
    img, draw = make_base(1, total, primary_rgb, brand_name, footer_ig)
    
    try:
        f_tag   = ImageFont.truetype(FR, 15)
        f_num   = ImageFont.truetype(FR, 15)
        f_title = ImageFont.truetype(FB, 54)
        f_body  = ImageFont.truetype(FR, 22)
        f_cta   = ImageFont.truetype(FB, 19)
        f_bullet= ImageFont.truetype(FR, 20)
    except:
        f_tag = f_num = f_title = f_body = f_cta = f_bullet = ImageFont.load_default()
    
    category = slide.get("category", "HOOK").upper()
    title = slide.get("title", "")
    body = slide.get("body", "")
    
    # Category tag
    draw.text((56, 56), f"{category}  ·  FINSPIRE", font=f_tag, fill=(*GOLD, 180))
    draw.text((W-56, 56), "01 / 05", font=f_num, fill=(150, 150, 150), anchor="ra")
    
    # Title - large and bold
    y = 110
    lines = []
    words = title.split()
    current = []
    for word in words:
        test = ' '.join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=f_title)
        if bbox[2] <= W - 112:
            current.append(word)
        else:
            if current: lines.append(' '.join(current))
            current = [word]
    if current: lines.append(' '.join(current))
    
    for i, line in enumerate(lines[:2]):
        color = GOLD if i == len(lines[:2]) - 1 else WHITE
        draw.text((56, y), line, font=f_title, fill=color)
        bbox = draw.textbbox((0, 0), line, font=f_title)
        y += bbox[3] - bbox[1] + 8
    
    # Gold divider
    y += 16
    draw.line([(56, y), (220, y)], fill=GOLD, width=3)
    y += 28
    
    # Body text
    y = draw_text_wrapped(draw, body, 56, y, f_body, (200, 200, 200), W - 112, 10)
    y += 30
    
    # CTA box
    box_y = y + 10
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([56, box_y, W-56, box_y+110], radius=20, 
                          fill=(255, 255, 255, 18), outline=(255, 255, 255, 35), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.line([(56, box_y), (64, box_y), (64, box_y+110), (56, box_y+110)], fill=GOLD, width=3)
    draw.text((84, box_y+18), "Swipe through for the complete guide →", font=f_cta, fill=(200, 200, 200))
    draw.text((84, box_y+50), "Learn. Save. Invest smarter.", font=f_cta, fill=WHITE)
    draw.text((84, box_y+80), "Your money deserves better strategy. 🚀", font=f_bullet, fill=(*GOLD, 200))
    
    return img

def slide_content(slide, slide_num, brand_name, footer_ig, primary_rgb, total):
    GOLD = (201, 168, 76)
    WHITE = (255, 255, 255)
    
    img, draw = make_base(slide_num, total, primary_rgb, brand_name, footer_ig)
    
    try:
        f_tag   = ImageFont.truetype(FR, 15)
        f_num   = ImageFont.truetype(FR, 15)
        f_title = ImageFont.truetype(FB, 58)
        f_title2= ImageFont.truetype(FB, 46)
        f_body  = ImageFont.truetype(FR, 21)
        f_bold  = ImageFont.truetype(FB, 21)
    except:
        f_tag = f_num = f_title = f_title2 = f_body = f_bold = ImageFont.load_default()
    
    category = slide.get("category", "").upper()
    title = slide.get("title", "")
    body = slide.get("body", "")
    
    # Category + slide number
    draw.text((56, 56), category, font=f_tag, fill=(*GOLD, 180))
    draw.text((W-56, 56), f"0{slide_num} / 0{total}", font=f_num, fill=(150, 150, 150), anchor="ra")
    
    # Title
    y = 110
    words = title.split()
    lines = []
    current = []
    font_to_use = f_title if len(title) < 20 else f_title2
    for word in words:
        test = ' '.join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font_to_use)
        if bbox[2] <= W - 112:
            current.append(word)
        else:
            if current: lines.append(' '.join(current))
            current = [word]
    if current: lines.append(' '.join(current))
    
    for i, line in enumerate(lines[:2]):
        color = GOLD if i == 1 else WHITE
        draw.text((56, y), line, font=font_to_use, fill=color)
        bbox = draw.textbbox((0, 0), line, font=font_to_use)
        y += bbox[3] - bbox[1] + 6
    
    # Divider
    y += 18
    draw.line([(56, y), (200, y)], fill=GOLD, width=3)
    y += 28
    
    # Body - split into bullet points
    sentences = [s.strip() for s in body.replace('•', '\n•').split('\n') if s.strip()]
    if not sentences:
        sentences = [body]
    
    for sentence in sentences[:4]:
        if not sentence: continue
        # Card background for each point
        card_h = 80
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle([56, y-8, W-56, y+card_h], radius=14,
                              fill=(255, 255, 255, 15), outline=(255, 255, 255, 25), width=1)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # Bullet
        draw.ellipse([70, y+10, 82, y+22], fill=GOLD)
        
        # Text
        draw_text_wrapped(draw, sentence.lstrip('•').strip(), 96, y+4, f_body, (210, 210, 210), W-160, 6)
        y += card_h + 12
        
        if y > H - 200:
            break
    
    return img

def slide_cta(slide, slide_num, brand_name, footer_ig, primary_rgb, total):
    GOLD = (201, 168, 76)
    GOLD_LIGHT = (232, 201, 122)
    WHITE = (255, 255, 255)
    
    img, draw = make_base(slide_num, total, primary_rgb, brand_name, footer_ig)
    
    try:
        f_tag   = ImageFont.truetype(FR, 15)
        f_star  = ImageFont.truetype(FB, 90)
        f_main  = ImageFont.truetype(FR, 30)
        f_date  = ImageFont.truetype(FB, 88)
        f_sub   = ImageFont.truetype(FR, 24)
        f_btn   = ImageFont.truetype(FB, 22)
        f_small = ImageFont.truetype(FR, 17)
    except:
        f_tag = f_star = f_main = f_date = f_sub = f_btn = f_small = ImageFont.load_default()
    
    draw.text((56, 56), "KEY TAKEAWAY", font=f_tag, fill=(*GOLD, 180))
    draw.text((W-56, 56), f"0{slide_num} / 0{total}", font=f_tag, fill=(150, 150, 150), anchor="ra")
    
    # Star decoration
    draw.text((W//2, 160), "✦", font=f_star, fill=(*GOLD, 200), anchor="mm")
    
    # Main message
    draw.text((W//2, 240), "Your deadline:", font=f_main, fill=(180, 180, 180), anchor="mm")
    draw.text((W//2, 330), "March 31", font=f_date, fill=GOLD, anchor="mm")
    draw.text((W//2, 410), "Act now or wait another year.", font=f_sub, fill=WHITE, anchor="mm")
    
    # Divider
    draw.line([(W//2-120, 445), (W//2+120, 445)], fill=(*GOLD, 60), width=1)
    
    # Checklist box
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([56, 460, W-56, 600], radius=20, fill=(255,255,255,18), outline=(255,255,255,30), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    checklist = ["✅  Review your portfolio this week", "✅  Identify loss-making positions", "✅  Consult your CA before selling"]
    for i, item in enumerate(checklist):
        draw.text((W//2, 482 + i*38), item, font=f_small, fill=(200, 200, 200), anchor="mm")
    
    # CTA Button
    overlay2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od2 = ImageDraw.Draw(overlay2)
    od2.rounded_rectangle([56, 618, W-56, 698], radius=28, fill=(*GOLD, 230))
    img = Image.alpha_composite(img.convert("RGBA"), overlay2).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.text((W//2, 658), f"Follow {footer_ig} for a FREE checklist 👇", font=f_btn, fill=(20, 20, 40), anchor="mm")
    
    draw.text((W//2, 720), "Share this with someone who needs it 🙏", font=f_small, fill=(120, 120, 120), anchor="mm")
    
    return img

def generate_slide(slide, slide_num, total, brand_name, footer_ig, primary_rgb):
    category = slide.get("category", "").upper()
    if slide_num == 1 or category == "HOOK":
        return slide_hook(slide, brand_name, footer_ig, primary_rgb, total)
    elif slide_num == total or category in ["KEY TAKEAWAY", "CTA"]:
        return slide_cta(slide, slide_num, brand_name, footer_ig, primary_rgb, total)
    else:
        return slide_content(slide, slide_num, brand_name, footer_ig, primary_rgb, total)

def img_to_base64(img):
    buf = BytesIO()
    img.save(buf, "PNG", quality=95)
    return base64.b64encode(buf.getvalue()).decode()

@app.route("/generate", methods=["POST"])
def generate():
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401
    
    data = request.json
    slides = data.get("slides", [])
    brand  = data.get("brand_name", "Finspire")
    topic  = data.get("topic", "")
    primary_hex = data.get("primary_color", "#0F3460")
    footer_ig   = data.get("footer_ig", "@handle")
    total  = len(slides) if slides else 5
    
    try:
        primary_rgb = hex_to_rgb(primary_hex)
    except:
        primary_rgb = (15, 52, 96)
    
    images = []
    for i, slide in enumerate(slides):
        slide_num = slide.get("slide", i + 1)
        img = generate_slide(slide, slide_num, total, brand, footer_ig, primary_rgb)
        images.append({
            "slide": slide_num,
            "base64": img_to_base64(img),
            "filename": f"slide_{slide_num:02d}.png"
        })
    
    return jsonify({"images": images, "count": len(images), "topic": topic})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Finspire Image Generator"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
