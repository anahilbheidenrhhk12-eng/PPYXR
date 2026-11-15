import base64
from io import BytesIO
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import qrcode
import re
import random 

def generate_qr_code_base64(data_text):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1,
    )
    qr.add_data(data_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')
    buffered = BytesIO()
    img.save(buffered, format='PNG')
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{img_str}'


def process_card_to_pdf_edge(
    input_path,
    output_pdf_path,
    new_username,
    new_lastname,
    new_firstname,
    new_valid_until="October 31th ,2028",
    new_image_path=None,
):
    # 1. Prevent ElementTree namespace prefix issues
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')

    tree = ET.parse(input_path)
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg', 'xlink': 'http://www.w3.org/1999/xlink'}

    # 2. Inject CSS style with Google Fonts (Inter + Montserrat)
    style_tag = root.find('.//svg:style', ns)
    print_css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400..700;1,400..700&family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap');
    @page {
        size: 1554px 2140px;
        margin: 0;
    }
    body, html {
        margin: 0;
        padding: 0;
        width: 1554px;
        height: 2140px;
    }
    svg {
        display: block;
        width: 100% !important;
        height: 100% !important;
    }
    """
    if style_tag is not None:
        style_tag.text = (style_tag.text or '') + print_css
    else:
        new_style = ET.Element('{http://www.w3.org/2000/svg}style')
        new_style.text = print_css
        root.insert(0, new_style)

    CENTER_X_COORD = '1056'

    # 3. Update and auto-center text fields
    for text_node in root.findall('.//svg:text', ns):
        transform_attr = text_node.get('transform', '')
        tspan_node = text_node.find('svg:tspan', ns)

        if tspan_node is not None:
            is_target = False
            target_y = ''
            new_value = ''

            if 'translate(827 1232)' in transform_attr:
                is_target = True
                target_y = '1317'
                new_value = str(new_username)
            elif 'translate(812 1070)' in transform_attr:
                is_target = True
                target_y = '1121'
                new_value = str(new_lastname)
            elif 'translate(837.999 1132)' in transform_attr:
                is_target = True
                target_y = '1209'
                new_value = str(new_firstname)

            if is_target:
                tspan_node.text = new_value
                if 'x' in tspan_node.attrib:
                    del tspan_node.attrib['x']
                if 'y' in tspan_node.attrib:
                    del tspan_node.attrib['y']
                text_node.set('text-anchor', 'middle')
                text_node.set('transform', f'translate({CENTER_X_COORD} {target_y})')

    # 4. Consolidate and update "Valid Until" text block with Inter Italic and Superscript
    date_nodes = [n for n in root.findall('.//svg:text', ns) if 'translate(247 1570)' in n.get('transform', '')]
    for n in date_nodes:
        root.remove(n)

    if new_valid_until:
        date_text = ET.Element('{http://www.w3.org/2000/svg}text', {
            'transform': 'translate(247 1598.9)', # Applied Y shift (1570 + 28.9) directly to prevent Edge headless drift
            'fill': 'black',
            'style': 'white-space: pre',
            'font-family': 'Inter',
            'font-size': '30',
            'font-style': 'italic',
            'letter-spacing': '0em'
        })
        
        # Regex to automatically extract superscript logic (e.g., "th", "st", "nd", "rd")
        match = re.match(r"(.*?)(\d+)(st|nd|rd|th)(.*)", new_valid_until)
        if match:
            base_str, day, suffix, year_str = match.groups()
            
            # Auto-prepend 'Valid Until ' if user only passes the raw date
            if "Valid Until" not in base_str:
                base_str = f"Valid Until {base_str}"
                
            tspan_base = ET.SubElement(date_text, '{http://www.w3.org/2000/svg}tspan')
            tspan_base.text = f"{base_str}{day}"
            
            tspan_super = ET.SubElement(date_text, '{http://www.w3.org/2000/svg}tspan', {
                'baseline-shift': 'super',
                'font-size': '20'
            })
            tspan_super.text = suffix
            
            tspan_year = ET.SubElement(date_text, '{http://www.w3.org/2000/svg}tspan')
            tspan_year.text = year_str
        else:
            tspan_base = ET.SubElement(date_text, '{http://www.w3.org/2000/svg}tspan')
            tspan_base.text = new_valid_until if "Valid Until" in new_valid_until else f"Valid Until {new_valid_until}"

        root.append(date_text)

    # 5. Update avatar picture
    if new_image_path:
        with open(new_image_path, 'rb') as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
            mime_type = (
                'image/png' if new_image_path.lower().endswith('.png') else 'image/jpeg'
            )
            new_avatar_uri = f'data:{mime_type};base64,{encoded_string}'

        image_node = root.find(".//svg:image[@id='image1_17_40']", ns)
        if image_node is not None:
            image_node.set('{http://www.w3.org/1999/xlink}href', new_avatar_uri)

    # 6. Update QR code
    qr_group = root.find(".//svg:g[@style='mix-blend-mode:darken']", ns)
    if qr_group is not None:
        new_qr_data_uri = generate_qr_code_base64(new_username)
        qr_group.clear()
        qr_group.attrib['style'] = 'mix-blend-mode:darken'

        new_qr_image = ET.Element(
            '{http://www.w3.org/2000/svg}image',
            {
                'x': '1018',
                'y': '1354',
                'width': '112',
                'height': '112',
                'preserveAspectRatio': 'none',
            },
        )
        new_qr_image.set('{http://www.w3.org/1999/xlink}href', new_qr_data_uri)
        qr_group.append(new_qr_image)

    # 7. Render PDF cleanly using Chrome Headless via secure temp file
    edge_path = '/usr/bin/google-chrome'
    
    # Fallback in case chromium is used instead of chrome
    if not os.path.exists(edge_path):
        edge_path = '/usr/bin/chromium-browser'

    abs_pdf = os.path.abspath(output_pdf_path)

    with tempfile.NamedTemporaryFile(
        delete=False, mode='w', suffix='.svg', encoding='utf-8'
    ) as temp_svg:
        temp_svg_path = temp_svg.name

    try:
        tree.write(temp_svg_path, encoding='utf-8', xml_declaration=True)

        cmd = [
            edge_path,
            '--headless',
            '--disable-gpu',
            '--no-sandbox',
            '--log-level=3',
            '--no-margins',
            '--print-to-pdf-no-header',
            f'--print-to-pdf={abs_pdf}',
            os.path.abspath(temp_svg_path),
        ]

        subprocess.run(cmd, check=True)
        print(
            f'  [ + ] Successfully generated clean, single-page pixel-perfect PDF at:'
            f' {output_pdf_path}'
        )

    finally:
        if os.path.exists(temp_svg_path):
            os.remove(temp_svg_path)

def get_random_file(directory_path):
  try:
    entries = os.listdir(directory_path)
    files = [f for f in entries if os.path.isfile(os.path.join(directory_path, f))]
    if not files:
      return None
    return random.choice(files)
  except FileNotFoundError:
    return 'Error: Directory not found.'
  except PermissionError:
    return 'Error: Permission denied.'

def load_users():
  if not os.path.exists('./Resources/users.txt'):
    print(' [-] ERROR: ./Resources/users.txt not found. Stopping script...')
    os._exit(1)
  try:
    with open('./Resources/users.txt', 'r', encoding='utf-8') as f:
      lines = [l.strip() for l in f if ':' in l]
      return [l.split(':')[0] for l in lines], [l.split(':')[1] for l in lines]
  except Exception as e:
    print(f' [-] ERROR: Failed to read users.txt - {str(e)}')
    os._exit(1)

def load_users():
    if not os.path.exists("./Resources/users.txt"):
        print(" [-] ERROR: ./Resources/users.txt not found. Stopping script...")
        os._exit(1)
    try:
        with open("./Resources/users.txt", "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if ":" in l]
            return [l.split(":")[0] for l in lines], [l.split(":")[1] for l in lines]
    except Exception as e:
        print(f" [-] ERROR: Failed to read users.txt - {str(e)}")
        os._exit(1)



def GetPDFfile(first_name, last_name):

    full_name = f"{first_name}{last_name}"

    Face = get_random_file('../images')
    username, _ = os.path.splitext(Face)
    username = username.rstrip('-')

    # Ensure Output directory exists before saving
    os.makedirs('./Output', exist_ok=True)
    OutputPDF = f'./Output/{first_name}{last_name}.pdf'

    process_card_to_pdf_edge(
        input_path='./Resources/Template.svg',
        output_pdf_path=OutputPDF,
        new_username=username,
        new_lastname=last_name,
        new_firstname=first_name,
        new_image_path=f'../images/{Face}',
    )
    return OutputPDF

f_names, l_names = load_users()
