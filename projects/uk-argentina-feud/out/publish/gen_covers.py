#!/usr/bin/env python
"""发布包封面生成器（pixel-chronicle 账号模板 v1，2026-07-20）。
用法: film-ir/.venv/bin/python gen_covers.py  （在仓库根运行）
依赖: pillow fonttools brotli；字体从 compose/assets/fonts 的 woff2 现场转 ttf。
版式: 程序化羊皮纸底 + 片内标题帧(奶油keyline+软阴影) + 大字「钱·血·球」层级。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fontTools.ttLib import TTFont
import random, tempfile, os

PROJ = 'projects/uk-argentina-feud'
PUB = f'{PROJ}/out/publish'
TMP = tempfile.mkdtemp()

def ttf(name):
    f = TTFont(f'{PROJ}/compose/assets/fonts/{name}.woff2'); f.flavor = None
    p = f'{TMP}/{name}.ttf'; f.save(p); return p

SERIF, SANS7, SANS4 = ttf('serif-sc-700-cn'), ttf('sans-sc-700-cn'), ttf('sans-sc-400-cn')
serif = lambda s: ImageFont.truetype(SERIF, s)
sans7 = lambda s: ImageFont.truetype(SANS7, s)
sans4 = lambda s: ImageFont.truetype(SANS4, s)
INK=(46,36,24); CREAM=(244,238,222); RED=(154,62,34); SUB=(104,84,56)

def parchment(w,h,seed=7):
    base = Image.new('RGB',(w,h),(201,168,118))
    noise = Image.effect_noise((w,h),18).convert('L')
    p = Image.blend(base, Image.merge('RGB',[noise]*3), 0.10)
    d = ImageDraw.Draw(p,'RGBA'); rnd = random.Random(seed)
    for y in range(0,h,3): d.line([(0,y),(w,y)],(120,95,60,rnd.randint(4,10)))
    vig = Image.new('L',(w,h),0)
    ImageDraw.Draw(vig).rectangle([int(w*.06),int(h*.04),int(w*.94),int(h*.96)],fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(min(w,h)//7))
    return Image.composite(p, Image.new('RGB',(w,h),(150,120,78)), vig.point(lambda v:130+v//2))

def center(d, CW, y, text, font, fill):
    x = (CW - d.textlength(text, font=font)) / 2
    d.text((x+3,y+3), text, font=font, fill=(60,44,24,70)); d.text((x,y), text, font=font, fill=fill)

def keyline_paste(canvas, img, y):
    x = (canvas.width - img.width)//2
    sh = Image.new('RGB',(img.width+26,img.height+26),(140,112,72)).filter(ImageFilter.GaussianBlur(2))
    canvas.paste(sh,(x-9,y-5))
    canvas.paste(Image.new('RGB',(img.width+16,img.height+16),CREAM),(x-8,y-8)); canvas.paste(img,(x,y))

frame = Image.open(f'{PUB}/_title_frame.png').convert('RGB')  # ffmpeg -ss 27.5 抽自 out/final.mp4

c = parchment(1080,1440); d = ImageDraw.Draw(c,'RGBA')
center(d,1080, 96, '英国 × 阿根廷', sans7(64), INK)
keyline_paste(c, frame.resize((1016,572), Image.LANCZOS), 250)
center(d,1080, 908, '钱 · 血 · 球', serif(150), INK)
center(d,1080, 1118, '三章讲完 220 年恩怨', sans7(66), RED)
center(d,1080, 1246, '从 1806 的账本，到世界杯的横幅', sans4(44), SUB)
c.save(f'{PUB}/cover_xhs_3x4.jpg', quality=92)

c = parchment(1080,1920,seed=11); d = ImageDraw.Draw(c,'RGBA')
center(d,1080, 170, '英国 × 阿根廷', sans7(72), INK)
keyline_paste(c, frame.resize((1016,572), Image.LANCZOS), 380)
center(d,1080, 1105, '钱 · 血 · 球', serif(172), INK)
center(d,1080, 1360, '三章讲完 220 年恩怨', sans7(74), RED)
center(d,1080, 1502, '补时绝杀之后，那条横幅从哪来', sans4(48), SUB)
c.save(f'{PUB}/cover_douyin_9x16.jpg', quality=92)
print('covers regenerated')
