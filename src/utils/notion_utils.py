def extract_title(page: dict) -> str:
    """Extract title from page data with multiple fallback options"""
    # Try direct title field first
    if isinstance(page.get('title'), str):
        return page['title']
    
    # Try properties.Page.title
    if 'properties' in page:
        page_prop = page['properties'].get('Page', {})
        if page_prop and 'title' in page_prop and page_prop['title']:
            try:
                return page_prop['title'][0]['plain_text']
            except (IndexError, KeyError):
                pass
        
        # Try properties.Name.title as fallback
        name_prop = page['properties'].get('Name', {})
        if name_prop and 'title' in name_prop and name_prop['title']:
            try:
                return name_prop['title'][0]['plain_text']
            except (IndexError, KeyError):
                pass
    
    # Try to extract from URL if available
    if page.get('url'):
        try:
            # Extract last part of URL and clean it
            url_title = page['url'].split('/')[-1].replace('-', ' ').title()
            if url_title:
                return url_title
        except Exception:
            pass
    
    # Final fallback - use ID with prefix
    return f"Untitled Page ({page['id'][:8]})"