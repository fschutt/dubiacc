import sys, base64, os, json, hashlib

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

# Loads templates from the /templates folder, so while generating articles
# we don't have to touch the filesystem. Also does some preliminary CSS inlining.
def load_templates():
    templates = {}
    templates["index"] = read_file("./templates/lorem.html")
    header_template = read_file("./templates/head.html")
    header_template = header_template.replace(
        "<!-- DARKLIGHT_STYLES -->", read_file("./templates/darklight.html")
    )
    header_template = header_template.replace(
        "<!-- CRITICAL_CSS -->", 
        "<style id='critical-css'>\r\n" + read_file("./static/css/head.css") + read_file("./static/css/style.css") + "    </style>"
    )
    templates["head"] = header_template
    templates["table-of-contents"] = read_file("./templates/table-of-contents.html")
    templates["page-metadata"] = read_file("./templates/page-metadata.html")
    templates["body-noscript"] = read_file("./templates/body-noscript.html")
    templates["header-navigation"] = read_file("./templates/header-navigation.html")
    templates["section"] = read_file("./templates/section.html")
    templates["special"] = read_file("./templates/special.html")
    return templates

def get_root_href():
    root_href = "http://localhost/:8080"
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
        filenames.append(k.split("/")[0] + ".html")
    filenames.extend(map(lambda x: "/" + x, dirs))
    filenames.append("/venv")
    filenames.append("*.md.json")
    filenames.append("md2json-bin")
    filenames.append("index.json")
    filenames.append("index.html")
    filenames.append(".DS_Store")
    filenames.append("/md2json/target")
    filenames.append("/md2json2/target")
    filenames.append("/img2avif/target")
    filenames.append("/md2json/out.txt")
    filenames.append("/venv/*")
    filenames.sort()
    filenames = list(set(filenames))
    gitignore = "\r\n".join(filenames)
    return gitignore

def get_title(lang, obj):
    title = obj.get("title", "")
    if title == "":
        title = "Discover the true Catholic Faith - dubia.cc"
        if lang == "de":
            title = "Entdecke den wahren katholischen Glauben - dubia.cc"
    else:
        title = title + " - dubia.cc"
    return title

def get_description(lang, obj):
    d = str(obj.get("description", ""))
    if d == "":
        d = "dubia is a collection of articles about the traditional Catholic faith. Did the Church really teach...? Answers to errors and questions, prayers, and more!"
        if lang == "de":
            d = "dubia ist eine Sammlung von Artikeln über den traditionellen katholischen Glauben. Hat die Kirche wirklich...? Antworten auf Irrtümer, Gebete, uvm."
    return d

# returns the <head> element of the page
def head(templates, lang, obj, title_id):
    head = templates["head"]
    title = get_title(lang, obj)
    description = get_description(lang, obj)
    head = head.replace("$$TITLE$$", title)
    head = head.replace("$$DESCRIPTION$$", description)
    head = head.replace("$$TITLE_ID$$", title_id)
    head = head.replace("<!-- DROPCAP_CSS -->", "<style>" + generate_dropcap_css(obj.get("initiale", "")) + "</style>")
    head = head.replace("$$KEYWORDS$$", ", ".join(obj.get("keywords", [])))
    head = head.replace("$$DATE$$", obj.get("date", ""))
    head = head.replace("$$AUTHOR$$", ", ".join(obj.get("authors", [])))
    head = head.replace("$$IMG$$", obj.get("img", {}).get("href", ""))
    head = head.replace("$$IMG_ALT$$", obj.get("img", {}).get("title", ""))
    head = head.replace("$$IMG_WIDTH$$", obj.get("img", {}).get("width", ""))
    head = head.replace("$$IMG_HEIGHT$$", obj.get("img", {}).get("height", ""))
    head = head.replace("$$LANG$$", lang)
    head = head.replace("$$SLUG$$", "")
    head = head.replace("$$ROOT_HREF$$", root_href)
    head = head.replace("$$PAGE_HREF$$", root_href + "/" + lang + "/" + slug_raw)
    skip = "Skip to main content"
    if lang == "de":
        skip = "Zum Hauptinhalt springen"
    head = head.replace("$$SKIP_TO_MAIN_CONTENT$$", skip)
    contact = "en/about"
    if lang == "de":
        contact = "de/impressum"
    head = head.replace("$$CONTACT_URL$$", contact)
    head = head.replace("$$SLUG$$", title_id)
    return head

def get_initiale(readme, slug):
    summary = readme.get("summary", [])
    if len(summary) == 0:
        return ""
    target = summary[0][0].get("data", {}).get("text", "")[0]
    if target == "'" or target == "\"":
        raise Exception("file " + slug + ": article starts with \" or '")
    return target

def header_navigation(templates, lang, display_logo):

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
        newest_title = "Neues"

        homepage_link = lang
        shop_link = lang + "/shop"
        about_link = lang + "/impressum"
        tools_link = lang + "/ressourcen"
        all_articles_link = lang + "/themen"
        newest_link = lang + "/neues"
    else:

        homepage_logo = "/static/img/logo/logo-smooth.svg#logo"
        homepage_desc = "Homepage"
        all_articles_desc = "Search all English articles by category / tag"
        all_articles_title = "Topics"
        shop_desc = "Support our apostolate with your purchase in our store!"
        shop_title = "Shop"
        shop_link = lang + "/shop"
        about_desc = "Imprint, contact and legal information"
        about_title = "About"
        tools_desc = "Software and aids for learning Latin, prayer collections, online Mass and Bible books, online library and much more"
        tools_title = "Tools"
        newest_desc = "Articles sorted by date"
        newest_title = "Newest"

        homepage_link = lang
        shop_link = lang + "/shop"
        about_link = lang + "/about"
        all_articles_link = lang + "/topics"
        newest_link = lang + "/newest"
        tools_link = lang + "/tools"

    header_navigation = templates["header-navigation"]

    logo = "<a class='logo has-content' rel='home me contents' href='$$ROOT_HREF$$/" + homepage_link + "' data-attribute-title='" + homepage_desc + "'>"
    logo += "<svg class='logo-image' viewBox='0 0 64 75'><use href='" + homepage_logo + "'></use></svg>"
    logo += "</a>"

    if display_logo:
        header_navigation = header_navigation.replace("$$HOMEPAGE_LOGO$$", logo)
    else:
        header_navigation = header_navigation.replace("$$HOMEPAGE_LOGO$$", "")

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
        topics_url = "topics"
        if lang == "de":
            topics_url = "themen"
        t_data = "<a href='$$ROOT_HREF$$/" + lang + "/" + topics_url + "#" + t
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

def render_rosary_glorybe(templates, lang, decade, id, prev_id, next_id):
    rosary_template = read_file("./templates/tools.rosary.glorybe." + lang + ".html")
    rosary_template = rosary_template.replace("$$ID$$", id)
    rosary_template = rosary_template.replace("$$PREV_ID$$", prev_id)
    rosary_template = rosary_template.replace("$$NEXT_ID$$", next_id)
    rosary_template = rosary_template.replace("$$DECADE$$", decade)
    return rosary_template

def render_rosary_fatima(templates, lang, decade, id, prev_id, next_id):
    rosary_template = read_file("./templates/tools.rosary.fatima." + lang + ".html")
    rosary_template = rosary_template.replace("$$ID$$", id)
    rosary_template = rosary_template.replace("$$PREV_ID$$", prev_id)
    rosary_template = rosary_template.replace("$$NEXT_ID$$", next_id)
    rosary_template = rosary_template.replace("$$DECADE$$", decade)
    return rosary_template

def render_rosary_ourfather(templates, lang, decade, id, prev_id, next_id):
    rosary_template = read_file("./templates/tools.rosary.ourfather." + lang + ".html")
    rosary_template = rosary_template.replace("$$ID$$", id)
    rosary_template = rosary_template.replace("$$PREV_ID$$", prev_id)
    rosary_template = rosary_template.replace("$$NEXT_ID$$", next_id)
    rosary_template = rosary_template.replace("$$DECADE$$", decade)
    return rosary_template

def render_nav(templates, lang, id):
    nav = read_file("./templates/tools.rosary.nav." + lang + ".html")
    nav = nav.replace("$$ID$$", id)
    return nav

def render_rosary_body(templates, lang, pagemeta):
    
    hm_start = "Gegrüßet seiest du Maria, voll der Gnaden, der Herr ist mit dir. Du bist gebenedeit unter den Weibern und gebenedeit ist die Frucht deines Leibes Jesus, "
    hm_end = " Heilige Maria, Mutter Gottes, bitte für uns Sünder, jetzt und in der Stunde unseres Todes."
    
    if lang == "en":
        hm_start = "Hail, Mary, full of grace, the Lord is with thee. Blessed art thou amongst women and blessed is the fruit of thy womb, Jesus, "
        hm_end = " Holy Mary, Mother of God, pray for us sinners, now and at the hour of our death."

    rosary_template = read_file("./templates/tools.rosary." + lang + ".html")
    start = "Anfang"
    if lang == "en":
        start = "Start"
    rosary_template = rosary_template.replace("<!-- OURFATHER -->", render_rosary_ourfather(templates, lang, start, "intro-05", "intro-04", "intro-06"))
    rosary_template = rosary_template.replace("<!-- GLORYBE -->", render_rosary_glorybe(templates, lang, start, "intro-09", "intro-08", "intro-10"))
    rosary_template = rosary_template.replace("<!-- FATIMA -->", render_rosary_fatima(templates, lang, start, "intro-10", "intro-09", "decade-1-ourfather"))
    rosary_template = rosary_template.replace("<!-- NAV_01 -->", render_nav(templates, lang, "intro-00"))
    rosary_template = rosary_template.replace("<!-- NAV_02 -->", render_nav(templates, lang, "intro-11"))
    rosary_template = rosary_template.replace("<!-- END -->", read_file("./templates/tools.rosary.outro." + lang + ".html"))

    rosary_section_template = read_file("./templates/tools.rosary.mystery.html")
    mysteries = json.loads(read_file("./static/img/rosary/mysteries.json"))["mysteries"]
    mst = []
    hm_add = [
        "den du, o Jungfrau, vom Heiligen Geist empfangen hast.",
        "den du, o Jungfrau, zu Elisabeth getragen hast.",
        "den du, o Jungfrau, in Bethlehem geboren hast.",
        "den du, o Jungfrau, im Tempel aufgeopfert hast.",
        "den du, o Jungfrau, im Tempel wiedergefunden hast.",

        "der für uns Blut geschwitzt hat.",
        "der für uns gegeißelt worden ist.",
        "der für uns mit Dornen gekrönt worden ist.",
        "der für uns das schwere Kreuz getragen hat.",
        "der für uns am Kreuz gestorben ist.",

        "der von den Toten auferstanden ist.",
        "der in den Himmel aufgefahren ist.",
        "der uns den Heiligen Geist gesandt hat.",
        "der dich, o Jungfrau, in den Himmel aufgenommen hat.",
        "der dich, o Jungfrau, im Himmel gekrönt hat.",
    ]

    if lang == "en":
        hm_add = [
            "whom you, O Virgin, received from the Holy Spirit.", 
            "whom you, O Virgin, carried to Elizabeth.",
            "to whom, O Virgin, you gave birth in Bethlehem.", 
            "whom you, O Virgin, offered up in the temple.", 
            "whom you, O Virgin, found again in the temple.", 

            "who sweated blood for us.", 
            "who was scourged for us.",
            "who was crowned with thorns for us.", 
            "who bore the heavy cross for us.", 
            "who died for us on the cross.", 

            "who rose from the dead.", 
            "who ascended into heaven.", 
            "who sent us the Holy Spirit.", 
            "who took you, O Virgin, up into heaven.", 
            "who crowned you, O Virgin, in heaven.", 
        ]

    for i in range(1, 16):

        hma = hm_add[i - 1]
        mys = mysteries[str(i)]
        decade = mys["decade"][lang]
        fruit = mys["spiritual-fruit"][lang]
        
        # + our father
        ourfather_prev = ""
        if i == 1:
            ourfather_prev = "intro-10"
        else:
            ourfather_prev = "decade-" + str(i - 1) + "-fatima"
        
        ourfather_next = ""
        if i == 15:
            ourfather_next = "outro-01"
        else:
            ourfather_next = "s" + mysteries[str(i)]["prayers"]["1"]["image"]
        
        mst.append(render_rosary_ourfather(templates, lang, decade, "decade-" + str(i) + "-ourfather", ourfather_prev, ourfather_next))

        for q in range(1, 11):
            pr = mys["prayers"][str(q)]
            text = pr[lang]
            source = pr["source"]
            prev_id = ""
            if q == 1:
                prev_id = "decade-" + str(i) + "-ourfather"
                next_id = "s" + mys["prayers"][str(q + 1)]["image"]
            elif q == 10:
                prev_id = "s" + mys["prayers"][str(q - 1)]["image"]
                next_id = "decade-" + str(i) + "-glorybe"
            else:
                prev_id = "s" + mys["prayers"][str(q - 1)]["image"]
                next_id = "s" + mys["prayers"][str(q + 1)]["image"]

            rst = rosary_section_template
            rst = rst.replace("$$SECTION_ID$$", pr["image"])
            rst = rst.replace("$$DECADE$$", decade)
            rst = rst.replace("$$INDEX$$", str(q))
            rst = rst.replace("$$TEXT_TOP$$", text) 
            rst = rst.replace("$$SOURCE$$", source)
            rst = rst.replace("$$PREV_SECTION_ID$$", prev_id)
            rst = rst.replace("$$NEXT_SECTION_ID$$", next_id)
            rst = rst.replace("$$HAIL_MARY_START$$", hm_start)
            rst = rst.replace("$$DECADE_ADDITION$$", hma)
            rst = rst.replace("$$HAIL_MARY_END$$", hm_end)
            mst.append(rst)
    
        glorybe_prev = mys["prayers"]["10"]["image"]
        glorybe_next = "decade-" + str(i) + "-fatima"
        mst.append(render_rosary_glorybe(templates, lang, decade, "decade-" + str(i) + "-glorybe", glorybe_prev, glorybe_next))

        fatima_prev = "decade-" + str(i) + "-glorybe"
        fatima_next = ""
        
        if i % 5 == 0:
            fatima_next = "nav-" + str(i)
        else:
            fatima_next = "decade-" + str(i + 1) + "-ourfather"
        
        mst.append(render_rosary_fatima(templates, lang, decade, "decade-" + str(i) + "-fatima", fatima_prev, fatima_next))
        
        if i % 5 == 0:
            mst.append(render_nav(templates, lang, "nav-" + str(i)))

    return rosary_template.replace("<!-- MYSTERIES -->", "".join(mst))

def page_desciption(templates, lang, pagemeta):
    descr = pagemeta.get("description", "")
    page_desciption = "<div class='page-description'><p>" + descr + "</p></div>"
    return page_desciption

def render_page_author_pages(lang, authors):

    text_contact = "Contact"
    text_donate = "Donate"

    if lang == "de":
        text_contact = "Kontakt"
        text_donate = "Spenden"
    
    for id, v in authors.items():
        i = id.lower().replace(":", "-")
        name = v.get("displayname", "")
        contact_url = v.get("contact", "")
        donate_urls = v.get("donate", {})
        dn = ""
        for platform, link in donate_urls.items():
            if platform == "paypal":
                dn += "<p><a href='" + link + "'>PayPal</a></p>"
            elif platform == "ko-fi":
                dn += "<p><a href='" + link + "'>Ko-Fi</a></p>"
            elif platform == "github":
                dn += "<p><a href='" + link + "'>GitHub Sponsors</a></p>"
            else:
                raise Exception("unknown platform " + platform + " for user " + id + "in authors.json")
        
        t = "<!doctype html><html><head><title>" + name + "</title></head><body>"
        t += "<h1>" + name + "</h1>"
        t += "<h2>" + text_contact + "</h2>"
        t += "<a href='" + contact_url + "'>" + contact_url + "</a>"
        t += "<h2>" + text_donate + "</h2>"
        t += dn
        t += "</body></html>"

        if not(os.path.isdir("./" + lang)):
            os.mkdir("./" + lang)
        if not(os.path.isdir("./" + lang + "/author")):
            os.mkdir("./" + lang + "/author")
        write_file(t, "./" + lang + "/author/" + i + ".html")

def page_metadata(templates, lang, pagemeta):
    
    page_metadata = templates["page-metadata"]

    date = pagemeta.get("date", "")
    date_desc = date
    date_title = date

    authors_link = []
    for k, v in pagemeta.get("authors", {}).items():
        id = k.lower().replace(":", "-")
        name = v.get("displayname", "")
        style = "data-link-icon='info-circle-regular' data-link-icon-type='svg' style=\"--link-icon-url: url('/static/img/icon/icons.svg#info-circle-regular');\""
        classes = "class='backlinks link-self has-icon has-content spawns-popup has-indicator-hook'"
        link = "<a href='/" + lang + "/author/" + id + "' data-attribute-title='" + name 
        link += "' " + style + " " + classes + "><span class='indicator-hook'></span>" + name 
        link += "<span class='link-icon-hook'>⁠</span></a>"
        authors_link.append(link)

    authors_link = ", ".join(authors_link)
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
    page_metadata = page_metadata.replace("<!-- AUTHORS -->", authors_link)

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

def render_text_item(obj, dropcap=False):

    context = obj.get("context", [])
    text = obj.get("text", "")
    link = obj.get("link", "")
    title = obj.get("title", "")

    if text == "":
        return ""
    
    if dropcap:
        target = text[1:]
    else:
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

def generate_dropcap_css(initiale):
    if initiale == "":
        return ""

    dropcap_map = {
        "A": "U+0041",
        "B": "U+0042",
        "C": "U+0043",
        "D": "U+0044",
        "E": "U+0045",
        "F": "U+0046",
        "G": "U+0047",
        "H": "U+0048",
        "I": "U+0049",
        "J": "U+004A",
        "K": "U+004B",
        "L": "U+004C",
        "M": "U+004D",
        "N": "U+004E",
        "O": "U+004F",
        "P": "U+0050",
        "Q": "U+0051",
        "R": "U+0052",
        "S": "U+0053",
        "T": "U+0054",
        "U": "U+0055",
        "V": "U+0056",
        "W": "U+0057",
        "X": "U+0058",
        "Y": "U+0059",
        "Z": "U+005A",
    }

    text = "@font-face {"
    text += "    font-family: 'Kanzlei Initialen';"
    text += "    src: url('/static/font/kanzlei/Kanzlei-Initialen-" + initiale + ".ttf') format('truetype');"
    text += "    font-display: swap;"
    text += "    unicode-range: " + dropcap_map[initiale] + ";"
    text += "}"
    return text

def render_paragraph(par,dropcap=False):
    target = ""
    for item in par:
        if item["type"] == "text":
            if dropcap and item["data"] == par[0]["data"]:
                drc = item["data"].get("text", "")[0]
                target += "<span class='dropcap'>" + drc + "</span>"
                target += render_text_item(item["data"], True)
            else:
                target += render_text_item(item["data"], False)
        elif item["type"] == "code":
            target += render_code_block(item["data"])
    return target

def render_section(templates, lang, section):
    
    paragraphs = section.get("paragraphs", [])
    if len(paragraphs) == 0:
        return ""
    
    header = section.get("header", "")
    level = section.get("level", 5)
    section_id = header.lower().replace(" ", "-")
    section_descr = ""
    if lang == "de":
        section_descr = "Link zum Abschnitt '" + header +"'"
    else:
        section_descr = "Link to section '" + header +"'"

    target = templates["section"]
    target = target.replace("$$LEVEL$$", str(level - 1))
    target = target.replace("$$SECTION_ID$$", section_id)
    target = target.replace("$$SECTION_DESCR$$", header)
    target = target.replace("$$SECTION_TITLE$$", header)
    target = target.replace("<!-- FIRST_PARAGRAPH -->", render_paragraph(paragraphs[0], False))
    
    for t in paragraphs[1:]:
        target += "<p class='block' style='--bsm: 0;'>" + render_paragraph(t, False) + "</p>"
    
    return target

def body_content(templates, lang, sections):

    target = ""

    if len(sections) == 0:
        return target
    
    for section in sections:
        target += render_section(templates, lang, section)

    return target

def table_of_contents(templates, lang, sections):

    if len(sections) == 0:
        return ""

    target = "<div id='TOC' class='TOC'>"
    target += "<ul class='list-level-1'>"

    cur_level = sections[0].get("level", 5)
    orig_cur_level = cur_level

    for section in sections:

        header = section.get("header", "")
        level = section.get("level", 5)
        section_id = header.lower().replace(" ", "-")
        
        if level > cur_level:
            target += "<ul class='list-level-" + str(level - 1) + "'>"

        while level < cur_level:
            target += "</ul>"
            cur_level -= 1

        cur_level = level
        target += "<li>"

        target += "<a href='#" + section_id + "' id='toc-" + section_id
        target += "' class='decorate-not has-content spawns-popup'>" + header + "</a>"
        
        target += "</li>"

    while orig_cur_level < cur_level:
        target += "</ul>"
        cur_level -= 1

    footnotes_id = "footnotes"
    similar_id = "similar"
    bibliography_id = "bibliography"
    backlinks_id = "backlinks"

    collapse_button_title = "Collapse table of contents"
    footnotes_title = "Footnotes"
    similar_title = "Similar articles"
    bibliography_title = "Bibliography"
    backlinks_title = "Verweise"

    if lang == "de":
        collapse_button_title = "Inhaltsverzeichnis zusammenklappen"
        footnotes_title = "Fußnoten"
        similar_title = "Ähnliche Artikel"
        bibliography_title = "Bibliographie"

    s = "class='link-self decorate-not has-content spawns-popup'"
    target += "<li><a " + s + " id='toc-backlinks' href='#" + backlinks_id +"'>" + backlinks_title + "</a></li>"
    target += "<li><a " + s + " id='toc-footnotes' href='#" + footnotes_id +"'>" + footnotes_title + "</a></li>"
    target += "<li><a " + s + " id='toc-similar' href='#" + similar_id + "'>" + similar_title + "</a></li>"
    target += "<li><a " + s + " id='toc-bibliography' href='#" + bibliography_id + "'>" + bibliography_title + "</a></li>"
    target += "</ul>"
    target += "<button class='toc-collapse-toggle-button' title='" + collapse_button_title + "' tabindex='-1'><span></span></button>"
    target += "</div>"
    return target

def body_abstract(templates, lang, abstract_json):

    target = ""
    if len(abstract_json) == 0:
        return target

    target += "<p class='first-block first-graf intro-graf block dropcap-kanzlei' style='--bsm: 0;'>"
    target += render_paragraph(abstract_json[0], True) 
    target += "</p>"

    for par in abstract_json[1:]:
        target += "<p class='block' style='--bsm: 0;'>" + render_paragraph(par, False) + "</p>"

    return target

def body_noscript(templates, lang):
    body_noscript = templates["body-noscript"]
    return body_noscript

def generate_searchindex(lang, articles_dict):
    version = read_file("./.git/refs/heads/master").strip().replace("\n", "")
    articles = {}
    for slug, readme in articles_dict.items():
        if not(slug.startswith(lang + "/")):
            continue
        slug = slug.replace(lang + "/", "")
        articles[slug] = { "title": readme.get("title", ""), "sha256": readme.get("sha256", "") }

    obj = {
        "git": version,
        "articles": articles
    }
    return json.dumps(obj,ensure_ascii=False).encode('utf8').decode()

def search_html(lang):
    version = read_file("./.git/refs/heads/master").strip().replace("\n", "")
    searchbar_placeholder = "Keyword, topic, question, ..."
    searchbar = "Search"
    no_results = "No results found."
    if lang == "de":
        searchbar_placeholder = "Stichwort, Thema, Frage, ..."
        searchbar = "Suchen"
        no_results = "Keine Ergebnisse gefunden."
    searchbar_html = read_file("./templates/searchbar.html")
    searchbar_html = searchbar_html.replace("$$VERSION$$", version)
    searchbar_html = searchbar_html.replace("$$SEARCHBAR_PLACEHOLDER$$", searchbar_placeholder)
    searchbar_html = searchbar_html.replace("$$SEARCH$$", searchbar)
    search_js = read_file("./static/js/search.js")
    search_js = search_js.replace("$$LANG$$", lang)
    search_js = search_js.replace("$$VERSION$$", version)
    search_js = search_js.replace("$$NO_RESULTS$$", no_results)
    write_file(search_js, "./static/js/search-" + lang + ".js")
    return searchbar_html

def render_index_sections(lang, sections):
    ret = ""
    for s in sections:
        section_id = s["id"]
        section_title = s["title"]
        if "links" in s:
            ret += render_index_section(lang, section_id, "", section_title, s["links"])
        elif "texts" in s:
            ret += render_index_section_texts(lang, section_id, "", section_title, s["texts"])
        elif "link" in s:
            section_links = s["link"]
            ret += render_index_section_img(lang, section_id, "", section_title, section_links["slug"], section_links["img"], section_links["title"])
    return ret 

def render_section_items_texts(lang, texts):
    section_items = ""
    for t in texts:
        if t == "":
            t = "<br/>"
        elif not(t.startswith("<")):
            t = "<p style='text-indent: 0px;'>" + t + "</p>"
        section_items += t
    return section_items

def render_section_items_img(lang, link, img, title):
    section_items = ""
    style = "justify-content: flex-end;margin-top:10px;width: 100%;min-height: 440px;display: flex;flex-direction:column;height: 100%;background-size: cover;background-image: url(" + img + ");"
    p_style = "font-variant-caps: small-caps;background: var(--background-color);border-radius:5px;border: 2px solid var(--GW-H1-border-color); text-align: center; text-decoration: underline; text-indent: 0px;margin: 10px;padding: 10px 20px;"
    section_items += "<a href='" + link + "' style='" + style + "'><p style='" + p_style + "'>" + title + "</p></a>"
    return section_items

def render_section_items(lang, links):
    section_items = ""
    first = True
    for l in links:
        slug = l["slug"]
        section_title = l["title"]
        bsm = "4"
        if not(first):
            bsm = "0"
        first = False

        final_link = "$$ROOT_HREF$$/" + lang + "/" + slug
        if slug.startswith("http"):
            final_link = slug
        section_items += "<li class='block link-modified-recently-list-item dark-mode-invert' style='--bsm: " + bsm + ";'>"
        section_items += "  <p class='in-list first-graf block' style='--bsm: 0;'><a href='" + final_link + "'"
        section_items += "      id='" + lang + "-" + slug + "'"
        section_items += "      class='link-annotated link-page link-modified-recently in-list has-annotation spawns-popup'"
        section_items += "      data-attribute-title='" + section_title + "'>" + section_title + "</a></p>"
        section_items += "</li>"

    return section_items

def render_index_section(lang, id, classes, title, links):
    section_html = read_file("./templates/index.section.html")
    section_html = section_html.replace("$$SECTION_ID$$", id)
    section_html = section_html.replace("$$SECTION_CLASSES$$", classes)
    section_html = section_html.replace("$$SECTION_NAME$$", title)
    section_html = section_html.replace("$$SECTION_NAME_TITLE$$", title)
    section_html = section_html.replace("<!-- SECTION_ITEMS -->", render_section_items(lang, links))
    return section_html

def render_index_section_texts(lang, id, classes, title, txts):
    section_html = read_file("./templates/index.section.html")
    section_html = section_html.replace("$$SECTION_ID$$", id)
    section_html = section_html.replace("$$SECTION_CLASSES$$", classes)
    section_html = section_html.replace("$$SECTION_NAME$$", title)
    section_html = section_html.replace("$$SECTION_NAME_TITLE$$", title)
    section_html = section_html.replace("<!-- SECTION_ITEMS -->", render_section_items_texts(lang, txts))
    return section_html

def render_index_section_img(lang, id, classes, title, link, img, t):
    section_html = read_file("./templates/index.section.html")
    section_html = section_html.replace("$$SECTION_ID$$", id)
    section_html = section_html.replace("$$SECTION_CLASSES$$", classes)
    section_html = section_html.replace("$$SECTION_NAME$$", title)
    section_html = section_html.replace("$$SECTION_NAME_TITLE$$", title)
    section_html = section_html.replace("<!-- SECTION_ITEMS -->", render_section_items_img(lang, link, img, t))
    return section_html

def render_other_index_sections(lang, tags, articles):
    
    first_section = ""

    for (k, v) in tags[lang]["iwanttolearn"].items():
        id = k
        title = v["title"]
        featured = []
        for f in v["featured"]:
            slug = f
            title = articles[lang + "/" + slug].get("title", "")
            featured.append({ "slug": slug, "title": title })
        v["featured"] = featured
        first_section += render_index_section(lang, id, "", title, featured)

    return first_section

def render_index_first_section(lang, tags, articles):

    for t in tags[lang]["ibelievein"]:
        featured = []
        for f in t["featured"]:
            slug = f
            title = articles[lang + "/" + slug].get("title", "")
            featured.append({ "slug": slug, "title": title })
        t["featured"] = featured

    text_ibelieve = "I believe in"
    if lang == "de":
        text_ibelieve = "Ich glaube an"

    ibelievein = tags[lang]["ibelievein"]
    first_section = read_file("./templates/index.first-section.html")
    sections = ""
    options = ""
    first = True
    other_sections = "<style>.section-hidden { display: none; }</style>"

    for t in ibelievein:
        li_items = render_section_items(lang, t["featured"])
        display_hidden = "display:none;"
        if first:
            display_hidden = ""
        classes = "index-first-section list list-level-1"
        sections += "<ul id='index-section-" + t["tag"] + "' class='" + classes + "' style='margin-top:20px;" + display_hidden + "'>" + li_items + "</ul>"
        options += "<option value='" + t["tag"] + "'>" + t["option"] + "</option>"
        for q in ibelievein:
            if t["tag"] == q["tag"]:
                continue
            hidden_class = "section-hidden"
            if first:
                hidden_class = ""
            other_sections += render_index_section(lang, q["tag"],  hidden_class + " invert invert-of-" + t["tag"], q["title"], q["featured"])
        first = False

    first_section = first_section.replace("$$I_BELIEVE_IN$$", text_ibelieve)
    first_section = first_section.replace("<!-- SECTIONS -->", sections)
    first_section = first_section.replace("<!-- OTHER_SECTIONS -->", other_sections)
    first_section = first_section.replace("<!-- OPTIONS -->", options)
    return first_section

def render_special_page(templates, lang, sections, pagemeta, page_id):
    special = templates["special"]
    special = special.replace("<!-- HEAD_TEMPLATE_HTML -->", head(templates, lang, pagemeta, page_id))
    special = special.replace("<!-- BODY_ABSTRACT -->", render_index_sections(lang, sections))
    special = special.replace("<!-- HEADER_NAVIGATION -->", header_navigation(templates, lang, True))
    special = special.replace("$$TITLE$$", pagemeta.get("title", "") + " - dubia.cc")
    special = special.replace("$$LANG$$", lang)
    special = special.replace("$$ROOT_HREF$$", root_href)
    return special
           
def render_index_html(lang, articles, tags):
    index_html = read_file("./templates/index.html")
    multilang = read_file("./templates/multilang.tags.html")
    index_body_html = read_file("./templates/index-body.html")
    index_body_html = index_body_html.replace("<!-- SECTIONS -->", render_index_first_section(lang, tags, articles))
    index_body_html = index_body_html.replace("<!-- SECTION_EXTRA -->", render_other_index_sections(lang, tags, articles))
    logo_svg = read_file("./static/img/logo/full.svg")
    
    keywords = ["catholic", "church", "church fathers", "faith", "meaning of life", "evolution", "protestant", "islam"]
    if lang == "de":
        keywords = ["katholisch", "kirche", "kirchenväter", "glauben", "sinn des lebens", "evolution", "evangelisch", "islam"]
    
    pagemeta = {
        "title": readme.get("title", ""),
        "description": readme.get("tagline", ""),
        "keywords": keywords,
        "img": {},
    }
    title = get_title(lang, pagemeta)
    description = get_description(lang, pagemeta)

    shtml = search_html(lang)
    search = read_file("./templates/search.html")
    search = search.replace("<!-- SEARCH -->", shtml)
    search = search.replace("<!-- HEADER_NAVIGATION -->", header_navigation(templates, lang, True))
    search = search.replace("$$LANG$$", lang)
    search = search.replace("$$ROOT_HREF$$", root_href)
    search_lang = "Search"
    if lang == "de":
        search_lang = "Suche"
    search_meta = {
        "title": search_lang,
        "description": "Search dubia.cc",
        "img": {},
    }
    search = search.replace("<!-- HEAD_TEMPLATE_HTML -->", head(templates, lang, search_meta, lang + "-search"))
    search = search.replace("$$TITLE$$", search_meta.get("title", "Search") + " - dubia.cc")
    write_file(search, "./" + lang + "/search.html")

    select_faith = "Select Faith"
    if lang == "de":
        "Glauben auswählen"
        
    index_body_html = index_body_html.replace("<!-- SEARCHBAR -->", shtml)
    index_html = index_html.replace("<!-- BODY_ABSTRACT -->", index_body_html)
    index_html = index_html.replace("<!-- PAGE_DESCRIPTION -->", read_file("./templates/page-description-" + lang + ".html"))
    index_html = index_html.replace("<!-- SVG_LOGO_INLINE -->", logo_svg)
    index_html = index_html.replace("<!-- HEAD_TEMPLATE_HTML -->", head(templates, lang, pagemeta, lang + "-index"))
    index_html = index_html.replace("<!-- PAGE_HELP -->", read_file("./templates/navigation-help-" + lang + ".html"))
    index_html = index_html.replace("<!-- HEADER_NAVIGATION -->", header_navigation(templates, lang, False))
    index_html = index_html.replace("<!-- MULTILANG_TAGS -->", multilang)
    index_html = index_html.replace("$$SKIP_TO_MAIN_CONTENT$$", "Skip to main content")
    index_html = index_html.replace("$$TITLE$$", title)
    index_html = index_html.replace("$$DESCRIPTION$$", description)
    index_html = index_html.replace("$$TITLE_ID$$", slug_raw)
    index_html = index_html.replace("$$LANG$$", lang)
    index_html = index_html.replace("$$SLUG$$", "")
    index_html = index_html.replace("$$SELECT_FAITH$$", select_faith)
    index_html = index_html.replace("$$ROOT_HREF$$", root_href)
    index_html = index_html.replace("$$PAGE_HREF$$", root_href + "/" + lang + "/" + slug_raw)
    index_html = index_html.replace("<link rel=\"preload\" href=\"/static/img/logo/logo-smooth.svg\" as=\"image\">", "")
    index_html = index_html.replace("<link rel=\"preload\" href=\"/static/font/ssfp/ssp/SourceSansPro-BASIC-Regular.woff2\" as=\"font\" type=\"font/woff2\" crossorigin>", "")
    return index_html

# SCRIPT STARTS HERE

TAGS = json.loads(read_file("./tags.json"))

articles_by_tag = {}
articles_by_date = {}

root_href = get_root_href()
templates = load_templates()
articles = load_articles()
authors = json.loads(read_file("./authors.json"))
render_page_author_pages("de", authors)
render_page_author_pages("en", authors)

for slug, readme in articles.items():

    lang = slug.split("/")[0]
    slug_raw = slug.split("/")[1]
    title_id = lang + "-" + slug_raw
    html = templates["index"]
    a = {}
    for q in readme.get("authors", []):
        a[q] = authors[q]

    pagemeta = {
        "title": readme.get("title", ""),
        "keywords": readme.get("tags", []),
        "date": readme.get("date", ""),
        "authors": a,
        "contact_url": "/about",
        "description": text_from_par(readme.get("tagline", [])),
        "img": readme.get("img", {}),
        "initiale": get_initiale(readme, slug)
    }

    # insert sorted by keyword
    for t in pagemeta["keywords"]:
        tag_name = TAGS[lang]["tags"][t]
        if not(lang in articles_by_tag):
            articles_by_tag[lang] = { }
        if not(t in articles_by_tag[lang]):
            articles_by_tag[lang][t] = {}
        if not("links" in articles_by_tag[lang][t]):
            articles_by_tag[lang][t]["links"] = []
        articles_by_tag[lang][t]["links"].append({"slug": slug_raw, "title": pagemeta["title"] })

    # insert sorted by date
    if not(lang in articles_by_date):
        articles_by_date[lang] = { }
    
    article_is_prayer = ("gebet" in pagemeta["keywords"]) or ("prayer" in pagemeta["keywords"])

    if pagemeta["date"] == "":
        if not(article_is_prayer):
            print("error: article " + lang + "/" + slug_raw + " has no date")
    else:
        year = pagemeta["date"].split("-")[0]
        month = pagemeta["date"].split("-")[1]
        day = pagemeta["date"].split("-")[2]
        if not(year in articles_by_date[lang]):
            articles_by_date[lang][year] = { }
        if not(month in articles_by_date[lang][year]):
            articles_by_date[lang][year][month] = { }
        if not(day in articles_by_date[lang][year][month]):
            articles_by_date[lang][year][month][day] = {"slug": slug_raw, "title": pagemeta["title"] }
        
    html = html.replace("<!-- HEAD_TEMPLATE_HTML -->", head(templates, lang, pagemeta, lang + "-" + slug_raw))
    html = html.replace("<!-- HEADER_NAVIGATION -->", header_navigation(templates, lang, True))
    html = html.replace("<!-- LINK_TAGS -->", link_tags(templates, lang, readme.get("tags", [])))
    if slug == "de/rosenkranz" or slug == "en/rosary":
        html = html.replace("<!-- PAGE_DESCRIPTION -->", "<div style='max-width:500px;margin-left:auto;margin-right:auto;'>" + page_desciption(templates, lang, pagemeta) + "</div>")
        html = html.replace("<!-- BODY_ABSTRACT -->", "<div class='abstract' style='max-width:500px;margin:0 auto;'><blockquote class='first-block first-graf block page-abstract blockquote-level-1' style='--bsm: 0;'>" + body_abstract(templates, lang, readme.get("summary", [])) + "</blockquote></div>")
        html = html.replace("<!-- BODY_CONTENT -->", render_rosary_body(templates, lang, pagemeta))
    else:

        if not(article_is_prayer):
            html = html.replace("<!-- TOC -->", table_of_contents(templates, lang, readme.get("sections", [])))
            html = html.replace("<!-- PAGE_DESCRIPTION -->", page_desciption(templates, lang, pagemeta))
            html = html.replace("<!-- PAGE_METADATA -->", page_metadata(templates, lang, pagemeta))
        
        html = html.replace("<!-- BODY_ABSTRACT -->", body_abstract(templates, lang, readme.get("summary", [])))
        html = html.replace("<!-- BODY_CONTENT -->", body_content(templates, lang, readme.get("sections", [])))
        html = html.replace("<!-- BODY_NOSCRIPT -->", body_noscript(templates, lang))
    
    skip = "Skip to main content"
    if lang == "de":
        skip = "Zum Hauptinhalt springen"
    html = html.replace("$$SKIP_TO_MAIN_CONTENT$$", skip)
    contact = "en/about"
    if lang == "de":
        contact = "de/impressum"
    html = html.replace("$$CONTACT_URL$$", contact)
    html = html.replace("$$TITLE$$", pagemeta["title"] + " - dubia.cc")
    html = html.replace("$$TITLE_ID$$", title_id)
    html = html.replace("$$LANG$$", lang)
    html = html.replace("$$SLUG$$", slug_raw)
    html = html.replace("$$ROOT_HREF$$", root_href)
    html = html.replace("$$PAGE_HREF$$", root_href + "/" + slug)

    write_file(html, "./" + lang + "/" + slug_raw + ".html")

write_file(generate_gitignore(articles), "./.gitignore")

at = {}
for lang, topics in articles_by_tag.items():
    if not(lang in at):
        at[lang] = []
    for topic, links in topics.items():
        at[lang].append({"id": topic, "title": TAGS[lang]["tags"][topic], "links": links["links"] })

write_file(render_special_page(templates, "de", at.get("de", []), { "title": "Themen", "description": "Themenübersicht", "img": { }}, "de-themen"), "./de/themen.html")
write_file(render_special_page(templates, "en", at.get("en", []), { "title": "Topics", "description": "Topics", "img": { }}, "en-topics"), "./en/topics.html")

ad2 = {}
for lang, year in articles_by_date.items():
    if not(lang in ad2):
        ad2[lang] = []
    a2 = {}
    for year, months in year.items():
        for month, days in months.items():
            for day, link in days.items():
                if not(year in a2):
                    a2[year] = []
                a2[year].append({"slug": link["slug"], "title": month + "-" + day + ": " + link["title"] })
    for y, links in a2.items():
        ad2[lang].append({ "id": "y" + y, "title": y, "links": links })
    ad2[lang].reverse()

write_file(render_special_page(templates, "de", ad2.get("de", []), { "title": "Neueste Links", "description": "Neueste Links", "img": { }}, "de-neues"), "./de/neues.html")
write_file(render_special_page(templates, "en", ad2.get("en", []), { "title": "Newest Links", "description": "Newest links", "img": { }}, "en-newest"), "./en/newest.html")

write_file(render_special_page(templates, "de", TAGS["de"]["ressources"], { "title": "Ressourcen", "description": "Ressourcen", "img": { }}, "de-ressourcen"), "./de/ressourcen.html")
write_file(render_special_page(templates, "en", TAGS["en"]["ressources"], { "title": "Tools", "description": "Tools", "img": { }}, "en-tools"), "./en/tools.html")

write_file(render_special_page(templates, "de", TAGS["de"]["shop"], { "title": "Shop", "description": "Shop", "img": { }}, "de-shop"), "./de/shop.html")
write_file(render_special_page(templates, "en", TAGS["en"]["shop"], { "title": "Shop", "description": "Shop", "img": { }}, "en-shop"), "./en/shop.html")

write_file(render_special_page(templates, "de", TAGS["de"]["about"], { "title": "Impressum", "description": "Impressum", "img": { }}, "de-impressum"), "./de/impressum.html")
write_file(render_special_page(templates, "en", TAGS["en"]["about"], { "title": "About", "description": "About", "img": { }}, "en-about"), "./en/about.html")

write_file(generate_searchindex("de", articles), "./de/index.json")
write_file(generate_searchindex("en", articles), "./en/index.json")

write_file(render_index_html("en", articles, TAGS), "./en.html")
write_file(render_index_html("de", articles, TAGS), "./de.html")

write_file(read_file("./templates/selectlang.html"), "./index.html")
