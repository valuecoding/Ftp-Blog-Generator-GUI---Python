import os
import tkinter as tk
from tkinter import filedialog, Text, ttk
from ftplib import FTP_TLS, error_perm
import html
import re
import traceback
import ssl
import hashlib
import sys

CONFIG = {
    "ftp_server": "INSERT YOUR FTP SERVER",
    "ftp_user": "INSERT YOUR FTP USER",
    "ftp_pass": "INSERT YOUR FTP PASSWORD",
    "ftp_directory": "INSERT YOUR FTP DIRECTORY"
}

EXPECTED_FINGERPRINT = "INSERT FINGERPRINT HERE FOR FTP"

complete_html = ""
image_urls = {}

def get_certificate_fingerprint(ssl_sock):
    der_cert = ssl_sock.getpeercert(binary_form=True)
    sha1_hash = hashlib.sha1(der_cert).hexdigest()
    fingerprint = ':'.join(sha1_hash[i:i+2] for i in range(0, len(sha1_hash), 2))
    return fingerprint.lower()

def connect_to_ftp(config):
    try:
        context = ssl.create_default_context()
        ftp = FTP_TLS(context=context)
        ftp.connect(config["ftp_server"], 21)
        ftp.auth()
        fingerprint = get_certificate_fingerprint(ftp.sock)
        if fingerprint != EXPECTED_FINGERPRINT.lower():
            raise ssl.SSLError(f"Zertifikatsfingerabdruck stimmt nicht überein. Erwartet: {EXPECTED_FINGERPRINT}, Erhalten: {fingerprint}")
        ftp.prot_p()
        ftp.login(user=config["ftp_user"], passwd=config["ftp_pass"])
        ftp.set_pasv(True)
        ftp.cwd(config["ftp_directory"])
        return ftp
    except (error_perm, ssl.SSLError, Exception) as e:
        print(f"FTP Fehler: {e}")
        traceback.print_exc()
        raise ConnectionError(f"FTP Verbindung fehlgeschlagen: {e}")

def upload_single_image(ftp, image_path):
    try:
        with open(image_path, 'rb') as file:
            filename = os.path.basename(image_path)
            ftp.storbinary(f'STOR {filename}', file)
            url = f"https://INSERT_YOUR_WEBSITE/{filename}"
            print(f'Uploaded {filename} to {config["ftp_directory"]}')
            return url
    except Exception as e:
        print(f"Fehler beim Hochladen von {image_path}: {e}")
        traceback.print_exc()
        return None

def replace_inline_markers(text):
    pattern = re.compile(r'@B:(.*?)@BEND', re.DOTALL)
    return pattern.sub(r'<strong>\1</strong>', text)

def format_blog_content(blog_content, image_urls_with_alt):
    html_output = []
    in_list = False
    lines = blog_content.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("@H1:"):
            content = line[4:].strip()
            content = replace_inline_markers(content)
            html_output.append(f"<h1>{html.escape(content)}</h1>")
        elif line.startswith("@H2:"):
            content = line[4:].strip()
            content = replace_inline_markers(content)
            html_output.append(f"<h2>{html.escape(content)}</h2>")
        elif line.startswith("@P:"):
            content = line[3:].strip()
            content = replace_inline_markers(content)
            html_output.append(f"<p>{html.escape(content)}</p>")
        elif line.startswith("@I:"):
            content = line[3:].strip()
            content = replace_inline_markers(content)
            html_output.append(f"<em>{html.escape(content)}</em>")
        elif line.startswith("@A:"):
            try:
                link_text, url = line[3:].strip().split("|", 1)
                link_text = replace_inline_markers(link_text.strip())
                html_output.append(f'<a href="{html.escape(url.strip())}">{link_text}</a>')
            except ValueError:
                html_output.append('<p style="color:red;">Ungültiges Link-Format für @A.</p>')
        elif line.startswith("@li:"):
            content = line[4:].strip()
            content = replace_inline_markers(content)
            if not in_list:
                html_output.append("<ul>")
                in_list = True
            html_output.append(f"<li>{content}</li>")
        elif line.startswith("@IMG"):
            img_match = re.match(r'^@IMG(\d+)$', line)
            if img_match:
                img_num = img_match.group(1)
                img_key = f"@IMG{img_num}"
                img_info = image_urls_with_alt.get(img_key)
                if img_info:
                    url, alt_text = img_info
                    html_output.append(f'<div class="image-container"><img src="{url}" alt="{html.escape(alt_text)}"></div>')
                else:
                    html_output.append(f'<p style="color:red;">Bild {img_key} fehlt!</p>')
        elif re.match(r'^@IMG\d+-ALT:', line):
            continue
        else:
            if in_list:
                html_output.append("</ul>")
                in_list = False
            content = replace_inline_markers(line)
            html_output.append(f"<p>{html.escape(content)}</p>")

    if in_list:
        html_output.append("</ul>")

    return "\n".join(html_output)

def validate_html(html_content):
    try:
        import lxml.html
    except ImportError:
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "lxml"])
            import lxml.html
        except Exception as e:
            print("lxml konnte nicht installiert werden. Bitte installiere es manuell mit 'pip install lxml'.")
            return False
    try:
        lxml.html.fromstring(html_content)
        return True
    except Exception as e:
        print(f"HTML Validation Error: {e}")
        return False

def copy_to_clipboard(text, text_type):
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        status_label.config(text=f"{text_type} in die Zwischenablage kopiert.", fg="green")
    except Exception as e:
        status_label.config(text=f"Fehler beim Kopieren von {text_type}.", fg="red")
        print(e)
        traceback.print_exc()

def copy_prompt():
    try:
        root.clipboard_clear()
        root.clipboard_append(PROMPT_TEXT)
        status_label.config(text="Prompt in die Zwischenablage kopiert.", fg="green")
    except Exception as e:
        status_label.config(text="Fehler beim Kopieren des Prompts.", fg="red")
        print(e)
        traceback.print_exc()

def generate_html():
    global complete_html
    blog_content = text_input.get("1.0", tk.END).strip()

    alt_texts = {}
    for match in re.finditer(r'^@IMG(\d+)-ALT:\s*(.+)$', blog_content, re.MULTILINE):
        img_num = match.group(1)
        alt_text = match.group(2).strip()
        alt_key = f"@IMG{img_num}"
        alt_texts[alt_key] = alt_text

    blog_content_cleaned = re.sub(r'^@IMG\d+-ALT:.*$', '', blog_content, flags=re.MULTILINE)

    image_urls_with_alt = {}
    for img_key, url in image_urls.items():
        alt_text = alt_texts.get(img_key, "Bild")
        image_urls_with_alt[img_key] = (url, alt_text)

    html_content = format_blog_content(blog_content_cleaned, image_urls_with_alt)
    title_text = extract_title(html_content)
    meta_description = extract_meta_description(html_content)
    meta_keywords = extract_meta_keywords(html_content)

    try:
        complete_html = html_template.format(
            title=meta_description,
            keywords=meta_keywords,
            title_text=title_text,
            content=html_content,
            nexo_link=""
        )
    except KeyError as e:
        status_label.config(text=f"Fehler bei der Platzhalter-Ersetzung: {e}", fg="red")
        print(f"Platzhalter-Fehler: {e}")
        traceback.print_exc()
        return

    if validate_html(complete_html):
        status_label.config(text="HTML generiert.", fg="green")
        copy_html_button.config(state=tk.NORMAL)
    else:
        status_label.config(text="Generiertes HTML ist ungültig.", fg="red")

def extract_title(html_content):
    match = re.search(r'<h1>(.*?)</h1>', html_content)
    return match.group(1) if match else "Blogeintrag"

def extract_meta_description(html_content):
    match = re.search(r'<p>(.*?)</p>', html_content, re.DOTALL)
    return match.group(1) if match else "Blogeintrag über Kryptowährungen."

def extract_meta_keywords(html_content):
    keywords = set(re.findall(r'\b\w+\b', html_content.lower()))
    common_words = {"und", "die", "der", "das", "ist", "in", "auf", "für", "mit", "von", "zu", "den", "als", "auch", "sich"}
    keywords = keywords - common_words
    return ', '.join(list(keywords)[:10])

def upload_images(image_index):
    global image_urls
    filetypes = (("Bilddateien", "*.jpg;*.jpeg;*.png;*.webp"), ("Alle Dateien", "*.*"))
    filepath = filedialog.askopenfilename(
        initialdir=os.path.expanduser("~/Pictures"),
        title=f"Bild {image_index} auswählen",
        filetypes=filetypes
    )
    if filepath:
        try:
            ftp = connect_to_ftp(CONFIG)
        except ConnectionError as e:
            status_label.config(text=str(e), fg="red")
            return

        url = upload_single_image(ftp, filepath)
        if url:
            image_key = f"@IMG{image_index}"
            image_urls[image_key] = url
            status_label.config(text=f"Bild {image_index} hochgeladen: {url}", fg="green")
        else:
            status_label.config(text=f"Fehler beim Hochladen von Bild {image_index}", fg="red")

        ftp.quit()

html_template = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="styles.css">
    <meta name="description" content="{title}">
    <meta name="keywords" content="{keywords}">
    <title>{title_text}</title>
</head>
<body>
    <div class="container blogentry-three">
        <header>
        </header>

        <article class="content">
            {content}
        </article>

        <footer>
            <p>© 2024 YourFooterText. Alle Rechte vorbehalten.</p>
        </footer>
    </div>
</body>
</html>
"""

PROMPT_TEXT = """
Hi, ich brauche einen ausführlichen, informativen Blogeintrag, den ich nach Bedarf anpassen kann.
Die Struktur des Blogeintrags sollte wie folgt sein:

- @H1: Überschrift
- @H2: Zwischenüberschriften
- @P: Absätze
- @B: Fetter Text @BEND
- @I: Kursiver Text
- @A: Linktext|URL für Links. **ACHTUNG: Der Link muss ein funktionierender Link zu einer relevanten Webseite sein. Beispiel-Links wie example.com sind nicht erlaubt.**
- @li: Listenpunkte (Verwende @B und @BEND für Fettschrift innerhalb von Listen)

Füge an passenden Stellen im Text die Platzhalter @IMG1, @IMG2 und @IMG3 für Bilder ein. Direkt nach jedem @IMGx-Platzhalter füge automatisch einen SEO-freundlichen Alt-Text hinzu, der den Inhalt des Bildes beschreibt.

Beispiel für die Bildplatzhalter:

@IMG1
@IMG1-ALT: Beschreibung des ersten Bildes, optimiert für SEO.

Achte darauf, dass die Alt-Texte präzise, beschreibend und mit relevanten Keywords versehen sind.

Verwende @B für Fettschrift und @BEND, um die Fettschrift zu beenden. Diese Platzhalter können überall im Text verwendet werden, nicht nur innerhalb von Listen.

Beispiel für Fettschrift in Listen:
@li: Punkt 1
@li: Punkt 2 @B: fetter Text @BEND restlicher Text

**Wichtige Anweisung bezüglich Links:** Verwende in deinen @A: Markups ausschließlich funktionierende und relevante Links. Beispiel-Links sind absolut verboten.
"""

root = tk.Tk()
root.title("Blog Generator coded by valuecoding 2024")

style = ttk.Style()
style.theme_use('clam')

main_frame = tk.Frame(root, padx=10, pady=10)
main_frame.pack(fill=tk.BOTH, expand=True)

status_label = tk.Label(main_frame, text="", fg="green")
status_label.pack(anchor='w')

input_frame = tk.Frame(main_frame)
input_frame.pack(fill=tk.BOTH, expand=True)

text_label = tk.Label(input_frame, text="Blog Inhalt:")
text_label.grid(row=0, column=0, sticky='w')
text_input = Text(input_frame, height=20, width=100)
text_input.grid(row=1, column=0, columnspan=3, pady=(0,10))

buttons_frame = tk.Frame(main_frame)
buttons_frame.pack(fill=tk.X, pady=10)

generate_blog_button = tk.Button(buttons_frame, text="Blog generieren", command=generate_html, fg="white", bg="green")
generate_blog_button.pack(side=tk.RIGHT, padx=(30, 5), pady=5)

copy_frame = tk.Frame(main_frame)
copy_frame.pack(fill=tk.X, pady=5)

copy_html_button = tk.Button(copy_frame, text="HTML kopieren", state=tk.DISABLED, command=lambda: copy_to_clipboard(complete_html, "HTML"))
copy_html_button.pack(side=tk.LEFT, padx=5)

copy_prompt_button = tk.Button(copy_frame, text="Prompt kopieren", command=copy_prompt)
copy_prompt_button.pack(side=tk.LEFT, padx=5)

upload_image1_button = tk.Button(main_frame, text="Bild 1 hochladen", command=lambda: upload_images(1))
upload_image1_button.pack(fill=tk.X, pady=2)

upload_image2_button = tk.Button(main_frame, text="Bild 2 hochladen", command=lambda: upload_images(2))
upload_image2_button.pack(fill=tk.X, pady=2)

upload_image3_button = tk.Button(main_frame, text="Bild 3 hochladen", command=lambda: upload_images(3))
upload_image3_button.pack(fill=tk.X, pady=2)

root.mainloop()
