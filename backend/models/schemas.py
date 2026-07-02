"""
Pydantic schemas for the Brownfield IDE API.
"""

from __future__ import annotations
from typing import Optional, List, Literal, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# File System Schemas
# ---------------------------------------------------------------------------

class FileNode(BaseModel):
    """Represents a file or folder in the project tree."""
    name: str
    path: str  # Relative to project root, forward-slash separated
    type: Literal["file", "folder"]
    extension: Optional[str] = None  # e.g. "js", "py", "json"
    size: Optional[int] = None       # Bytes (files only)
    modified: Optional[float] = None  # Unix timestamp
    # None = folder not yet expanded (lazy load)
    # []   = folder is empty
    # [..] = folder children (loaded)
    children: Optional[List[FileNode]] = None

    model_config = {"populate_by_name": True}


FileNode.model_rebuild()  # Required for self-referential model


class FileContent(BaseModel):
    """File content returned from the API."""
    path: str
    content: str
    size: int
    encoding: str = "utf-8"
    language: Optional[str] = None  # Monaco language ID


class WriteFileRequest(BaseModel):
    """Request body for writing a file."""
    path: str = Field(..., description="Relative path from project root")
    content: str = Field(..., description="File content to write")


class CreateFileRequest(BaseModel):
    """Request body for creating a new file."""
    path: str = Field(..., description="Relative path from project root")


class CreateFolderRequest(BaseModel):
    """Request body for creating a new folder."""
    path: str = Field(..., description="Relative path from project root")


class DeleteRequest(BaseModel):
    """Request body for deleting a file or folder."""
    path: str = Field(..., description="Relative path from project root")


class RenameRequest(BaseModel):
    """Request body for renaming a file or folder."""
    path: str = Field(..., description="Current relative path from project root")
    new_name: str = Field(..., description="New name (not full path, just the filename/dirname)")


class SearchResult(BaseModel):
    """A search result entry."""
    nodes: List[FileNode]
    total: int
    query: str


# ---------------------------------------------------------------------------
# Workspace Schemas
# ---------------------------------------------------------------------------

class RecentProject(BaseModel):
    """A recently opened project."""
    path: str
    name: str
    opened_at: str  # ISO 8601 timestamp


class WorkspaceState(BaseModel):
    """Persisted workspace state."""
    current_project: Optional[str] = None
    recent_projects: List[RecentProject] = []


class OpenProjectRequest(BaseModel):
    """Request to open a project by absolute path."""
    path: str = Field(..., description="Absolute path to the project folder")


class OpenProjectResponse(BaseModel):
    """Response after opening a project."""
    project_name: str
    project_path: str
    tree: FileNode


# ---------------------------------------------------------------------------
# Terminal Schemas
# ---------------------------------------------------------------------------

class TerminalSessionInfo(BaseModel):
    """Information about a terminal session."""
    session_id: str
    cwd: str
    alive: bool
    created_at: str


class CreateTerminalRequest(BaseModel):
    """Request to create a terminal session."""
    cwd: Optional[str] = None
    cols: int = 80
    rows: int = 24


class CreateTerminalResponse(BaseModel):
    """Response after creating a terminal session."""
    session_id: str
    cwd: str


# ---------------------------------------------------------------------------
# Generic Response
# ---------------------------------------------------------------------------

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None
