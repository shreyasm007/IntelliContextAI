from typing import Dict, Any, Optional, Tuple
import re
from datetime import datetime

class DocumentPreprocessor:
    """Handles document preprocessing steps before chunking."""

    def __init__(self):
        self.cleaning_patterns = [
            (r'\s+', ' '),  # Replace multiple spaces with single space
            (r'^\s+|\s+$', ''),  # Remove leading/trailing whitespace
            (r'[^\x00-\x7F]+', ' ')  # Replace non-ASCII chars with space
        ]

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        cleaned_text = text
        for pattern, replacement in self.cleaning_patterns:
            cleaned_text = re.sub(pattern, replacement, cleaned_text)
        return cleaned_text

    def extract_metadata(self, text: str, filename: str) -> Dict[str, Any]:
        """Extract metadata from document content."""
        metadata = {
            'filename': filename,
            'processed_date': datetime.now().isoformat(),
            'char_count': len(text),
            'word_count': len(text.split()),
            'estimated_reading_time': len(text.split()) / 200  # Assuming 200 WPM
        }

        # Try to extract title from first line
        first_line = text.strip().split('\n')[0]
        if len(first_line) < 200:  # Reasonable title length
            metadata['title'] = first_line
        else:
            metadata['title'] = filename

        return metadata

    def validate_content(self, text: str) -> Tuple[bool, Optional[str]]:
        """Validate document content."""
        if not text.strip():
            return False, "Document is empty"

        if len(text) < 10:
            return False, "Document content too short"

        # Check for common encoding issues
        try:
            text.encode('ascii', 'strict')
        except UnicodeEncodeError:
            return True, "Document contains non-ASCII characters"

        return True, None