import type { Note, NoteInput, NoteUpdate, PresignResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed (${response.status})`);
  }

  if (response.status === 204) {
    return null as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }
  return (await response.text()) as T;
}

async function listNotes(): Promise<Note[]> {
  return request<Note[]>("/notes");
}

async function getNote(noteId: string): Promise<Note> {
  return request<Note>(`/notes/${noteId}`);
}

async function createNote(payload: NoteInput): Promise<Note> {
  return request<Note>("/notes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function updateNote(noteId: string, payload: NoteUpdate): Promise<Note> {
  return request<Note>(`/notes/${noteId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

async function deleteNote(noteId: string): Promise<void> {
  await request(`/notes/${noteId}`, { method: "DELETE" });
}

async function presignUpload(
  noteId: string,
  fileName: string,
  contentType: string,
): Promise<PresignResponse> {
  return request<PresignResponse>("/notes/presign", {
    method: "POST",
    body: JSON.stringify({
      note_id: noteId,
      file_name: fileName,
      content_type: contentType,
    }),
  });
}

async function uploadFile(url: string, file: Blob, contentType: string) {
  const response = await fetch(url, {
    method: "PUT",
    headers: { "Content-Type": contentType },
    body: file,
  });
  if (!response.ok) {
    throw new Error("Upload failed");
  }
}

async function summarizeNote(noteId: string, content: string) {
  return request<{ summary: string; keywords: string[] }>("/ai/summarize", {
    method: "POST",
    body: JSON.stringify({ note_id: noteId, content }),
  });
}

async function ocr(imageUrl: string, noteId?: string) {
  return request<{ text: string }>("/ai/ocr", {
    method: "POST",
    body: JSON.stringify({ image_url: imageUrl, note_id: noteId }),
  });
}

async function transcribe(audioUrl: string, noteId?: string) {
  return request<{ text: string }>("/ai/transcribe", {
    method: "POST",
    body: JSON.stringify({ audio_url: audioUrl, note_id: noteId }),
  });
}

export const api = {
  listNotes,
  getNote,
  createNote,
  updateNote,
  deleteNote,
  presignUpload,
  uploadFile,
  summarizeNote,
  ocr,
  transcribe,
};
