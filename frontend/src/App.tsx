import { useEffect, useMemo, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import "./App.css";
import { api } from "./api";
import type { Note } from "./types";

type NoteForm = {
  title: string;
  content: string;
  tags: string;
};

const tagsToString = (tags: string[]) => tags.join(", ");
const tagsFromString = (raw: string) =>
  raw
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);

function App() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [newForm, setNewForm] = useState<NoteForm>({
    title: "",
    content: "",
    tags: "",
  });
  const [editForm, setEditForm] = useState<NoteForm>({
    title: "",
    content: "",
    tags: "",
  });
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [aiBusy, setAiBusy] = useState(false);
  const [ocrTarget, setOcrTarget] = useState<string>("");
  const [transcribeTarget, setTranscribeTarget] = useState<string>("");

  const selectedNote = useMemo(
    () => notes.find((n) => n.note_id === selectedId) ?? null,
    [notes, selectedId],
  );

  useEffect(() => {
    void loadNotes();
  }, []);

  useEffect(() => {
    if (selectedNote) {
      setEditForm({
        title: selectedNote.title,
        content: selectedNote.content,
        tags: tagsToString(selectedNote.tags),
      });
      setOcrTarget(
        selectedNote.media.find((m) => m.type.startsWith("image"))?.url ?? "",
      );
      setTranscribeTarget(
        selectedNote.media.find((m) => m.type.startsWith("audio"))?.url ?? "",
      );
    }
  }, [selectedNote?.note_id]);

  async function loadNotes() {
    setLoading(true);
    try {
      const data = await api.listNotes();
      setNotes(data);
      if (!selectedId && data.length) {
        setSelectedId(data[0].note_id);
      }
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function refreshSelected(noteId: string) {
    try {
      const latest = await api.getNote(noteId);
      setNotes((prev) =>
        prev.map((note) => (note.note_id === noteId ? latest : note)),
      );
      setSelectedId(noteId);
    } catch (err) {
      setMessage((err as Error).message);
    }
  }

  async function handleCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    try {
      const created = await api.createNote({
        title: newForm.title,
        content: newForm.content,
        tags: tagsFromString(newForm.tags),
      });
      setNotes((prev) => [created, ...prev]);
      setSelectedId(created.note_id);
      setNewForm({ title: "", content: "", tags: "" });
      setMessage("Note created");
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!selectedNote) return;
    setLoading(true);
    try {
      const updated = await api.updateNote(selectedNote.note_id, {
        title: editForm.title,
        content: editForm.content,
        tags: tagsFromString(editForm.tags),
      });
      setNotes((prev) =>
        prev.map((note) => (note.note_id === updated.note_id ? updated : note)),
      );
      setMessage("Note saved");
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (!selectedNote) return;
    if (!window.confirm("Delete this note?")) return;
    setLoading(true);
    try {
      await api.deleteNote(selectedNote.note_id);
      setNotes((prev) => prev.filter((n) => n.note_id !== selectedNote.note_id));
      const remaining = notes.filter((n) => n.note_id !== selectedNote.note_id);
      setSelectedId(remaining[0]?.note_id ?? null);
      setMessage("Note deleted");
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(file: File) {
    if (!selectedNote) return;
    setUploading(true);
    try {
      const presign = await api.presignUpload(
        selectedNote.note_id,
        file.name,
        file.type || "application/octet-stream",
      );
      await api.uploadFile(presign.upload_url, file, file.type);
      const mediaType = file.type || "file";
      const updated = await api.updateNote(selectedNote.note_id, {
        media: [...(selectedNote.media || []), { type: mediaType, url: presign.object_url }],
      });
      setNotes((prev) =>
        prev.map((note) => (note.note_id === updated.note_id ? updated : note)),
      );
      setMessage("File uploaded and attached");
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setUploading(false);
    }
  }

  async function handleSummarize() {
    if (!selectedNote) return;
    setAiBusy(true);
    try {
      await api.summarizeNote(selectedNote.note_id, editForm.content);
      await refreshSelected(selectedNote.note_id);
      setMessage("Summary updated");
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setAiBusy(false);
    }
  }

  async function handleOCR() {
    if (!selectedNote) return;
    const target =
      ocrTarget || selectedNote.media.find((m) => m.type.startsWith("image"))?.url;
    if (!target) {
      setMessage("Add an image first.");
      return;
    }
    setAiBusy(true);
    try {
      await api.ocr(target, selectedNote.note_id);
      await refreshSelected(selectedNote.note_id);
      setMessage("OCR text added to note");
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setAiBusy(false);
    }
  }

  async function handleTranscribe() {
    if (!selectedNote) return;
    const target =
      transcribeTarget ||
      selectedNote.media.find((m) => m.type.startsWith("audio"))?.url;
    if (!target) {
      setMessage("Add an audio file first.");
      return;
    }
    setAiBusy(true);
    try {
      await api.transcribe(target, selectedNote.note_id);
      await refreshSelected(selectedNote.note_id);
      setMessage("Transcription added to note");
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setAiBusy(false);
    }
  }

  const onFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      await handleUpload(file);
    }
    event.target.value = "";
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>AI Notes Vault</h1>
          <p className="muted">FastAPI + React + MongoDB + Gemini</p>
        </div>
        <div className="status">
          {loading && <span>Loading...</span>}
          {uploading && <span>Uploading...</span>}
          {aiBusy && <span>AI working...</span>}
          {message && <span className="message">{message}</span>}
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <section className="card">
            <h3>New Note</h3>
            <form onSubmit={handleCreate} className="form">
              <label>
                Title
                <input
                  value={newForm.title}
                  onChange={(e) => setNewForm({ ...newForm, title: e.target.value })}
                  required
                />
              </label>
              <label>
                Content
                <textarea
                  rows={4}
                  value={newForm.content}
                  onChange={(e) => setNewForm({ ...newForm, content: e.target.value })}
                />
              </label>
              <label>
                Tags (comma separated)
                <input
                  value={newForm.tags}
                  onChange={(e) => setNewForm({ ...newForm, tags: e.target.value })}
                  placeholder="work, ai, research"
                />
              </label>
              <button type="submit" disabled={loading}>
                Create
              </button>
            </form>
          </section>

          <section className="card">
            <h3>Notes</h3>
            <div className="note-list">
              {notes.map((note) => (
                <button
                  key={note.note_id}
                  className={`note-item ${selectedId === note.note_id ? "active" : ""}`}
                  onClick={() => setSelectedId(note.note_id)}
                >
                  <div className="note-title">{note.title || "Untitled"}</div>
                  <div className="note-meta">
                    <span>{new Date(note.updated_at).toLocaleString()}</span>
                    {note.tags.length > 0 && (
                      <span className="tags">{tagsToString(note.tags)}</span>
                    )}
                  </div>
                  {note.summary && <p className="summary">{note.summary}</p>}
                </button>
              ))}
              {notes.length === 0 && <p className="muted">No notes yet.</p>}
            </div>
          </section>
        </aside>

        <main className="panel">
          {selectedNote ? (
            <>
              <div className="card">
                <div className="panel-header">
                  <h2>Edit Note</h2>
                  <div className="actions">
                    <button onClick={handleSave} disabled={loading}>
                      Save
                    </button>
                    <button className="danger" onClick={handleDelete} disabled={loading}>
                      Delete
                    </button>
                  </div>
                </div>
                <div className="form-grid">
                  <label>
                    Title
                    <input
                      value={editForm.title}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          title: e.target.value,
                        })
                      }
                    />
                  </label>
                  <label>
                    Tags
                    <input
                      value={editForm.tags}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          tags: e.target.value,
                        })
                      }
                    />
                  </label>
                </div>
                <label className="block">
                  Content
                  <textarea
                    rows={8}
                    value={editForm.content}
                    onChange={(e) => setEditForm({ ...editForm, content: e.target.value })}
                  />
                </label>
                <div className="meta-row">
                  <span className="muted">
                    Updated {new Date(selectedNote.updated_at).toLocaleString()}
                  </span>
                </div>
              </div>

              <div className="card">
                <div className="panel-header">
                  <h3>AI Tools</h3>
                </div>
                <div className="ai-actions">
                  <button onClick={handleSummarize} disabled={aiBusy || loading}>
                    Summarize + Keywords
                  </button>
                  <div className="row">
                    <input
                      placeholder="Image URL for OCR (optional)"
                      value={ocrTarget}
                      onChange={(e) => setOcrTarget(e.target.value)}
                    />
                    <button onClick={handleOCR} disabled={aiBusy || loading}>
                      OCR Image
                    </button>
                  </div>
                  <div className="row">
                    <input
                      placeholder="Audio URL for transcription (optional)"
                      value={transcribeTarget}
                      onChange={(e) => setTranscribeTarget(e.target.value)}
                    />
                    <button onClick={handleTranscribe} disabled={aiBusy || loading}>
                      Transcribe Audio
                    </button>
                  </div>
                </div>
                <div className="summary-block">
                  <h4>Summary</h4>
                  <p>{selectedNote.summary || "Run summarize to generate one."}</p>
                  {selectedNote.keywords?.length > 0 && (
                    <p className="muted">Keywords: {selectedNote.keywords.join(", ")}</p>
                  )}
                </div>
              </div>

              <div className="card">
                <div className="panel-header">
                  <h3>Attachments</h3>
                  <label className="upload">
                    <input type="file" onChange={onFileChange} />
                    <span>Upload file</span>
                  </label>
                </div>
                <div className="media-list">
                  {selectedNote.media?.length ? (
                    selectedNote.media.map((m, idx) => (
                      <div key={`${m.url}-${idx}`} className="media-item">
                        <div>
                          <strong>{m.type}</strong>
                          <div className="muted">{m.url}</div>
                        </div>
                        <a href={m.url} target="_blank" rel="noreferrer">
                          Open
                        </a>
                      </div>
                    ))
                  ) : (
                    <p className="muted">No attachments yet.</p>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="card">
              <p>Select or create a note to begin.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
