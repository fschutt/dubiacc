import sys, base64, os, json

# Returns if the script is run in a production 
# environment ("with --production")
def is_prod():
    l = len(sys.argv)
    if l > 1:
        return sys.argv[1] == "--production"
    else:
        return False
    
# Reads a text file as a string
def read_file(path):
    text_file = open(path, 'r')
    text_file_contents = text_file.read()
    text_file.close()
    return text_file_contents

# Reads a binary file as a base64 string
def read_file_base64(path):
    encoded_string = ""
    with open(path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return encoded_string

# Writes a text string to a file
def write_file(string, path):
    text_file = open(path, "w+", newline='')
    text_file.write(string)
    text_file.close()

# Chunks an array into chunks of maximum n items
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# Loads templates from the /templates folder, so while generating articles
# we don't have to touch the filesystem. Also does some preliminary CSS inlining.
def load_templates():
    templates = {}
    templates["index"] = read_file("./templates/lorem.html")
    inlined_styles_light = read_file("./static/css/inlined-styles.css")
    inlined_styles_dark = read_file("./static/css/inlined-styles-color-dark.css")
    header_template = read_file("./templates/head.html")
    header_template = header_template.replace(
        "<!-- INLINED_STYLES_LIGHT -->", 
        "<style id='inlined-styles-colors'>\r\n" + inlined_styles_light + "    </style>"
    )
    header_template = header_template.replace(
        "<!-- INLINED_STYLES_DARK -->", 
        "<style id='inlined-styles-colors-dark' media='all and (prefers-color-scheme: dark)'>\r\n" + inlined_styles_dark + "    </style>"
    )
    header_template = header_template.replace(
        "<!-- CRITICAL_CSS -->", 
        "<style id='critical-css'>\r\n" + read_file("./static/css/critical.css") + "    </style>"
    )
    templates["head"] = header_template
    templates["table-of-contents"] = read_file("./templates/table-of-contents.html")
    templates["page-metadata"] = read_file("./templates/page-metadata.html")
    templates["body-noscript"] = read_file("./templates/body-noscript.html")
    templates["header-navigation"] = read_file("./templates/header-navigation.html")
    return templates

def get_root_href():
    root_href = "http://127.0.0.1:8080"
    if is_prod():
        root_href = "https://dubia.cc"
    return root_href

def load_articles():
    articles = {}
    for lang in os.listdir("./articles"):
        if lang == ".DS_Store":
            continue
        if not(os.path.isdir("./" + lang)):
            os.mkdir("./" + lang)
        for slug in os.listdir("./articles/" + lang):
            if slug == ".DS_Store":
                continue
            filepath = "./articles/" + lang + "/" + slug + "/index.md.json"
            if os.path.isfile(filepath):
                index_md = read_file(filepath)
                articles["" + lang + "/" + slug] = json.loads(index_md)
            else:
                print("WARN: missing file /articles/" + lang + "/" + slug + "/index.md.json")
                print("WARN: run md2json in the root dir to fix this issue")
                if (is_prod()):
                    raise Exception("")
    return articles

# Generates a .gitignore so that during development, the generated 
# articles aren't comitted to source control
def generate_gitignore(articles_dict):
    filenames = list(map(lambda x: x + ".html", articles_dict.keys()))
    dirs = []
    for k in articles_dict.keys():
        dirs.append(k.split("/")[0])
    filenames.extend(map(lambda x: "/" + x, dirs))
    filenames.append("/venv")
    filenames.append("*.md.json")
    filenames.append("md2json-bin")
    filenames.append("/md2json/target")
    filenames.append("/md2json/out.txt")
    filenames.append("/venv/*")
    filenames.sort()
    filenames = list(set(filenames))
    gitignore = "\r\n".join(filenames)
    return gitignore

# returns the <head> element of the page
def head(templates, lang, obj):
    head = templates["head"]
    head = head.replace("$$TITLE$$", obj.get("title", ""))
    head = head.replace("$$KEYWORDS$$", ", ".join(obj.get("keywords", [])))
    head = head.replace("$$DATE$$", obj.get("date", ""))
    head = head.replace("$$AUTHOR$$", ", ".join(obj.get("keywords", [])))
    head = head.replace("$$DESCRIPTION$$", obj.get("description", ""))
    head = head.replace("$$IMG$$", obj.get("img", {}).get("href", ""))
    head = head.replace("$$IMG_ALT$$", obj.get("img", {}).get("title", ""))
    head = head.replace("$$IMG_WIDTH$$", obj.get("img", {}).get("width", ""))
    head = head.replace("$$IMG_HEIGHT$$", obj.get("img", {}).get("height", ""))
    return head

def header_navigation(templates, lang):

    homepage_logo = "/static/img/logo/logo-smooth.svg#logo"
    homepage_desc = ""
    all_articles_desc = ""
    all_articles_title = ""
    shop_desc = ""
    shop_title = ""
    shop_link = ""
    about_desc = ""
    about_title = ""
    tools_desc = ""
    tools_title = ""
    newest_desc = ""
    newest_title = ""
    about_link = ""
    homepage_link = lang
    all_articles_link = lang
    newest_link = ""
    tools_link = ""
    
    if lang == "de":
        homepage_logo = "/static/img/logo/logo-smooth.svg#logo"
        homepage_desc = "Startseite: Kategorisierte Liste aller deutschen Artikel"
        all_articles_desc = "Durchsuche alle deutschen Artikel"
        all_articles_title = "Themen"
        shop_desc = "Unterstütze unser Apostolat mit deinem Einkauf in unserem Shop!"
        shop_title = "Shop"
        about_desc = "Über diese Seite, Kontakt und Rechtliches"
        about_title = "Impressum"
        tools_desc = "Software und Hilfsmittel zum Latein-Lernen, Gebetssammlungen, Online Mess- und Bibelbücher, Online-Bücherei u.v.m"
        tools_title = "Ressourcen"
        newest_desc = "Artikel sortiert nach Datum"
        newest_title = "Neuigkeiten"

        homepage_link = lang
        shop_link = lang + "/shop"
        about_link = lang + "/impressum"
        tools_link = lang + "/ressourcen"
        all_articles_link = lang + "/themen"
        newest_link = lang + "/neu"
    else:

        homepage_logo = "/static/img/logo/logo-smooth.svg#logo"
        homepage_desc = "Homepage"
        all_articles_desc = "Search all English articles by category / tag"
        all_articles_title = "Categories"
        shop_desc = "Support our apostolate with your purchase in our store!"
        shop_title = "Shop"
        shop_link = lang + "/shop"
        about_desc = "Imprint, contact and legal information"
        about_title = "Contact"
        tools_desc = "Software and aids for learning Latin, prayer collections, online Mass and Bible books, online library and much more"
        tools_title = "Tools"
        newest_desc = "Articles sorted by date"
        newest_title = "Newest"

        homepage_link = lang
        shop_link = lang + "/shop"
        about_link = lang + "/contact"
        all_articles_link = lang + "/categories"
        newest_link = lang + "/newest"
        tools_link = lang + "/tools"

    header_navigation = templates["header-navigation"]

    header_navigation = header_navigation.replace("$$HOMEPAGE_LOGO$$", homepage_logo)
    header_navigation = header_navigation.replace("$$HOMEPAGE_DESC$$", homepage_desc)
    header_navigation = header_navigation.replace("$$HOMEPAGE_LINK$$", homepage_link)

    header_navigation = header_navigation.replace("$$TOOLS_DESC$$", tools_desc)
    header_navigation = header_navigation.replace("$$TOOLS_TITLE$$", tools_title)
    header_navigation = header_navigation.replace("$$TOOLS_LINK$$", tools_link)

    header_navigation = header_navigation.replace("$$ABOUT_DESC$$", about_desc)
    header_navigation = header_navigation.replace("$$ABOUT_TITLE$$", about_title)
    header_navigation = header_navigation.replace("$$ABOUT_LINK$$", about_link)

    header_navigation = header_navigation.replace("$$ALL_ARTICLES_TITLE$$", all_articles_title)
    header_navigation = header_navigation.replace("$$ALL_ARTICLES_DESC$$", all_articles_desc)
    header_navigation = header_navigation.replace("$$ALL_ARTICLES_LINK$$", all_articles_link)

    header_navigation = header_navigation.replace("$$NEWEST_DESC$$", newest_desc)
    header_navigation = header_navigation.replace("$$NEWEST_TITLE$$", newest_title)
    header_navigation = header_navigation.replace("$$NEWEST_LINK$$", newest_link)

    header_navigation = header_navigation.replace("$$SHOP_DESC$$", shop_desc)
    header_navigation = header_navigation.replace("$$SHOP_TITLE$$", shop_title)
    header_navigation = header_navigation.replace("$$SHOP_LINK$$", shop_link)
    
    return header_navigation

def link_tags(templates, lang, tags):
    link_tags = "<div class='link-tags'><p>$$TAGS$$</p></div>"
    tags_str = ""
    for t in tags:
        t_descr = "Link to " + t + " tag"
        t_data = "<a href='$$ROOT_HREF$$/" + lang + "/tag/" + t
        t_data += "' class='link-tag link-page link-annotated icon-not has-annotation spawns-popup' rel='tag' data-attribute-title='"
        t_data += t_descr + "'>" + t + "</a>"
        if t != tags[-1]:
            t_data += ", "
        tags_str += t_data
    link_tags = link_tags.replace("$$TAGS$$", tags_str)  
    return link_tags

def text_from_par(paragraph):
    target = ""
    for p in paragraph:
        target += p.get("data", {}).get("text", "")
    return target

def page_desciption(templates, lang, pagemeta):
    descr = pagemeta.get("description", "")
    page_desciption = "<div class='page-description'><p>" + descr + "</p></div>"
    return page_desciption

def page_metadata(templates, lang, pagemeta):
    
    page_metadata = templates["page-metadata"]

    date = pagemeta.get("date", "")
    date_desc = date
    date_title = date

    backlinks_desc = ""
    backlinks_title = ""
    similar_desc = ""
    similar_title = ""
    bibliography_desc = ""
    bibliography_title = ""

    if lang == "de":
        backlinks_desc = "Liste der anderen Seiten, die auf diese Seite verweisen"
        backlinks_title = "verweise"
        similar_desc = "Ähnliche Artikel"
        similar_title = "ähnlich"
        bibliography_desc = "Bibliographie der auf dieser Seite zitierten Links"
        bibliography_title = "bibliografie"
    else:
        backlinks_desc = "List of other pages which link to this page"
        backlinks_title = "⁠backlinks"
        similar_desc = "Similar articles for this link"
        similar_title = "⁠similar"
        bibliography_desc = "Bibliography of links cited in this page"
        bibliography_title = "bibliography"
        
    page_metadata = page_metadata.replace("$$DATE_DESC$$", date_desc)
    page_metadata = page_metadata.replace("$$DATE_TITLE$$", date_title)
    page_metadata = page_metadata.replace("$$BACKLINKS_DESC$$", backlinks_desc)
    page_metadata = page_metadata.replace("$$BACKLINKS_TITLE$$", backlinks_title)
    page_metadata = page_metadata.replace("$$SIMILAR_DESC$$", similar_desc)
    page_metadata = page_metadata.replace("$$SIMILAR_TITLE$$", similar_title)
    page_metadata = page_metadata.replace("$$BIBLIOGRAPHY_DESC$$", bibliography_desc)
    page_metadata = page_metadata.replace("$$BIBLIOGRAPHY_TITLE$$", bibliography_title)       

    return page_metadata

def render_link_internal(internal_link, title, link_text):
    link_id = "dubia-" + internal_link.replace("https://", "").replace("/", "-").lower()
    v = "<a href='$$ROOT_HREF$$/" + internal_link + "' id='" + link_id + "'" 
    v += "class='link-annotated link-page has-icon has-annotation spawns-popup'"
    v += "data-link-icon-type='text' data-link-icon='𝔡'"
    v += "data-attribute-title='" + title + "'"
    v += "style=\"--link-icon: '𝔡';\""
    v += ">" + link_text + "<span class='link-icon-hook'>⁠</span></a>&nbsp;"  
    return v

def render_wikipedia_link(wikipedia_link, title, link_text):
    v = "<a href='" + wikipedia_link + "'"
    v += "class='link-annotated-partial link-live has-icon has-annotation content-transform spawns-popup'"
    v += "data-link-icon='wikipedia'"
    v += "data-link-icon-type='svg'"
    v += "data-url-html='" + wikipedia_link + "#bodyContent'"
    v += "style='--link-icon-url: url('/static/img/icon/icons.svg#wikipedia');'"
    v += "data-attribute-title='" + title + "'"
    v += ">" + link_text + "<span class='link-icon-hook'>⁠</span></a>&nbsp;"
    return v

def render_link(link, title, text):
    if "wikipedia." in link:
        return render_wikipedia_link(link, title, text)
    else:
        return render_link_internal(link, title, text)

def render_blockquote(q):
    return "" # todo

def render_code_block(obj):
    return ""

def render_text_item(obj):

    context = obj.get("context", [])
    text = obj.get("text", "")
    link = obj.get("link", "")
    title = obj.get("title", "")

    target = text

    if target == "":
        return target
    else:
        target = target + "&nbsp;"
    
    if "strikethrough" in context:
        target = "<del>" + target + "</del>"
    
    if "superscript" in context:
        target = "<sup>" + target + "</sup>"
    elif "subscript" in context:
        target = "<sub>" + target + "</sub>"

    if "italic" in context:
        target = "<em>" + target + "</em>"
    
    if "bold" in context:
        target = "<strong>" + target + "</strong>"
    
    if "underline" in context:
        target = "<span class='smallcaps'>" + target + "</span>"
    
    if "link" in context:
        target = render_link(link, title, target)

    return target

def render_paragraph(par):
    target = ""
    for item in par:
        if item["type"] == "text":
            target += render_text_item(item["data"])
        elif item["type"] == "code":
            target += render_code_block(item["data"])
    return target

def body_abstract(templates, lang, abstract_json):

    target = ""
    if len(abstract_json) == 0:
        return target

    target += "<p class='first-block first-graf block' style='--bsm: 0;'>"
    target += render_paragraph(abstract_json[0]) 
    target += "</p>"

    for par in abstract_json[1:]:
        target += "<p class='block' style='--bsm: 0;'>" + render_paragraph(par) + "</p>"

    style = "class='first-block block blockquote-level-1' style='--bsm: 0;'"
    ba = "<div class='abstract'><blockquote " + style + ">" + target + "</blockquote></div>"

    return ba

def body_noscript(templates, lang):
    body_noscript = templates["body-noscript"]
    return body_noscript


# SCRIPT STARTS HERE

root_href = get_root_href()
templates = load_templates()
articles = load_articles()

for slug, readme in articles.items():

    readme_tags = ["hexe", "mittelalter", "fruehe-neuzeit", "inquisition"]

    lang = slug.split("/")[0]
    slug_raw = slug.split("/")[1]
    html = templates["index"]

    pagemeta = {
        "title": readme.get("title", ""),
        "keywords": readme.get("tags", ""),
        "date": readme.get("date", ""),
        "author": readme.get("authors", []),
        "contact_url": "/contact",
        "description": text_from_par(readme.get("tagline", [])),
        "img": readme.get("img", {}),
    }

    html = html.replace("<!-- HEAD_TEMPLATE_HTML -->", head(templates, lang, pagemeta))
    html = html.replace("<!-- HEADER_NAVIGATION -->", header_navigation(templates, lang))
    html = html.replace("<!-- LINK_TAGS -->", link_tags(templates, lang, readme.get("tags", [])))
    html = html.replace("<!-- PAGE_DESCRIPTION -->", page_desciption(templates, lang, pagemeta))
    html = html.replace("<!-- PAGE_METADATA -->", page_metadata(templates, lang, pagemeta))
    html = html.replace("<!-- BODY_ABSTRACT -->", body_abstract(templates, lang, readme.get("summary", [])))
    html = html.replace("<!-- BODY_NOSCRIPT -->", body_noscript(templates, lang))
    
    html = html.replace("$$SKIP_TO_MAIN_CONTENT$$", "Skip to main content")
    html = html.replace("$$TITLE$$", pagemeta["title"])
    html = html.replace("$$LANG$$", lang)
    html = html.replace("$$SLUG$$", slug_raw)
    html = html.replace("$$ROOT_HREF$$", root_href)
    html = html.replace("$$PAGE_HREF$$", root_href + "/" + slug)

    write_file(html, "./" + slug + ".html")

write_file(generate_gitignore(articles), "./.gitignore")

# special pages: /de - list all articles
# /de/neu - list newest articles
# /index.html - search page (automatic language)