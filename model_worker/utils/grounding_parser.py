import seaborn as sns
from PIL import Image, ImageDraw, ImageFont
import matplotlib.font_manager
import spacy
import re

nlp = spacy.load("en_core_web_sm")

def draw_boxes(image, boxes, texts, output_fn='output.png'):
    box_width = 5
    color_palette = sns.color_palette("husl", len(boxes))
    colors = [(int(r*255), int(g*255), int(b*255)) for r, g, b in color_palette]

    width, height = image.size
    absolute_boxes = [[(int(box[0] * width), int(box[1] * height), int(box[2] * width), int(box[3] * height)) for box in b] for b in boxes]
    
    overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    font_path = sorted(matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf'))[0]
    font = ImageFont.truetype(font_path, size=26)

    for box, text, color in zip(absolute_boxes, texts, colors):
        for b in box:
            draw.rectangle(b, outline=color, width=box_width)
            if not text:
                continue
            splited_text = text.split('\n')
            num_lines = len(splited_text)
            text_width, text_height = font.getbbox(splited_text[0])[-2:]
            y_start = b[3] - text_height * num_lines - box_width
            if b[2] - b[0] < 100 or b[3] - b[1] < 100:
                y_start = b[3]
            for i, line in enumerate(splited_text):
                text_width, text_height = font.getbbox(line)[-2:]
                x = b[0] + box_width
                y = y_start + text_height * i
                draw.rectangle([x, y, x+text_width, y+text_height], fill=(128, 128, 128, 160))
                draw.text((x, y), line, font=font, fill=(255, 255, 255))
    img_with_overlay = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
    img_with_overlay.save(output_fn)

def boxstr_to_boxes(box_str):
    boxes = [[int(y)/1000 for y in x.split(',')] for x in box_str.split(';') if x.replace(',', '').isdigit()]
    return boxes

def text_to_dict(text):
    doc = nlp(text)

    box_matches = list(re.finditer(r'\[\[([^\]]+)\]\]', text))
    box_positions = [match.start() for match in box_matches]

    noun_phrases = []
    boxes = []

    for match, box_position in zip(box_matches, box_positions):
        nearest_np_start = max([0] + [chunk.start_char for chunk in doc.noun_chunks if chunk.end_char <= box_position])
        noun_phrase = text[nearest_np_start:box_position].strip()
        if noun_phrase and noun_phrase[-1] == '?':
            noun_phrase = text[:box_position].strip()
        box_string = match.group(1)
        
        noun_phrases.append(noun_phrase)
        boxes.append(boxstr_to_boxes(box_string))

    pairs = []
    for noun_phrase, box_string in zip(noun_phrases, boxes):
        pairs.append((noun_phrase.lower(), box_string))
    return dict(pairs)

def parse_response(img, response, output_fn='output.png'):
    img = img.convert('RGB')
    width, height = img.size
    ratio = min(1920 / width, 1080 / height)
    new_width = int(width * ratio)
    new_height = int(height * ratio)
    new_img = img.resize((new_width, new_height), Image.LANCZOS)
    pattern = r"\[\[(.*?)\]\]"
    positions = re.findall(pattern, response)
    boxes = [[[int(y) for y in x.split(',')] for x in pos.split(';') if x.replace(',', '').isdigit()] for pos in positions]
    dic = text_to_dict(response)
    if not dic:
        texts = []
        boxes = []
    else:
        texts, boxes = zip(*dic.items())
    # draw_boxes(new_img, boxes, texts, output_fn=output_fn)