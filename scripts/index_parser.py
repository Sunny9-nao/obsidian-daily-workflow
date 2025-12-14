""""
INDEX line parser for daily notes

This module provides functionality to parse INDEX lines from daily notes
according to the fixed grammar defined in docs/ai-instructions.md
"""
import re
from typing import Optional, Dict, List, Any


class IndexParseError(Exception):
    """"Raised when an INDEX line cannot be parsed"""
    pass


# Regex patterns for INDEX line parsing
BLOCK_ID_PATTERN = re.compile(r'\^(\d{8})-([tleia])(\d+)$')
LINK_BODY_PATTERN = re.compile(r'!\[\[([^#\]]+)#(\^[^\]]+)\]\]')
TAG_PATTERN = re.compile(r'#([a-zA-Z0-9_]+):([^\s#]+)')
META_EFFORT_PATTERN = re.compile(r'effort=(\d+)')
META_STATUS_PATTERN = re.compile(r'status=(inbox|doing|done|dropped)')

VALID_TYPES = {'learning', 'experiment', 'idea', 'action'}
VALID_STATUSES = {'inbox', 'doing', 'done', 'dropped'}


def parse_index_line(line: str) -> Dict[str, Any]:
    """"
    Parse a single INDEX line according to the fixed grammar
    
    Args:
        line: A single INDEX line from daily notes
        
    Returns:
        Dictionary containing parsed fields:
        - type: str (learning/experiment/idea/action)
        - body: str (content text or link)
        - ref_source_path: Optional[str] (for LINK_BODY)
        - ref_block_id: Optional[str] (for LINK_BODY)
        - tags: List[str] (list of "prefix:value" tags)
        - block_id: str (^YYYYMMDD-<kind><n>)
        - effort_min: Optional[int] (action only)
        - status: Optional[str] (action only)
        
    Raises:
        IndexParseError: If line doesn't conform to expected format
    """
    line = line.strip()
    
    # Must start with "- "
    if not line.startswith('- '):
        raise IndexParseError(f"Line must start with '- ': {line}")
    
    # Extract block_id first (must be at the end)
    block_id_match = BLOCK_ID_PATTERN.search(line)
    if not block_id_match:
        raise IndexParseError(f"Missing or invalid block_id (must be ^YYYYMMDD-<kind><n>): {line}")
    
    block_id = line[block_id_match.start():block_id_match.end()]
    content_before_block_id = line[2:block_id_match.start()].strip()
    
    # Extract type
    type_match = re.match(r'\[(\w+)\]\s+', content_before_block_id)
    if not type_match:
        raise IndexParseError(f"Missing type [learning|experiment|idea|action]: {line}")
    
    item_type = type_match.group(1)
    if item_type not in VALID_TYPES:
        raise IndexParseError(f"Invalid type '{item_type}'. Must be one of {VALID_TYPES}: {line}")
    
    remaining = content_before_block_id[type_match.end():].strip()
    
    # Extract tags
    tags = []
    # Remove link bodies first to avoid false positives in tag detection
    remaining_without_links = LINK_BODY_PATTERN.sub('', remaining)
    
    # Check for invalid tag format (# without prefix:value)
    invalid_tags = re.findall(r'#([^\s:]+)(?:\s|$)', remaining_without_links)
    for tag in invalid_tags:
        # Check if this tag is not in valid prefix:value format
        tag_full = f'#{tag}'
        if ':' not in tag_full:
            raise IndexParseError(f"Invalid tag format '{tag_full}'. Tags must be #prefix:value: {line}")
    
    for match in TAG_PATTERN.finditer(remaining):
        prefix = match.group(1)
        value = match.group(2)
        tags.append(f"{prefix}:{value}")
    
    # Remove tags from remaining to isolate body and meta
    body_and_meta = TAG_PATTERN.sub('', remaining).strip()
    
    # Extract meta (effort and status) for action type
    effort_min = None
    status = None
    
    if item_type == 'action':
        effort_match = META_EFFORT_PATTERN.search(body_and_meta)
        status_match = META_STATUS_PATTERN.search(body_and_meta)
        
        if not effort_match or not status_match:
            raise IndexParseError(f"action type must have 'effort=<min> status=<status>': {line}")
        
        effort_min = int(effort_match.group(1))
        status = status_match.group(1)
        
        # Remove meta from body
        body_and_meta = META_EFFORT_PATTERN.sub('', body_and_meta)
        body_and_meta = META_STATUS_PATTERN.sub('', body_and_meta)
    
    body = body_and_meta.strip()
    
    # Check if body is LINK_BODY or TEXT_BODY
    ref_source_path = None
    ref_block_id = None
    
    link_match = LINK_BODY_PATTERN.search(body)
    if link_match:
        ref_source_path = link_match.group(1)
        ref_block_id = link_match.group(2)
    
    return {
        'type': item_type,
        'body': body,
        'ref_source_path': ref_source_path,
        'ref_block_id': ref_block_id,
        'tags': tags,
        'block_id': block_id,
        'effort_min': effort_min,
        'status': status,
    }


def extract_index_section(content: str) -> List[str]:
    """"
    Extract INDEX section lines from daily note content
    
    Args:
        content: Full content of a daily note
        
    Returns:
        List of INDEX lines (excluding the ## INDEX header)
        
    Raises:
        IndexParseError: If no INDEX section is found
    """
    lines = content.split('\n')
    in_index_section = False
    index_lines = []
    
    for line in lines:
        # Check if we're entering INDEX section
        if line.strip() == '## INDEX':
            in_index_section = True
            continue
        
        # Check if we're leaving INDEX section (next heading)
        if in_index_section and line.strip().startswith('## '):
            break
        
        # Collect lines in INDEX section
        if in_index_section and line.strip():
            if line.strip().startswith('- '):
                index_lines.append(line)
    
    if not in_index_section:
        raise IndexParseError("No '## INDEX' section found in content")
    
    return index_lines
