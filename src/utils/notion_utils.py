def extract_title(page: dict) -> str:
    """Extract clean title from page data"""
    if 'properties' in page:
        for prop_name in ['Page', 'Name', 'Title']:
            if prop_name in page['properties']:
                title_prop = page['properties'][prop_name].get('title', [])
                if title_prop and isinstance(title_prop, list):
                    plain_text = title_prop[0].get('plain_text', '').strip()
                    if plain_text:
                        parts = plain_text.split()
                        if len(parts[-1]) == 32 and parts[-1].isalnum():
                            plain_text = ' '.join(parts[:-1])
                        return plain_text

    if 'title' in page:
        title_array = page['title']
        if isinstance(title_array, list) and title_array:
            title = title_array[0].get('plain_text', '').strip()
            if title:
                return title

    return "Untitled Document"