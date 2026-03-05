export type MediaItem = {
  type: string;
  url: string;
};

export type Note = {
  note_id: string;
  title: string;
  content: string;
  tags: string[];
  owner_id: string;
  media: MediaItem[];
  summary?: string | null;
  keywords: string[];
  created_at: string;
  updated_at: string;
};

export type NoteInput = {
  title: string;
  content: string;
  tags: string[];
  media?: MediaItem[];
  owner_id?: string;
};

export type NoteUpdate = Partial<NoteInput> & {
  summary?: string;
  keywords?: string[];
};

export type PresignResponse = {
  upload_url: string;
  object_url: string;
  expires_in: number;
  key: string;
};
