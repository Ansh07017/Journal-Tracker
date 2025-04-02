import os
import requests
from datetime import datetime

# External API keys
CROSSREF_EMAIL = os.environ.get("CROSSREF_EMAIL", "user@example.com")
PATENTS_API_KEY = os.environ.get("PATENTS_API_KEY", "")

def search_papers(query, limit=10):
    """
    Search for papers using the Crossref API
    """
    try:
        # Use Crossref API for searching papers
        url = f"https://api.crossref.org/works"
        params = {
            'query': query,
            'rows': limit,
            'sort': 'relevance',
            'order': 'desc',
            'mailto': CROSSREF_EMAIL
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        results = []
        if 'message' in data and 'items' in data['message']:
            for item in data['message']['items']:
                # Extract paper information
                paper = {
                    'title': item.get('title', [''])[0] if item.get('title') else '',
                    'authors': _format_authors(item.get('author', [])),
                    'publication': item.get('container-title', [''])[0] if item.get('container-title') else '',
                    'year': item.get('published', {}).get('date-parts', [['']])[0][0] if item.get('published') else '',
                    'doi': item.get('DOI', ''),
                    'url': item.get('URL', ''),
                    'type': item.get('type', '')
                }
                results.append(paper)
                
        return results
    except Exception as e:
        print(f"Error searching papers: {str(e)}")
        return []

def get_doi_metadata(doi):
    """
    Get metadata for a specific DOI
    """
    try:
        url = f"https://api.crossref.org/works/{doi}"
        response = requests.get(url)
        
        if response.status_code != 200:
            return {'error': f'DOI not found or unavailable. Status code: {response.status_code}'}
        
        data = response.json()
        
        if 'message' not in data:
            return {'error': 'Invalid response from Crossref API'}
        
        item = data['message']
        
        # Extract paper information
        metadata = {
            'title': item.get('title', [''])[0] if item.get('title') else '',
            'authors': _format_authors(item.get('author', [])),
            'publication': item.get('container-title', [''])[0] if item.get('container-title') else '',
            'year': item.get('published', {}).get('date-parts', [['']])[0][0] if item.get('published') else '',
            'doi': item.get('DOI', ''),
            'url': item.get('URL', ''),
            'type': item.get('type', ''),
            'abstract': item.get('abstract', ''),
            'keywords': ', '.join(item.get('subject', []))
        }
        
        return metadata
    except Exception as e:
        print(f"Error getting DOI metadata: {str(e)}")
        return {'error': str(e)}

def _format_authors(authors_list):
    """
    Format authors list into a string
    """
    authors = []
    for author in authors_list:
        if 'given' in author and 'family' in author:
            authors.append(f"{author['family']}, {author['given']}")
        elif 'name' in author:
            authors.append(author['name'])
    
    return '; '.join(authors)

def format_citation(doi, style='ieee'):
    """
    Format a citation for a DOI in the specified style
    """
    try:
        # Use the Crossref Content Negotiation API for citations
        url = f"https://doi.org/{doi}"
        
        headers = {
            'Accept': _get_citation_format(style)
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.text.strip()
        else:
            # Fallback to metadata and manual formatting
            metadata = get_doi_metadata(doi)
            if 'error' in metadata:
                return f"Unable to generate citation: {metadata['error']}"
            
            return _manual_format_citation(metadata, style)
    
    except Exception as e:
        print(f"Error formatting citation: {str(e)}")
        return f"Unable to generate citation: {str(e)}"

def _get_citation_format(style):
    """
    Get the content type for citation format
    """
    style_formats = {
        'bibtex': 'application/x-bibtex',
        'ris': 'application/x-research-info-systems',
        'apa': 'text/x-bibliography; style=apa',
        'mla': 'text/x-bibliography; style=mla',
        'chicago': 'text/x-bibliography; style=chicago-author-date',
        'harvard': 'text/x-bibliography; style=harvard',
        'ieee': 'text/x-bibliography; style=ieee'
    }
    
    return style_formats.get(style.lower(), 'text/x-bibliography')

def _manual_format_citation(metadata, style):
    """
    Manually format a citation when the API fails
    """
    if style.lower() == 'ieee':
        authors = metadata['authors'].replace('; ', ', ')
        title = metadata['title']
        publication = metadata['publication']
        year = metadata['year']
        
        return f"{authors}, \"{title},\" {publication}, {year}."
    
    # Default fallback format
    return f"{metadata['authors']}. {metadata['title']}. {metadata['publication']}. {metadata['year']}."

def search_patents(query, limit=10):
    """
    Search for patents (using a mock for now, would require a patent API)
    """
    try:
        # Note: In a production system, you would connect to a patent database API like
        # USPTO, EPO, Google Patents, etc.
        # For this demo, we'll return a simple placeholder response
        
        # Sample implementation using the USPTO PatentsView API
        url = "https://api.patentsview.org/patents/query"
        
        params = {
            "q": {"_text_any": {"patent_title": query}},
            "f": ["patent_number", "patent_title", "patent_date", "patent_abstract", 
                 "inventor_first_name", "inventor_last_name", "assignee_organization"],
            "o": {"page": 0, "per_page": limit}
        }
        
        # This would be an actual API call in a production system
        # response = requests.post(url, json=params)
        # data = response.json()
        
        # Placeholder mock response
        results = []
        # In production, you would extract actual data from 'data' variable
        
        return results
    except Exception as e:
        print(f"Error searching patents: {str(e)}")
        return []
