use std::path::Path;

use crate::MetaJson;

pub fn generate_resistance_pages(cwd: &Path, meta: &MetaJson) -> Result<(), String> {
    // For each language, generate a resistance.html file
    for lang in meta.strings.keys() {
        let content = generate_resistance_html(lang, meta)?;
        let output_path = cwd.join(lang).join("resistance.html");

        // Ensure the directory exists
        if let Some(parent) = output_path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }

        // Write the file
        let _ = std::fs::write(output_path, &crate::minify(&content));
    }

    Ok(())
}

fn generate_resistance_html(lang: &str, meta: &MetaJson) -> Result<String, String> {
    // Get the template HTML
    let mut template = include_str!("../../templates/resistance.html").to_string();

    // Get translations for this language
    let strings = meta
        .strings
        .get(lang)
        .ok_or_else(|| format!("Language not found: {}", lang))?;

    // Replace standard placeholders
    template = template.replace("$$LANG$$", lang);
    template = template.replace("$$ROOT_HREF$$", &crate::get_root_href());

    // Replace translation placeholders
    for (key, value) in strings.iter() {
        let placeholder = format!("$${}$$", key);
        template = template.replace(&placeholder, value);
    }

    // Add specific titles and descriptions
    let title = crate::get_string(meta, lang, "resistance-title")
        .unwrap_or_else(|_| "Catholic Resistance".to_string());
    let desc = crate::get_string(meta, lang, "resistance-desc")
        .unwrap_or_else(|_| "Find traditional Catholic priests and Masses worldwide".to_string());

    template = template.replace("$$TITLE$$", &title);
    template = template.replace("$$DESCRIPTION$$", &desc);

    Ok(template)
}
