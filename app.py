from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import os, base64, json
from io import BytesIO

app = Flask(__name__)
API_KEY = os.environ.get("IMAGE_SERVICE_KEY", "finspire2025")

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def make_slide(topic, brand, primary, secondary, footer_ig, slide):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(12 + (6-12)*t)
        g = int(14 + (8-14)*t)
        b = int(35 + (20-35)*t)
        draw.line([(0,y),(W,y)], fill=(r,g,b))
    draw.rectangle([0,0,W,6], fill=(201,168,76))
    draw.rectangle([0,H-90,W,H], fill=(0,0,0))
    draw.line([(0,H-90),(W,H-90)], fill=(201,168,76,80), width=1)
    try:
        fb = ImageFont.truetype(FB, 56)
        fm = ImageFont.truetype(FB, 22)
        fr = ImageFont.truetype(FR, 18)
        fs = ImageFont.truetype(FR, 15)
    except:
        fb = fm = fr = fs = ImageFont.load_default()
    num = slide.get("slide", 1)
    title = slide.get("title", "")
    body = slide.get("body", "")
    cat = slide.get("category", "").upper()
    draw.text((52, 52), f"{cat}  ·  {num:02d}/05", font=fs, fill=(201,168,76))
    draw.text((52, 100), title, font=fb, fill=(255,255,255))
    draw.line([(52,180),(200,180)], fill=(201,168,76), width=3)
    y = 200
    for line in body.split("\n"):
        draw.text((52, y), line, font=fr, fill=(200,200,200))
        y += 30
    draw.text((52, H-68), brand.upper(), font=fm, fill=(201,168,76))
    draw.text((52, H-43), f"Follow {footer_ig} for daily insights", font=fs, fill=(150,150,150))
    buf = BytesIO()
    img.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()

@app.route("/generate", methods=["POST"])
def generate():
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401
    data = request.json
    slides = data.get("slides", [])
    brand = data.get("brand_name", "Finspire")
    topic = data.get("topic", "")
    primary = data.get("primary_color", "#0F3460")
    secondary = data.get("secondary_color", "#E94560")
    footer_ig = data.get("footer_ig", "@handle")
    images = []
    for slide in slides:
        b64 = make_slide(topic, brand, primary, secondary, footer_ig, slide)
        images.append({"slide": slide.get("slide"), "base64": b64})
    return jsonify({"images": images, "count": len(images)})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
