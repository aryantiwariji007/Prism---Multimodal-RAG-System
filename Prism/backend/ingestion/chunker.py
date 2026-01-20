"""
Text chunking utilities for document processing
Token-free, Ollama / DeepSeek compatible
"""

import re
from typing import List, Dict
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Add the backend directory to the Python path for progress service
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from app.services.progress_service import progress_service
except ImportError:
    progress_service = None


class DocumentChunker:
    def __init__(
        self,
        chunk_size: int = 800,       # characters
        chunk_overlap: int = 150     # characters
    ):
        """
        Initialize document chunker (Recursive Character based)

        Args:
            chunk_size: Max characters per chunk
            chunk_overlap: Overlap between chunks (characters)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Define separators for recursive splitting (in order of priority)
        self.separators = ["\n\n", "\n", " ", ""]

    def chunk_text(self, text: str, file_id: str) -> List[Dict]:
        """
        Split text into overlapping using recursive character splitting
        Preserves structure (like tables) better than fixed slicing.
        """
        text = self._clean_text(text)
        
        # Use recursive splitting logic
        final_chunks_text = self._recursive_split(text, self.separators)

        chunks = []
        for i, chunk_txt in enumerate(final_chunks_text):
            chunks.append({
                "file_id": file_id,
                "chunk_id": i,
                "text": chunk_txt,
                "char_count": len(chunk_txt),
            })

        return chunks

    def chunk_document_pages(
        self,
        pages: List[Dict],
        progress_file_id: str = None
    ) -> List[Dict]:
        """
        Chunk a document already split into pages
        """
        all_chunks = []
        total_pages = len(pages)

        for page_idx, page in enumerate(pages):
            if progress_service and progress_file_id:
                progress = int((page_idx / total_pages) * 90)
                progress_service.update_progress(
                    progress_file_id,
                    2,
                    f"Chunking page {page_idx + 1} of {total_pages}",
                    progress
                )

            page_chunks = self.chunk_text(
                page.get("text", ""),
                page.get("file_id")
            )

            for chunk in page_chunks:
                chunk["page"] = page.get("page")
                chunk["source_page"] = page.get("page")

            all_chunks.extend(page_chunks)

        # Re-index all chunks to ensure unique chunk_ids across the entire document
        for i, chunk in enumerate(all_chunks):
            chunk["chunk_id"] = i

        if progress_service and progress_file_id:
            progress_service.update_progress(
                progress_file_id,
                2,
                f"Chunking completed - {len(all_chunks)} chunks created",
                100
            )

        logger.info(f"Created {len(all_chunks)} chunks from {total_pages} pages")
        return all_chunks

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """
        Recursively split text by separators until chunks differ
        based on providing correct size.
        """
        final_chunks = []
        
        # Get appropriate separator
        separator = separators[-1]
        new_separators = []
        for i, _s in enumerate(separators):
            if _s == "":
                separator = _s
                break
            if _s in text:
                separator = _s
                new_separators = separators[i + 1:]
                break
                
        # Split
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text) # Split by char

        # Reform chunks
        good_splits = []
        _separator = separator if separator else ""
        
        for s in splits:
            if not s.strip():
                continue
            good_splits.append(s)

        merged_text = []
        current_chunk = []
        current_len = 0
        
        for split in good_splits:
            split_len = len(split)
            
            # If a single split is too big, must recurse
            if split_len > self.chunk_size:
                # Add current accumulation first
                if current_chunk:
                    merged_text.append(_separator.join(current_chunk))
                    current_chunk = []
                    current_len = 0
                # Recurse on the big split
                if new_separators:
                    sub_chunks = self._recursive_split(split, new_separators)
                    merged_text.extend(sub_chunks)
                else:
                    # Hard slice if no separators left (unlikely to happen often)
                    merged_text.extend(self._hard_slice(split))
                continue

            # Check if adding this split exceeds chunk size
            # Add separator length (estimation)
            sep_len = len(_separator) if current_len > 0 else 0
            
            if current_len + split_len + sep_len > self.chunk_size:
                # Flush current
                merged_text.append(_separator.join(current_chunk))
                
                # Start overlap logic: Keep last items that fit in overlap
                # This is a simplified overlap since true recursive overlap is complex
                # We just start new chunk with current split
                current_chunk = [split]
                current_len = split_len
            else:
                current_chunk.append(split)
                current_len += split_len + sep_len
        
        if current_chunk:
            merged_text.append(_separator.join(current_chunk))
            
        return merged_text

    def _hard_slice(self, text: str) -> List[str]:
        """Fallback to hard slicing if recursive fails"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start += self.chunk_size - self.chunk_overlap
        return chunks

    def _clean_text(self, text: str) -> str:
        """
        Clean text but PRESERVE NEWLINES to keep table structure.
        """
        if not text:
            return ""
        # 1. Normalize carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # 2. Remove excessive duplicate newlines (more than 2)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # 3. Clean spaces but keep newlines
        # Split by newline, clean each line, join back
        lines = text.split('\n')
        cleaned_lines = [re.sub(r"\s+", " ", line).strip() for line in lines]
        return "\n".join(cleaned_lines)


# Global chunker instance
document_chunker = DocumentChunker()
